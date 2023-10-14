from tests.testing import *
from reem.connection import KeyValueStore,RedisInterface
from reem import marshalling
import logging
import numpy as np


# Logging Configuration
log_file_name = "logs/reem_testing_kvs_timed.log"
FORMAT = "%(asctime)20s %(filename)30s:%(lineno)3s  %(funcName)20s() %(levelname)10s     %(message)s"
logging.basicConfig(format=FORMAT, filename=log_file_name, filemode='w')
logger = logging.getLogger("reem.datatypes")
logger.setLevel(logging.DEBUG)

image_array = np.random.rand(640, 480, 3)

flat_data = get_flat_data()
nested_data = get_nested_data()
image_dict = {"image": image_array}
hundred_key_dict = single_level_dictionary()
layered_dictionary = nested_level_dictionary(levels=20)

interface = RedisInterface(host="localhost",marshallers=[marshalling.NumpyMarshaller()])
interface.initialize()

server = KeyValueStore(interface)


def test_write_hundred_key_dict():
    for i in range(100):
        server["hundred_key_dict"] = hundred_key_dict
        logger.debug("\n")


def test_write_multilevel_dict():
    for i in range(100):
        server["layered_dict"] = layered_dictionary
        logger.debug("\n")


def test_read_hundred_key_dict():
    server["hundred_key_dict"] = hundred_key_dict
    for i in range(100):
        # server["hundred_key_dict"].read()
        # server["hundred_key_dict"]["single_key"] = {"number":5}
        server["image_dictionary"] = image_dict
        logger.debug("\n")


def test_list_set():
    list_dict = {"list": ["sdfdsfdfsfdsfsdfsd" for i in range(100)]}
    for i in range(100):
        server["list_dict"] = list_dict
        logger.debug("\n")


# New Tests
"""
Reset Whole Dictionary vs Reset each key
Come up with workarounds for slow sets and warnings about performance
"""

