import socket
import threading
import random
import secrets

from json_reader import JSONReader
from tools import decode, encode, recv_nb_bytes

json_reader = JSONReader()


class Server:

    # dict to handle all the clients
    clients = {}

    def __init__(self):
        self.server_ip = self.get_ip_address()  # server hostname or IP address
        self.port = json_reader.config["port"]  # server port number
        # list of random numbers to send to the clients to know what is the next block
        self.blocks = [self.get_random_number()]

        self.in_game = False
        self.nb_players = 0
        self.scores = []


    def get_ip_address(self) -> str:
        return socket.gethostbyname(socket.gethostname())

    def get_nb_players(self) -> int:
        return len([client for client in self.clients if self.clients[client]["in_game"]])

    def send_message(self, key, response: dict):

        print(f"Sent : {response}")

        data = encode(response)
        # transform the reseponse size in four bytes
        size = len(data).to_bytes(json_reader.config["header_size"], byteorder="big")


        # sending messages with the size of the data in front
        self.clients[key]["socket"].sendall(size + data)

    def generate_key(self) -> str:
        # generates a key
        key = secrets.token_hex(3)
        # checks if the key isn't already used for a client
        while key in self.clients:
            key = secrets.token_hex(3)

        return key

    def close_conn_with(self, client_key: str):
        self.end_game(client_key)
        self.clients[client_key]["online"] = False
        print(f"Closing connection with client : {client_key}")
        self.send_message(client_key, {"type": "RESPONSE", "name": "CLOSED", "args": None})

    def start_game(self, mode):
        if not self.in_game:
            for client in self.clients:

                # checks if the client is online
                if self.clients[client]["online"]:
                    self.send_message(client, {"type": "RESPONSE", "name": "GAME_STARTED", "args": mode})
                    self.clients[client]["in_game"] = True

        self.nb_players = self.get_nb_players()
        self.in_game = True

    # ends the game for one player
    def end_game(self, key: str):
        self.clients[key]["in_game"] = False

        # checks if a client is still playing
        for client in self.clients:
            if self.clients[client]["in_game"]:
                self.in_game = True
                break

            else:
                self.in_game = False

    def game_over(self, originator_key: str, status: str):
        """""
        originator_key : key of the client who sent the GAME_OVER message
        status : if the originator won or lost
        """""

        print(self.scores)

        # telling the clients that the game is over and getting the score of every player
        for client in self.clients:
            if self.clients[client]["in_game"]:
                self.send_message(client, {"type": "GET", "name": "GAME_OVER", "args": None})

        self.nb_players = self.get_nb_players()
        # waiting for the clients to answer
        while len(self.scores) < self.nb_players:
            pass
        self.scores = sorted(self.scores, key=lambda x: list(x.values())[0], reverse=True)

        # we save the originator score and delete it from self.scores
        for score in self.scores:
            if list(score.keys())[0] == originator_key:
                originator_score = score[originator_key]
                self.scores.remove(score)
                break

        # if he lost, he is last one
        if status == "LOST":
            self.scores.append({originator_key: originator_score})

        # if he won he is first one
        elif status == "WON":
            self.scores.insert(0, {originator_key: originator_score})

        # send the results to the client and end the game
        for client in self.clients:
            if self.clients[client]["in_game"]:
                self.send_message(client, {"type": "RESPONSE", "name": "RESULTS", "args": self.scores})
                self.end_game(client)


    def get_key(self, client_socket: socket.socket) -> str | None:
        # receives the key that the client sent
        client_key = decode(client_socket.recv(1024))

        try:
            # if the game is already launched, we don't accept any connections
            if not self.in_game:

                if client_key in self.clients:
                    # checks if the client is already connected
                    if self.clients[client_key]["online"]:
                        raise Exception("Client already connected")

                    else:
                        self.clients[client_key]["online"] = True

                else:
                    # creates a new key
                    client_key = self.generate_key()
                    self.clients[client_key] = {"online": True, "socket": client_socket, "in_game": False, "block": 0}

            else:
                raise Exception("Game has already started")

        # handles exceptions
        except Exception as e:
            client_socket.send(encode(e.args[0]))
            return None

        else:
            client_socket.send(encode(client_key))
            print(f"Accepted connection from client with key {client_key}")
            return client_key


    def handle_client(self, client_socket, addr):
        key = self.get_key(client_socket)

        # if the key is valid
        if key is not None:
            try:
                while True:
                    # getting the size of the request which is stored in 4 bytes in front of the request itself
                    request_size = recv_nb_bytes(self.clients[key]["socket"], json_reader.config["header_size"])
                    # transforming bytes to int
                    request_size = int.from_bytes(request_size, byteorder="big")

                    # receive the message, knowing the size allow us to make sure the request doesn't mix with other
                    request = decode(recv_nb_bytes(self.clients[key]["socket"], request_size))
                    print(f"Received from {key}: {request}")

                    # when the user sends a request to change a state
                    if request["type"] == "EVENT":

                        if request["name"] == "CLOSE":
                            self.close_conn_with(key)
                            break

                        elif request["name"] == "START":
                            self.start_game(request["args"])

                        elif request["name"] == "GAME_OVER":
                            self.game_over(key, request["args"])

                    # if the user wants to transfer data to the other players
                    elif request["type"] == "TRANSFER":

                        # every time the profiles are changed, we send them to players
                        if request["name"] == "ADD_PROFILE":
                            profile_name = request["args"]
                            # if the profile name isn't already used
                            if not profile_name in json_reader.profiles:
                                self.create_new_profile(profile_name)
                                self.send_data(key, "PROFILES", json_reader.profiles, request["receivers"])
                                # saves the profiles
                                json_reader.save_profiles()

                        elif request["name"] == "DELETE_PROFILE":
                            profile_key = request["args"]
                            if profile_key in json_reader.profiles:
                                # we delete the profiles
                                del json_reader.profiles[profile_key]
                                self.send_data(key, "PROFILES", json_reader.profiles, request["receivers"])
                                # saves the profiles
                                print(json_reader.profiles)
                                json_reader.save_profiles()

                        elif request["name"] == "CHANGE_PROFILE":
                            json_reader.profiles[request["args"]["key"]] = request["args"]["profile"]
                            self.send_data(key, "PROFILES", json_reader.profiles, request["receivers"])
                            # saves the profiles
                            json_reader.save_profiles()

                        # for other requests
                        else:
                            self.send_data(key, request["name"], request["args"], request["receivers"])

                    # when the user sends a request and waits for a value
                    elif request["type"] == "GET":

                        if request["name"] == "NEXT_BLOCK":
                            self.next_block(key)

                        elif request["name"] == "NB_PLAYERS":
                            self.nb_players = self.get_nb_players()
                            self.send_message(key, {"type": "RESPONSE", "name": "NB_PLAYERS", "args": self.nb_players})

                        # used at the beginning so that the client can get the profiles, event if they weren't changed
                        elif request["name"] == "PROFILES":
                            self.send_message(key, {"type": "RESPONSE", "name": "PROFILES", "args": json_reader.profiles})

                    elif request["type"] == "POST":

                        if request["name"] == "SCORE":
                            self.scores.append({key: request['args']})


            except Exception as e:
                print(e)

            finally:
                self.clients[key]["online"] = False
                client_socket.close()
                print(f"Connection to client ({addr[0]}:{addr[1]}) closed")


    def run(self):
        # create a socket object
        try:

            # gets the profiles
            # if no profile was created, we create a built-in profile
            if json_reader.profiles == {}:
                self.create_new_profile("John Doe")

            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # bind the socket to the host and port
            server.bind((self.server_ip, self.port))
            # listen for incoming connections
            server.listen()
            print(f"Listening on {self.server_ip}:{self.port}")

            while True:
                # accept a client connection
                client_socket, addr = server.accept()
                print(f"Incoming connection from {addr[0]}:{addr[1]}")

                # start a new thread to handle the client
                thread = threading.Thread(target=self.handle_client, args=(client_socket, addr,))
                thread.start()

        except Exception as e:
            print(f"Error: {e}")
        finally:
            server.close()

    ################################
    # Handles all the game mechanics
    ################################

    def get_random_number(self):
        return random.randint(json_reader.config["first_fixed_block"], json_reader.config["last_fixed_block"])

    def next_block(self, key):
        self.clients[key]["block"] += 1
        # creates a new number
        if len(self.blocks) == self.clients[key]["block"]:
            self.blocks.append(self.get_random_number())

        # sends the new number to the client
        block = self.blocks[self.clients[key]["block"]]
        self.send_message(key, {"type": "RESPONSE", "name": "NEXT_BLOCK", "args": block})

    def send_data(self, key, data_name, data, receivers):

        if receivers == "opponents":
            receivers = [client for client in self.clients if client != key and self.clients[client]["online"]]

        elif receivers == "all":
            receivers = [client for client in self.clients if self.clients[client]["online"]]

        for receiver in receivers:
            self.send_message(receiver, {"type": "RESPONSE", "name": data_name.upper(), "args": data})

    def create_new_profile(self, name):
        json_reader.profiles[self.generate_key()] = self.get_base_profile(name)

    def get_base_profile(self, name: str) -> dict:
        return {"name": name,
                "best_score": 0,
                "key_binds": {
                    "right": 100,
                    "left": 113,
                    "speed up": 115,
                    "turn right": 1073741903,
                    "turn left": 1073741904
                    }

                }


server = Server()
server.run()