from reem.connection import RedisInterface
from reem.datatypes import KeyValueStore
import numpy as np

interface = RedisInterface(host="localhost")
interface.initialize()
server = KeyValueStore(interface)

# Set a key and read it and its subkeys
server["foo"] = {"number": 100.0, "string": "REEM"}
print("Reading Root  : {}".format(server["foo"].read()))
print("Reading Subkey: {}".format(server["foo"]["number"].read()))

# Set a new key that didn't exist before to a numpy array
server["foo"]["numpy"] = np.random.rand(3,4)
print("Reading Root  : {}".format(server["foo"].read()))
print("Reading Subkey: {}".format(server["foo"]["numpy"].read()))
