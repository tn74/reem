Set Up Tutorial
================================

In REEM, data is passed between client programs and a centralized Redis server.
This tutorial will demonstrate how to set
up the server and connect to it with a REEM client. Both the server
and client will run on the local machine.


Requirements:

 - Python 3
 - Linux/macOS (ReJSON requirement, though you can run ReJSON with Docker on Windows)


Server
#############

This section goes through how to set up a server. REEM runs on Redis and requires the ReJSON module. We
will install both and check that they are working.

Redis
******

The following script will download and build Redis with supporting packages from source inside
a folder called ``database-server``.
REEM has been tested with Redis version 5.0.4. You may want to pull the latest version of Redis in the future. Change the
versioning in the script appropriately

DO NOT install Redis through ``apt-get install redis-server``
This will install Redis 3 which does not support modules. You will not be able to run REEM.

Once you download and build Redis from source, you will need to access two executables:
``redis-server`` and ``redis-cli``. The former is the executable that launches a redis-server. The latter is a
useful command line interface (cli) that allows for easy testing. The executables are located at

``database-server/redis-5.0.4/src/redis-server``

``database-server/redis-5.0.4/src/redis-cli``

The script below gives them aliases to make things easier. Note that these aliases will disappear
when the terminal closes.

.. code-block:: bash

    mkdir database-server
    cd database-server
    wget http://download.redis.io/releases/redis-5.0.4.tar.gz
    tar xzf redis-5.0.4.tar.gz
    cd redis-5.0.4/deps
    make hiredis lua jemalloc linenoise
    cd ..
    make
    alias redis-server=$PWD/src/redis-server
    alias redis-cli=$PWD/src/redis-cli
    cd ..

Check that the version of Redis you have is 5.0.x by running ``redis-server --version``
Now, check that the redis server will boot. Run ``redis-server`` in your terminal. The redis server will take over
your terminal.

Open up another terminal and run ``redis-cli``. The CLI will take over that terminal and your prompt should look like
``127.0.0.1:6379>``
Execute a basic set and get with Redis, ensuring the output looks similar to the output below:

.. code-block:: bash

    127.0.0.1:6379> SET key 1
    OK
    127.0.0.1:6379> GET key
    "1"
    127.0.0.1:6379>

Congratulations! You have successfully installed and ran Redis. Shutdown the Redis server (issue the ``shutdown`` command
in the cli) and exit the cli.

ReJSON
*******
`ReJSON <https://oss.redislabs.com/redisjson/>`_ is a third party module developed for Redis developed by Redis Labs.
It introduces a JSON datatype to Redis that is not available in standard Redis. REEM relies on it for serializable data.

Starting from inside the ``database-server`` folder, continuing from the Redis installation script, the following will
build ReJSON from source.

.. code-block:: bash

    git clone https://github.com/RedisLabsModules/redisjson.git
    cd redisjson
    make
    cd ..
    wget https://raw.githubusercontent.com/tn74/reem/master/examples/redis.conf

The above script produces an compiled library file at ``database-server/redisjson/src/rejson.so``. Redis needs to be
told to use that library file, and so the last line downloads a configuration file that enables ReJSON when Redis uses it.  

Some details about this configuration file:

- Line 46 (in the modules section) says ``loadmodule redisjson/src/rejson.so`` specifying the compiled library for rejson
- Line 71 (in the network section) says ``bind 127.0.0.1`` to bind only to the local host network interface.

If you later want to make this redis server accessible on a network,
you must change line 71 to bind to that interface too.
For example if the computer hosting the redis server has an ip address ``10.0.0.1``
on the network, this line should become ``bind 127.0.0.1 10.0.0.1``
so that it binds to the local interface and the network interface.

Let's test the ReJSON installation. Run ``redis-server redis.conf``. This will start the Redis server with ReJSON.
Open another terminal and run ``redis-cli``. Be sure you can execute the following in that redis-cli prompt

.. code-block:: bash

    127.0.0.1:6379> JSON.SET foo . 0
    OK


Client
#############
Before you begin this part of the turtorial, make sure a redis server is available for a client to connect to.
If a server is not already running, run ``redis-server redis.conf`` in a terminal and leave that terminal be.

Client machines connect to the server purely through Python with the REEM client.
Install REEM and it's dependencies with the below command

.. code-block:: bash

    pip3 install reem

Copy the below into a file and run it:

.. code-block:: python

    from reem.connection import RedisInterface
    from reem.datatypes import KeyValueStore
    import numpy as np
    import time

    interface = RedisInterface(host="localhost")
    interface.initialize()
    server = KeyValueStore(interface)

    # Set a key and read it and its subkeys
    server["foo"] = {"number": 100.0, "string": "REEM"}
    print("Reading Root  : {}".format(server["foo"].read()))
    print("Reading Subkey: {}".format(server["foo"]["number"].read()))

    # Set a new key that didn't exist before to a numpy array
    server["foo"]["numpy"] = np.random.rand(3,4)
    time.sleep(0.0001)  # Needed on ubuntu machine for numpy set to register?
    print("Reading Root  : {}".format(server["foo"].read()))
    print("Reading Subkey: {}".format(server["foo"]["numpy"].read()))


The output should appear something like the below

.. code-block:: console

    Reading Root  : {'number': 100, 'string': 'REEM'}
    Reading Subkey: 100
    Reading Root  : {'number': 100, 'string': 'REEM', 'numpy': array([[0.41949741, 0.40785201, 0.70637666, 0.1809309 ],
           [0.37884759, 0.70176005, 0.14115555, 0.82246663],
           [0.24243882, 0.86587402, 0.19852017, 0.21833667]])}
    Reading Subkey: [[0.41949741 0.40785201 0.70637666 0.1809309 ]
     [0.37884759 0.70176005 0.14115555 0.82246663]
     [0.24243882 0.86587402 0.19852017 0.21833667]]

The code connects to a Redis server and ``set`` s a dictionary with basic number and string data. It then
reads and prints that data. Next, it sends a numpy array to Redis and reads that back as well. It uses a KeyValueStore
object to do all this. Learn more about it in the next section.

Congratulations! You have got REEM working on your machine! Continue to the next section to see what it can do.