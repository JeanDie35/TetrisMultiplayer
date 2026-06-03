import socket
import threading
import random
import secrets
from config import Config
from tools import decode, encode

config = Config()


class Server:

    clients = {}

    def __init__(self):
        self.server_ip = self.get_ip_address()  # server hostname or IP address
        self.port = config.data["port"]  # server port number
        self.blocks = [self.get_random_number()]

        self.in_game = False
        self.nb_online_players = 0


    def get_ip_address(self) -> str:
        return socket.gethostbyname(socket.gethostname())

    def generate_key(self) -> str:
        key = secrets.token_hex(3)
        # checks if the key isn't already used for a client
        while key in self.clients:
            key = secrets.token_hex(3)

        return key

    def close_conn_with(self, client_key: str):
        print(f"Closing connection with client : {client_key}")
        self.clients[client_key]["socket"].send(encode({"name": "CLOSED", "args": None}))

    def start_game(self):
        for client in self.clients:
            # checks if the client is online and not already playing
            if self.clients[client]["online"]:
                self.clients[client]["socket"].send(encode({"name": "GAME_STARTED", "args": None}))
                self.clients[client]["in_game"] = True
        self.nb_online_players = len([client for client in self.clients if self.clients[client]["online"]])
        self.in_game = True

    def end_game(self, client_key: str):
        self.clients[client_key]["in_game"] = False

        for client in self.clients:
            if self.clients[client]["in_game"]:
                self.in_game = True
                break

            else:
                self.in_game = False

    def recv_nb_bytes(self, key: str, nb_bytes: int):
        data = b""  # empty buffer

        while len(data) < nb_bytes:
            chunk = self.clients[key]["socket"].recv(nb_bytes - len(data))
            data += chunk

        return data

    def get_key(self, client_socket: socket.socket) -> str | None:
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
                    client_key = self.generate_key()
                    self.clients[client_key] = {"online": True, "socket": client_socket, "in_game": False, "block": 0, "score" : 0, "grid": None}

            else:
                raise Exception("Game is already started")

        except Exception as e:
            client_socket.send(encode(e.args[0]))
            return None

        else:
            client_socket.send(encode(client_key))
            print(f"Accepted connection from client with key {client_key}")
            return client_key


    def handle_client(self, client_socket, addr):
        key = self.get_key(client_socket)

        if key is not None:
            try:
                while True:

                    # getting the size of the request which is stored in 4 bytes in front of the request itself
                    request_size = self.recv_nb_bytes(key, config.data["nb_bytes_size"])
                    # transforming bytes to int
                    request_size = int.from_bytes(request_size, byteorder="big")

                    # receive the message, knowing the size allow us to make sure the request doesn't mix with other
                    request = decode(self.recv_nb_bytes(key, request_size))

                    # when the user sends a request to change a state
                    if request["type"] == "EVENT":

                        if request["name"] == "CLOSE":
                            self.close_conn_with(key)
                            break

                        elif request["name"] == "START":
                            self.start_game()

                        elif request["name"] == "OVER":
                            self.end_game(key)

                    # if the user wants to update existing data in the server
                    elif request["type"] == "PUT" != -1:

                        if request["name"] == "GRID":
                            self.clients[key]["grid"] = request["args"]

                        elif request["name"] == "SCORE":
                            self.clients[key]["score"] = request["args"]

                    # when the user sends a request and waits for a value
                    elif request["type"] == "GET":

                        if request["name"] == "NEXT_BLOCK":
                            self.next_block(key)

                        elif request["name"] == "GRID":
                            self.send_grid(key)

                        elif request["name"] == "SCORE":
                            self.send_score(key)


            finally:
                self.clients[key]["online"] = False
                client_socket.close()
                print(f"Connection to client ({addr[0]}:{addr[1]}) closed")


    def run(self):
        # create a socket object
        try:
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
        return random.randint(config.data["first_fixed_block"], config.data["last_fixed_block"])

    def next_block(self, key):
        self.clients[key]["block"] += 1
        # creates a new number
        if len(self.blocks) == self.clients[key]["block"]:
            self.blocks.append(self.get_random_number())

        # sends the new number to the client
        block = self.blocks[self.clients[key]["block"]]
        self.clients[key]["socket"].send(encode({"name": "NEXT_BLOCK", "args": block}))

    def send_grid(self, key):
        if self.nb_online_players == 2:
            opponent = None
            for client in self.clients:
                if client != key:
                    opponent = client

            # send the opponent's grid
            self.clients[key]["socket"].send(encode({"name": "GRID", "args": self.clients[opponent]["grid"]}))

        else:
            self.clients[key]["socket"].send(encode({"name": "GRID", "args": None}))
    def send_score(self, key):
        if self.nb_online_players == 2:
            opponent = None
            for client in self.clients:
                if client != key:
                    opponent = client

            self.clients[key]["socket"].send(encode({"name": "SCORE", "args": self.clients[opponent]["score"]}))

        else:
            self.clients[key]["socket"].send(encode({"name": "SCORE", "args": None}))


server = Server()
server.run()