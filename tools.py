import json
import numpy as np

def encode(msg) -> bytes:
    return json.dumps(msg).encode("utf-8")

def decode(msg: bytes):
    return json.loads(msg.decode("utf-8"))


"""""
import json
import numpy as np

def encode(msg) -> bytes:
    if isinstance(msg, str):
        return msg.encode("utf-8")
    else:
        if isinstance(msg, np.ndarray):
            # if message is array, we turn it into a list
            msg = msg.tolist()
        return json.dumps(msg).encode("utf-8")

def decode(msg: bytes):
    msg = msg.decode("utf-8")
    if isinstance(msg, str):
        return msg
    else:
        msg = json.loads(msg)
        if isinstance(msg, list):
            # if msg is a list, we turn it into an array
            msg = np.array(msg)

        return msg
"""""

