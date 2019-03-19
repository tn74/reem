from testing import *
from reem.datatypes import KeyValueStore
from reem.supports import RedisInterface
from reem import shippers
import logging
import numpy as np
import redis

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

server = KeyValueStore(interface)


# Can't-Do  Behavior Defining Tests
def test_store_non_dict():
    # Store something that is not a dictionary at the top level of server. This wouldn't use ReJSON
    try:
        server["image_array"] = image_array
    except AssertionError:
        return
    assert False


def test_store_under_non_existant_top_key():
    # Storing into a subkey of top level key that does not yet exist
    random_key_name = get_flat_data()["string"] # A random key that does not exist with high probability
    try:
        server[random_key_name]["item"] = 5
    except redis.exceptions.ResponseError as e:
        # Redis spits error: new objects must be created at the root
        return
    assert False


def test_store_under_non_existant_sub_key():
    # Storing into a subkey of a subkey that does not yet exist
    test_kvs_upload_all()
    try:
        server["flat_data"]["not_real_key"]["not_real_key"] = 5
    except redis.exceptions.ResponseError as e:
        # Redis spits error: missing key at non-terminal path level
        return
    assert False

# ----------------------------


# Post several things with all types of data and ensure they are correct
def test_kvs_upload_all():
    server["image_dict"] = image_dict
    server["flat_data"] = flat_data
    server["nested_data"] = nested_data
    server["hundred_key_dict"] = hundred_key_dict
    server["layered_dict"] = layered_dictionary

    # Image Dictionary
    assert np.array_equal(server["image_dict"]["image"].read(), image_array)

    # Flat Data
    assert str(flat_data) == str(server["flat_data"].read())  # Serializing Dictionaries to compare them
    assert flat_data["number"] == server["flat_data"]["number"].read()

    # Nested Data
    assert str(nested_data) == str(server["nested_data"].read())
    assert str(nested_data["flat_nested"]) == str(server["nested_data"]["flat_nested"].read())
    assert nested_data["flat_nested"]["nested"]["number"] == server["nested_data"]["flat_nested"]["nested"]["number"].read()

    # Hundred Key Dictionary
    assert hundred_key_dict["copy_0_time"] == server["hundred_key_dict"]["copy_0_time"].read()
    assert hundred_key_dict["copy_49_time"] == server["hundred_key_dict"]["copy_49_time"].read()
    assert np.array_equal(hundred_key_dict["copy_0_np_arr"], server["hundred_key_dict"]["copy_0_np_arr"].read())
    assert np.array_equal(hundred_key_dict["copy_49_np_arr"], server["hundred_key_dict"]["copy_49_np_arr"].read())

    # Layered Dictionary
    assert str(layered_dictionary) == str(server["layered_dict"].read())


# Test Updating Elements inside the existing dictionaries
def test_kvs_update():
    test_kvs_upload_all()
    server["layered_dict"]["update"] = flat_data
    assert str(layered_dictionary) != str(server["layered_dict"].read())
    assert str(flat_data) == str(server["layered_dict"]["update"].read())






