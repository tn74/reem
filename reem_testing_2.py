from testing import *
from reem.datatypes import KeyValueStore
from reem.supports import RedisInterface
from reem import shippers
import logging
import numpy as np

# Logging Configuration
FORMAT = "%(filename)s:%(lineno)s  %(funcName)20s() %(levelname)10s     %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("reem.datatypes")
logger.setLevel(logging.DEBUG)


# image_array = np.random.rand( (640, 480, 3) )
image_array = np.random.random( (3, 4) )
image_dict = {"image": image_array}
hundred_key_dict = single_level_dictionary()
ten_level_dictionary = nested_level_dictionary(levels=10)

interface = RedisInterface(host="localhost", shippers=[shippers.NumpyHandler()])
interface.initialize()

server = KeyValueStore(interface)


def test_one():
    server["image_array"] = image_array
    assert np.array_equiv(server["image_array"].read(), image_array)
