from testing import *
from reem.datatypes import KeyValueStore
from reem.supports import RedisInterface
from reem import shippers
import logging
import numpy as np
import redis

# Logging Configuration
log_file_basename = "logs/reem_testing_kvs_timed"
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

interface = RedisInterface(host="localhost", shippers=[shippers.NumpyHandler()])
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
        server["hundred_key_dict"].read()
        logger.debug("\n")