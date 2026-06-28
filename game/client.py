import socket
import threading
from tools import decode, encode, recv_nb_bytes

# handles the connection with the server
class Client:

    def __init__(self, json_reader, key=" "):
        self.json_reader = json_reader

        # create a socket object
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = self.json_reader.config["server_ip"]  # replace with the server's IP address
        self.server_port = self.json_reader.config["port"]  # replace with the server's port number
        self.key = key

        # dict to store the server's responses depending on the name of the response
        self.responses = {}

    def connect(self) -> str | None:
        """""
        return the client's key
        """""

        try:
            # establish connection with server
            self.socket.connect((self.server_ip, self.server_port))
            # client sends its key to check if it's valid
            self.socket.send(encode(self.key))

            response = decode(self.socket.recv(1024))
            if response == 'Client already connected':
                raise Exception("Client already connected")

            elif response == 'Game has already started':
                raise Exception("Game has already started")

            else:
                self.key = response
                print(f"Your key to connect to the server is {self.key}")

                # when the user is connected, we start a thread that will listen for incoming responses and store
                # them is self.responses
                start_thread = threading.Thread(target=self.get_response)
                start_thread.start()

                return self.key

        # when the server isn't online
        except OSError:
            print("Connection failed, the server is shutdown")

        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_response(self):
        while True:

            # getting the size of the request which is stored in 4 bytes in front of the request itself
            response_size = recv_nb_bytes(self.socket, self.json_reader.config["header_size"])
            # transforming bytes to int
            response_size = int.from_bytes(response_size, byteorder="big")

            # receive the message, knowing the size allow us to make sure the request doesn't mix with other
            response = decode(recv_nb_bytes(self.socket, response_size))

            # store the response's arguments in self.responses
            self.responses[response["name"]] = Response(response["args"])

            print(f"Received from server : request {response["type"]} with name {response["name"]} with args {response["args"]} ")

            if response["name"] == "CLOSED":
                self.close_conn()
                break


    def send_request(self, request: dict):

        print(f"Sent request {request["type"]} with name {request['name']} with args {request['args']}")


        data = encode(request)
        # transform the size in four bytes
        size = len(data).to_bytes(self.json_reader.config["header_size"], byteorder="big")

        # sending messages with the size of the data in front
        self.socket.sendall(size + data)

    def get_color(self):
        # sends a request for the next block
        self.send_request({"type": "GET", "name": "NEXT_BLOCK", "args": None})
        # waits for the server to answer
        while not "NEXT_BLOCK" in self.responses or self.responses["NEXT_BLOCK"].read:
            pass
        return self.responses["NEXT_BLOCK"].response

    def get_nb_players(self):
        # sends a request for the next block
        self.send_request({"type": "GET", "name": "NB_PLAYERS", "args": None})
        # waits for the server to answer
        while not "NB_PLAYERS" in self.responses or self.responses["NB_PLAYERS"].read :
            pass
        return self.responses["NB_PLAYERS"].response

    def get_profiles(self):
        # sends a request for the next block
        self.send_request({"type": "GET", "name": "PROFILES", "args": None})
        # waits for the server to answer
        while not "PROFILES" in self.responses or self.responses["PROFILES"].read:
            pass
        return self.responses["PROFILES"].response

    def close_conn(self):
        # close client socket (connection to the server)
        self.socket.close()
        print("Connection to server closed")


class Response:

    def __init__(self, response):
        self.__response = response
        self.read = False

    @property
    def response(self):
        self.read = True
        return self.__response