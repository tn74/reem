Set Up Tutorial
================================

In REEM, data is passed between client programs and a centralized Redis server.
This tutorial will demonstrate how to set
up the server and connect to it with a REEM client. Both the server
and client will run on the local machine.


Requirements:

 - Python 3.5+
 - Linux, macOS, or Windows


Installing Redis and ReJSON (Linux or MacOS)
############################################

This section goes through how to set up a server. REEM runs on Redis and requires the ReJSON module. We will install both and check that they are working.


Redis install
**************

In Ubuntu 18.04+, simply install Redis via  ``sudo apt-get install redis-server``.

If you are running Ubuntu 16.04, DO NOT install Redis through ``apt-get install redis-server``
This will install Redis 3 which does not support modules, and you will not be able to run REEM.
Instead, follow the instructions below to install Redis from source.

The following script will download and build Redis with supporting packages from source inside
a folder we will call ``rejson-server``.
REEM has been tested with Redis version 5.0.4. You may want to pull the latest version of Redis in the future. Change the
versioning in the script appropriately.

Once you download and build Redis from source, you will need to access two executables:
``redis-server`` and ``redis-cli``. The former is the executable that launches a redis-server. The latter is a
useful command line interface (cli) that allows for easy testing. The executables are located at

``rejson-server/redis-5.0.4/src/redis-server``

``rejson-server/redis-5.0.4/src/redis-cli``

The script below gives them aliases to make things easier. Note that these aliases will disappear
when the terminal closes.

.. code-block:: bash

    mkdir rejson-server
    cd rejson-server
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
Now, check that the redis server will boot. Run ``redis-server`` in your terminal. The redis server will take over your terminal and run until it is killed.

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

Installing ReJSON
*****************
`ReJSON <https://oss.redislabs.com/redisjson/>`_ is a third party module that introduces a JSON datatype to Redis. REEM relies on it extensively

Starting from inside the ``rejson-server`` folder, continuing from the Redis installation script

The following will
build ReJSON from source.

.. code-block:: bash

    git clone https://github.com/RedisLabsModules/redisjson.git
    cd redisjson
    make
    cd ..
    wget https://raw.githubusercontent.com/tn74/reem/master/examples/redis.conf

The above script produces an compiled library file at ``redisjson/src/rejson.so``. Redis needs to be
told to use that library file, and so the last line downloads a configuration file that enables ReJSON when Redis uses it.  

Specifically, line 46 (in the modules section) says ``loadmodule redisjson/src/rejson.so`` to specify
the compiled library for rejson.
If you've installed via ``apt-get``, you should edit the ``redis.conf`` file to change
line 46 to point to the absolute path to the compiled library file.  Then, copy it to
the version that the Redis service will use via 

.. code-block:: bash
    
    sudo cp redis.conf /etc/redis/redis.conf
    sudo nano /etc/redis/redis.conf

Then, you will want to change the value of the ``supervised`` directive to ``systemd``.  Finally, restart the service via

.. code-block:: bash

    sudo systemctl restart redis.service

If you installed via another method, e.g. source you will need to manually open up a terminal and run
``redis-server redis.conf``. This will start the Redis server with ReJSON.

Let's test the ReJSON installation.  Open another terminal and run ``redis-cli``. Be sure you can execute the following in that redis-cli prompt

.. code-block:: bash

    127.0.0.1:6379> JSON.SET foo . 0
    OK

You can then press Ctrl+C or enter "exit" to exit.


Installing Redis and ReJSON (Windows)
############################################

For Windows, you will use the `Windows builds of Redis <https://github.com/tporadowski/redis>`_ and `ReJSON <https://github.com/tporadowski/rejson>`_

To install Redis, grab one of the 5.x installs from `this page <https://github.com/tporadowski/redis/releases>`_ and install it on your machine.  We have tested this to work on version 5.0.14. The files will typically be in "C:\\Program Files\\Redis", which you may want to add to your PATH for convenience.
If you have installed using the MSI installer, this will install a "Redis Windows Service" for you that will run on startup.  If you used the Zip file, you will need to start the server manually. 

Next, download a release from the `ReJSON releases <https://github.com/tporadowski/rejson/releases>`_. We have tested this to work on version 1.0.6.  Create a folder named rejson-server, and unzip the release into this folder. You should now have a DLL and PDB file here.

Then, download an example redis.conf file, such as `the default here <https://github.com/tporadowski/redis/blob/develop/redis.conf>`_, and put it into rejson-server. Then, in the section labeled "MODULES", add the line "loadmodule ReJSON.dll".  Save and close the file.

Finally you will need to obtain a running Redis server configured with ReJSON. 
If you want to use Redis Windows Service, replace C:\\Program Files\\Redis\\redis-windows-service.conf
with the redis.conf that you just edited, and also copy the ReJSON.dll and pdb files to C:\\Program Files\\Redis.
To make sure the changes have an effect,
restart the service by going into Services (e.g., press the Windows key and search for "services"), find Redis, and then stop and restart it.

If you need to start the Redis server manually, open a Command Prompt and
navigate to the rejson-server folder. Enter

.. code-block:: bash

    > "C:\Program Files\Redis\redis-server.exe" redis.conf

which will start the server.  It should say "Ready to accept connections". 

To test that everything is working, open another command prompt and enter:

.. code-block:: bash

    > "C:\Program Files\Redis\redis-cli.exe"

And then at the prompt type:

.. code-block:: bash

    127.0.0.1:6379> JSON.SET foo . 0
    OK

If you get something other than OK, you have misconfigured the server.

That's it! Close out of the second command prompt window and continue on with the rest of the tutorial.


Common Redis Configuration Options
##################################

``redis.json`` configures a lot of functionality about the Redis server. As an example,
line 71 (in the network section) says ``bind 127.0.0.1`` to bind only to the local host network interface.
If you later want to make this redis server accessible on a network,
you must change line 71 to bind to that interface too.
For example if the computer hosting the redis server has an IP address ``10.0.0.1``
on the network, this line should become ``bind 127.0.0.1 10.0.0.1``
so that it binds to the local interface and the network interface.

There are plenty of other resources on Redis on the web, so we will not go into more detail here.


Setting up REEM
###############

The REEM client provides a convenient Python frontend to Redis / ReJSON. First, install REEM and its dependencies with the below command

.. code-block:: bash

    python -m pip install reem

Then, make sure a redis server is available for a client to connect to.
If a server is not already running, run ``redis-server redis.conf`` in a terminal and leave that terminal be.

In another window, verify that the server is running and properly configured using:

.. code-block:: bash

    > redis-cli

Then, check that you can execute the following:

.. code-block:: bash

    127.0.0.1:6379> JSON.SET foo . 0
    OK
    127.0.0.1:6379> exit

Now, let's test REEM. Copy the below into a file and run it:

.. code-block:: python

    from reem import KeyValueStore
    import numpy as np
    import time

    server = KeyValueStore("localhost")

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
reads and prints that data. Next, it sends a numpy array to Redis and reads that back as well. 

Congratulations! You have got REEM working on your machine! Continue to the next section to see what else REEM can do.

