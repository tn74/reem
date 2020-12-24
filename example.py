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
print("Printing Root  :",server["foo"])
print("Reading Root  :",server["foo"].read())
print("Reading Subkey:",server["foo"]["number"].read())

# Set a new key that didn't exist before to a numpy array
#server["foo"]["numpy"] = np.random.rand(3,4)
var = server["foo"]["numpy"]
var.write(np.random.rand(3,4))
print("Reading Root  :",server["foo"].read())
#print("Reading Subkey: {}".format(server["foo"]["numpy"].read()))

del server["foo"]["numpy"]
print("After delete ['foo']['numpy']:",server["foo"].read())

del server["foo"]["string"]
print("After delete ['foo']['string']:",server["foo"].read())

del server["foo"]
try:
    val = server["foo"].read()
    print("['foo'] was not deleted successfully! ",val)
except Exception:
    print("['foo'] was deleted successfully:")

server['foo'] = {'bar':[0,1,2,3,4,5]}
print("Resetting to",server['foo'].read())
print("Reading array index:",server["foo"]['bar'][2].read())
server['foo']['bar'].append(6)
print("After appending 6:",server['foo'].read())
server['foo']['bar'] += [7,8,9]
print("After adding [7,8,9]:",server['foo'].read())

del server["foo"]['bar'][2]
print("After delete ['foo']['bar'][2]:",server["foo"].read())

server['foo'] = [0,1,2,3,4,5]
print("Resetting to:",server['foo'].read())
print("Reading array index:",server["foo"][2].read())
server['foo'].append(6)
print("After appending 6:",server['foo'].read())
print("Length of ['foo']:",len(server['foo']))
for i in range(len(server['foo'])):
    server['foo'][i] *= 2
print("After multiplying everything by 2:",server['foo'].read())

del server["foo"][2]
print("After delete ['foo'][2]:",server["foo"].read())