# REEM

REEM is a centralized middleware package for robotic communication that utilizes Redis, a fast in-memory key-value database. It is designed for ease of use and efficiency.

## Design Philosophy:
REEM expects you will store your data as a nested data structure - think of communication between computers as passing JSON's between machines. REEM is built to model as much data as it can using Redis's [ReJSON](https://pypi.org/project/rejson/) module. This works great for serializable data, but we often want to work with non-serializable types like numpy arrays. Users can define encoder/decoder objects called Ships that define how non-serializable types should be pushed to and retrieved from Redis. REEM provides a default Ship for handling numpy arrays.

## Tutorial

This tutorial will demonstrate how to set up a Redis/ReJSON database on your local computer and connect to it using REEM.

Requirements:
- Python 3
- Linux/macOS (ReJSON requirement, though you can run ReJSON with Docker on Windows)


Open a new terminal and navigate to the directory you would like to work in. **We will refer to this directory as ``.``**

### Redis
First we will install Redis. If at any point, you are stuck in this tutorial, take a look at the [Redis Quickstart](https://redis.io/topics/quickstart) page for help.

Run the following commands in your terminal
```bash
mkdir database-server
cd database-server
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
```
Congratulations! You have installed Redis. Test your installation by running the following in your terminal
```bash
redis-server --daemonize yes
redis-cli
```
You just started a redis server and entered the command line interface (cli) to access the server. Your prompt will look a little different now. To test if the connection is working, type in ``ping`` and you shold see that the redis server you began responds ``PONG``. Then shutdown the server by issuing the ``shutdown`` command and exit the redis-cli with ``ctrl-c``. This whole exchange should look like this:

```bash
MacBook-Pro:redis-stable trishul$ redis-server --daemonize yes
85795:C 28 Mar 2019 14:26:28.140 # oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
85795:C 28 Mar 2019 14:26:28.140 # Redis version=5.0.3, bits=64, commit=00000000, modified=0, pid=85795, just started
85795:C 28 Mar 2019 14:26:28.140 # Configuration loaded
MacBook-Pro:redis-stable trishul$ redis-cli
127.0.0.1:6379> ping
PONG
127.0.0.1:6379> shutdown
not connected>
MacBook-Pro:redis-stable trishul$
```
[//]: ![](https://i.imgur.com/OyL42kS.png)


[//]: #![](https://i.imgur.com/448WsNT.png)

### ReJSON
Now we will install ReJSON. Refer to [ReJSON's Instructions](https://oss.redislabs.com/redisjson/) for additional help if necessary.
```bash
cd ..
git clone https://github.com/RedisLabsModules/redisjson.git
cd rejson
make
cd ..
```
ReJSON is now installed on your computer as an so file inside ``.rejson/src/rejson.so``. We need to tell Redis to use this module. We will do this with a redis configuration file. Download [this example file](https://github.com/tn74/reem/blob/master/examples/redis.conf) configuration file and put it inside the ``database-server`` directory. Then run the following
```bash
redis-server redis.conf --daemonize yes
redis-cli
```
You should see your prompt change again. Enter ``JSON.SET foo . 0`` and verify the output looks as below
```
127.0.0.1:6379> JSON.SET foo . 0
OK
```
You now have a server running Redis and ReJSON!

### Running REEM
Exit the redis-cli by entering ``ctrl-C``. In your terminal, install REEM and all of its dependencies with the following command:
```bash
pip3 install reem rejson redis six numpy
```

Let's try running something!

Copy the following code into a file ``example.py`` into the directory ``.``
```python
from reem.connections import RedisInterface
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

```
In ``.``, run ``python3 example.py``
If it runs without error, congratulations! Installation was successful. Let's look deeper at the code.

#### Initialization
```python
interface = RedisInterface(host="localhost")
interface.initialize()
server = KeyValueStore(interface)
```
The ``interface`` variable defines what a connection to redis is going to look like. You will need to specify the host name of the redis server you wish to connect to.

Every datatype you wish to instantiate later is going to refer to this interface to know what server it is connected to. Here, we instantiate a ``KeyValueStore `` object with the interface as the variable ``server``. A ``KeyValueStore`` object serves as your standard get and set database.


#### Database Syntax
```python
# Set a key and read it and its subkeys
server["foo"] = {"number": 100.0, "string": "REEM"}
print("Reading Root  : {}".format(server["foo"].read()))
print("Reading Subkey: {}".format(server["foo"]["number"].read()))

# Set a new key that didn't exist before to a numpy array
server["foo"]["numpy"] = np.random.rand(3,4)
print("Reading Root  : {}".format(server["foo"].read()))
print("Reading Subkey: {}".format(server["foo"]["numpy"].read()))
```
In the first section of this example code, we set a top level json inside the server to be a python dictionary. Next we read exactly what we wrote. What we get back is a python dictionary identical to the one we submitted. We can also execute a read on a specific subkey of the data we set as we do in third line.

In the second section of the code, we set a numpy array inside the redis server. A numpy array is treated exactly as any other object that we had. Internally, it is handled differently than the strings and numbers we set earlier because a numpy array is not serialiable and thus cannot normally be stored in a JSON. If you are interestined in handling more non-serializable data types, see the ``Ship`` class documentation, coming soon.

Congratulations! You have completed the basic tutorial on REEM. You can explore further topics of interest to you:
- Key Value Store Paradigm
- Publish/Subscribe Paradigm
<!-- #### A Publish/Subscribe Example
Following a successful installation, you should be able to run any of the examples listed in this repository!

Download [ImageProcessing.py](https://github.com/tn74/reem/blob/master/examples/ImageProcessing.py) into your working directory (the one that contains database-server). Execute the following:
```bash
cd ..
python3 ImageProcessing.py
```
If the file executes without error, you have successfully installed and ran a program with REEM!  -->
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
