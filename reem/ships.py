from __future__ import print_function,unicode_literals

from abc import ABCMeta, abstractmethod
import numpy as np
import io


class SpecialDatatypeShip(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        super(SpecialDatatypeShip, self).__init__()

    @abstractmethod
    def check_fit(self, value):
        """ Determine if this ship will handle ``value``

        This method returns true if ``value`` is data that this ship is supposed to handle. If this ship handled all
        numpy arrays, it would check if ``value``'s type is a numpy array.

        Args:
            value: object to check

        Returns: True if ship will handle ``value``

        """
        pass

    @abstractmethod
    def write(self, key, value, client):
        """ Write ``value`` to Redis at the specified ``key`` using ``client``

        Given a Redis client, execute any number of needed commands to store the ``value`` in Redis. You
        are required to use the key given for REEM to find it. If you must store multiple pieces of information,
        use a `Redis Hash <https://redis.io/topics/data-types>`_ which acts like a one level dictionary.

        Args:
            key (str): The Redis key name this ship must store data under
            value: The value to write into Redis
            client: A `ReJSON Redis Client <https://github.com/RedisJSON/rejson-py>`_ pipeline

        Returns: None

        """
        pass

    @abstractmethod
    def read(self, key, client):
        """ Retrieve necessary information from Redis

        Given a Redis client, execute ONE command to retrieve all the information you need to rebuild the data
        that was stored in ``write`` from Redis. This method should execute the command that allows you to retrieve
        all data stored under key

        Args:
            key (str): a keyname that contains data stored by ``write``
            client: A `ReJSON Redis Client <https://github.com/RedisJSON/rejson-py>`_ pipeline

        Returns: None

        """
        pass

    @abstractmethod
    def interpret_read(self, responses):
        """ Translate Redis data into a local object

        Redis will reply to you with something according to what read command you executed in ``read``. This method
        takes whatever Redis replied with and turns it into an object identical to what was initially passed to
        ``write`` as value.

        Args:
            responses: Redis's reply data based on ``read`` method

        Returns: An object identical to what was initially written to Redis.

        """
        pass

    @abstractmethod
    def get_label(self):
        """ Return a unique string identifier

        This method should return a string that uniquely identifies this ship. REEM will use it to determine what ship
        to use to decode data that is already stored in Redis.

        Returns:
             str: the string identifier

        """
        pass


class NumpyShip(SpecialDatatypeShip):
    def check_fit(self, value):
        return type(value) in [np.array, np.ndarray]

    def write(self, key, value, client):
        client.hset(key, "arr", memoryview(value.data).tobytes())
        client.hset(key, "dtype", str(value.dtype))
        client.hset(key, "shape", str(value.shape))
        client.hset(key, "strides", str(value.strides))

    def get_label(self):
        return "default_numpy_handler"

    def read(self, key,  client):
        client.hgetall(key)

    def interpret_read(self, responses):
        hash = responses[0]
        dtype = eval("np.{}".format(hash[b'dtype'].decode('utf-8')))
        shape = hash[b'shape'].decode("utf-8")[1:-1]
        shape = tuple([int(s) for s in shape.split(",") if len(s) > 0])
        arr = np.frombuffer(hash[b'arr'], dtype)
        arr = np.reshape(arr, shape)
        return arr
