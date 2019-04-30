Basic Usage
================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

This page explains how to use database and publish/subscribe paradigms with REEM.

Initialization
###############

Before any information can be passed to a Redis server, we need to specify how to contact the server.
A ``RedisInterface`` object is meant to represent a connection to a specific server. Instantiate it and call initialize
before attaching any datatypes to it. You must specify the host as the IP address of the server running Redis
(or localhost). If no host is provided, **the default argument for host is localhost**

.. code-block:: python

   from reem.connection import RedisInterface
   interface = RedisInterface(host="localhost")
   interface.initialize()

Key Value Store
#################

The ``KeyValueStore`` object is meant to be your way of interacting with Redis as a nested database server.
You should treat a ``KeyValueStore`` object as though it were a python dictionary that can
contain native python types and numpy arrays. When you set something inside this "dictionary", the corresponding
entry will be set in Redis. Reading the "dictionary" will read the corresponding entry in Redis.

The ``KeyValueStore`` is instantiated with a ``RedisInterface`` object, identifying what Redis server it is connected
to.

.. code-block:: python

   from reem.datatypes import KeyValueStore
   server = KeyValueStore(interface)

The below code illustrates:

- To set an item in Redis, the syntax is identical to that setting a path in a Python dictionary
- To get an item from Redis, the syntax is the same as a dictionary's but you must call ``.read()`` on the final path.

.. code-block:: python

   data = {'number': 1000, 'string': 'REEM'}
   server["foo"] = flat_data

   bar = server["foo"].read()
   # Sets bar = {'number': 1000, 'string': 'REEM'}

   bar = server["foo"]["number"].read()
   # Sets bar = 1000


**Limitations**

1. Cannot use non-string Keys

.. code-block:: python

   server["foo"] = {0:"zero", 1:"one"} # Not Okay
   server["foo"] = {"0":"zero", "1":"one"} # Okay

REEM assumes all keys are strings to avoid having to parse JSON keys to determine if they are strings or numbers.

2. Cannot have a list with nonserializable types.

.. code-block:: python

   server["foo"] = {"bar":[np.arange(3), np.arange(4)]} # Not Okay
   server["foo"] = {"bar":[3, 4]} # Okay

REEM does not presently check lists for non serializable types. We hope to allow this in a future release.
For now, we ask you substitute the list with a dictionary

.. code-block:: python

   server["foo"] = {"bar":[np.arange(3), np.arange(4)]} # Not Okay
   server["foo"] = {"bar":{"arr1": np.arange(3), "arr2": np.arange(4)}} # Okay



Publish/Subscribe
#################

Publishing and subscribing is implemented with a single type of publisher and two types of subscribers. Publishers

Publisher
----------

Publishers are instantiated with an ``RedisInterface``.
You may treat a publisher like an python dictionary that you CANNOT read.

.. code-block:: python

   from reem.datatypes import PublishSpace
   publisher = PublishSpace(interface)


When you set something inside this "dictionary"  the publisher broadcasts a message indicating what path was updated.
All subscribers listening to that path are notified and will act accordingly.

.. code-block:: python

   data = {"image": np.random.rand(640, 480, 3), "id": 0}

   # publishes raw_image
   publisher["raw_image"] = data

   # publishes raw_image.id
   publisher["raw_image"]["id"] = 1


All limitations that apply to ``KeyValueStore`` apply to ``PublishSpace`` as well.
``PublishSpace`` is a subclass of ``KeyValueStore`` with alterations.

Subscribers
------------

Subscribes listen to a key on the Redis Server and will act based on changes to that key OR its subkeys.
For example a subscriber to the key "raw_image" will be notified if "camera_data" is freshly uploaded
by a publisher or if the path "raw_image.id" is updated.

A subscriber's ``.listen()`` method must be called for it to start listening to Redis updates.

Subscribing has two implementations

Silent Subscribers
^^^^^^^^^^^^^^^^^^^^

A silent subscriber acts like a local variable that mimics the data in Redis
underneath the key indicated by its channel. It will silently update as fast as it can without notifying the
user that an updated occurred. Use it if you would like a variable that just keeps the latest copy of Redis information
at all times.

The ``SilentSubscriber`` is initialized with a channel name and an interface. The channel represents the path inside
the RedisServer this subscriber should listen to. Initialization is as below

.. code-block:: python

   from reem.datatypes import SilentSubscriber
   subscriber = SilentSubscriber(channel="silent_channel", interface=interface)
   subscriber.listen()


The below code illustrates how to read data from a subscriber.

.. code-block:: python

   publisher["silent_channel"] = {"number": 5, "string":"REEM"}
   time.sleep(0.01)

   foo = subscriber["number"].read()
   # foo = 5
   foo = subscriber.value()
   # foo = {"number": 5, "string":"REEM"}

   publisher["silent_channel"] = 5
   time.sleep(0.01)

   foo = subscriber.value()
   # foo = 5

**Note:** The ``.read()`` method does not go to
Redis but copies the dictionary at that path in the local variable. This is faster than the ``.read()`` method used by
the ``KeyValueStore``



Callback Subscribers
^^^^^^^^^^^^^^^^^^^^


Callback Subscribers listen to a key in Redis and execute a user-specified function when an update occurs.
They are instantiated with an interface, channel name, a function, and dictionary specifying key-word
arguments to the function.

Instantiation is as below

.. code-block:: python

   def callback(data, updated_path, foo):
    print("Foo = {}".format(foo))
    print("Data = {}".format(data))

   # Initialize a callback subscriber
   subscriber = CallbackSubscriber(channel="callback_channel",
                                   interface=interface,
                                   callback_function=callback,
                                   kwargs={"foo":5})
   subscriber.listen()

**The Callback Function**

The callback function must have ``data`` and ``updated_path`` as it's first two arguments. When a publisher sets a key,
``data`` gives the entire updated data structure below the key and ``updated_path`` tells what path was updated.
Further arguments can be passed as keyword arguments set during the instantiation of subscriber.


If the publisher executes

.. code-block:: python

   publisher["callback_channel"] = {"number": 5, "string": "REEM"}
   publisher["callback_channel"]["number"] = 6

The subscriber program will have the following output:

.. code-block:: console

   Foo = 5
   Updated Path = callback_channel
   Data = {'number': 6, 'string': 'REEM'}
   Foo = 5
   Updated Path = callback_channel.number
   Data = {'number': 6, 'string': 'REEM'}