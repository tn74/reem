# REEM

REEM is a centralized middleware package for robotic communication that utilizes Redis, a fast in-memory key-value database. It is designed for ease of use and efficiency.

## Design Philosophy:
REEM expects you will store your data as a nested data structure - think of communication between computers as passing JSON's between machines. REEM is built to model as much data as it can using Redis's [ReJSON](https://pypi.org/project/rejson/) module. This works great for serializable data, but we often want to work with non-serializable types like numpy arrays. Users can define encoder/decoder objects called Ships that define how non-serializable types should be pushed to and retrieved from Redis. REEM provides a default Ship for handling numpy arrays.

## Installation
``pip install reem``


## Getting Started
Before any machines can communicate using REEM, someone has to run a redis server. Set up a computer to run a redis server. This can be on your local machine. These [instructions](https://redis.io/topics/quickstart) are a great help.

### Starting an Interface
```python
from reem import supports, ships

interface = supports.RedisInterface(host="localhost", shippers=[ships.NumpyShip()])
interface.initialize()
```
The code above encapsulates information about the connection a specific redis database. You must specify:
- ``hostname`` hostname of the computer running the redis server. Could be an IP address
- ``ships`` A list of ships that will handle how non-serializable data will be transferred between your program and redis

**Note: ``interface.initialize()`` must be called before this interface can be used**


### Key-Value Database
```python
from reem.datatypes import KeyValueStore
server = KeyValueStore(interface)
```
The above is all you need to start your data store. The interface defines what database``server`` is connected to. From there you can write to and read from the database as below.

```python
>>> data = {"number": 1000, "string": "REEM" }
>>> server["flat_data"] = data
>>> server["flat_data"].read()
{'number': 1000, 'string': 'REEM'}
>>> server["flat_data"]["number"].read()
1000
```

#### Things You Can Do:

1. Set/Read a whole dictionary or Set/Read a subkey

```python
# Set and read a whole dictionary
>>> server["foo"] = {"key1": data, "key2": data}
>>> server["foo"].read()
{'key1': {'number': 1000, 'string': 'REEM'}, 'key2': {'number': 1000, 'string': 'REEM'}}


# Set and read a terminal key
>>> server["foo"]["key1"]["number"] = 0
>>> server["foo"]["key1"]["number"].read()
0
>>> server["foo"].read()
{'key1': {'number': 1000, 'string': 'REEM'}, 'key2': {'number': 1000, 'string': 'REEM'}}


# Set and read a subdictionary
>>> server["foo"]["key1"] = data
>>> server["foo"]["key1"].read()
{'number': 1000, 'string': 'REEM'}
>>> server["foo"].read()
{'key1': {'number': 1000, 'string': 'REEM'}, 'key2': {'number': 1000, 'string': 'REEM'}}
```

2. Set dictionaries that contain non-serializable types if they are covered by the interface's ships

```python
# Set and read dictionary containing numpy array
>>> server["bar"] = {"image": np.random.rand(3,4)}
>>> server["bar"].read()
{'image': array([[0.71795717, 0.77878419, 0.25546115, 0.7323883 ],
       [0.03937303, 0.28085217, 0.79515465, 0.0912133 ],
       [0.91485541, 0.99704263, 0.65124421, 0.4761731 ]])}

# Read array directly
>>> server["new_key"]["image"].read()
array([[0.71795717, 0.77878419, 0.25546115, 0.7323883 ],
       [0.03937303, 0.28085217, 0.79515465, 0.0912133 ],
       [0.91485541, 0.99704263, 0.65124421, 0.4761731 ]])
```
#### Things You Can't Do:
1. Set a top level key of the server to something other than a dictionary.
```python
 server["new_key"] = image_array              # Not Okay
 server["new_key"] = {"foo":image_array}      # Okay
```
2. Set a subkey of a key that does not exist yet
```python
 server["existing_key"]["non_existant_key"]["non_existant_key"] = 5  # Not Okay
 server["existing_key"]["non_existant_key"] = 5  # Okay
```
#### Changing Schema

REEM by default presumes that the schema underneath a top level key is static. For example, if you write
```python
 server["new_key"] = {"foo":image_array, "bar":1}
```
then REEM expects that the only paths accessed are ``new_key, new_key.foo, new_key.bar``. Additionally it expects that ``new_key.foo`` is a numpy array and ``new_key.bar`` is a number. This is done for performance reasons.

If you want to dynamically change the schema under a specific key, you must call this function with the key names in the list ``keys`` before you alter the schema

```python
 server.track_schema_changes(True, keys=["new_key"])
```

Once you do this, you can overwrite the top level key or any subkey with anything you like, doing something like below.

```python
>>> server["foo"].read()
{'key1': {'number': 1000, 'string': 'REEM'}, 'key2': {'number': 1000, 'string': 'REEM'}}
>>> server["foo"] = data
>>> server["foo"].read()
{'number': 1000, 'string': 'REEM'}
```

**Note that if you fail to call ``track_schema_changes()`` and update the schema, there is no guaranteed behavior. It may or may not work.**
