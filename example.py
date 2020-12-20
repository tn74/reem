from __future__ import print_function

from reem.connection import RedisInterface
from reem.datatypes import KeyValueStore
import numpy as np

server = KeyValueStore("localhost")

try:
    server['foo']['bar'] = 12345
    print("ERROR: set subkey without top level key existing")
except Exception:
    pass

# Set a key and read it and its subkeys
server["foo"] = {"number": 100.0, "string": "REEM"}
print("Reading Root  : {}".format(server["foo"].read()))
print("Reading Subkey: {}".format(server["foo"]["number"].read()))

# Set a new key that didn't exist before to a numpy array
server["foo"]["numpy"] = np.random.rand(3,4)
print("Reading Root  : {}".format(server["foo"].read()))
#print("Reading Subkey: {}".format(server["foo"]["numpy"].read()))
