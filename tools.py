import json

def encode(msg) -> bytes:
    return json.dumps(msg).encode("utf-8")

def decode(msg: bytes):
    return json.loads(msg.decode("utf-8"))

# when sending a message on a socket, it creates a flow, this function reads this flow but only nb_bytes bytes
def recv_nb_bytes(socket, nb_bytes: int):
    data = b""  # empty buffer

    while len(data) < nb_bytes:
        chunk = socket.recv(nb_bytes - len(data))
        data += chunk

    return data


