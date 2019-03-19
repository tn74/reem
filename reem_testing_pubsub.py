from testing import *
from reem.datatypes import PublishSpace, ActiveSubscriber, PassiveSubscriber
from reem.supports import RedisInterface
from reem import shippers
import logging
import numpy as np
import time

# Logging Configuration
FORMAT = "%(filename)s:%(lineno)s  %(funcName)20s() %(levelname)10s     %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("reem.datatypes")
logger.setLevel(logging.WARNING)

image_array = np.random.rand(640, 480, 3)

flat_data = get_flat_data()
nested_data = get_nested_data()
image_dict = {"image": image_array}
hundred_key_dict = single_level_dictionary()
layered_dictionary = nested_level_dictionary(levels=3)

interface = RedisInterface(host="localhost", shippers=[shippers.NumpyHandler()])
interface.initialize()

pspace = PublishSpace(interface)


def test_basic():
    active = ActiveSubscriber("test_basic", interface)
    active.listen()

    pspace["test_basic"] = flat_data
    time.sleep(.01)
    assert str(active.read_root()) == str(flat_data)

    pspace["test_basic"]["subkey"] = flat_data
    time.sleep(.01)
    assert str(active.read_root()) != str(flat_data)
    assert str(active["subkey"]) == str(flat_data)
    assert active["number"] == flat_data["number"]







