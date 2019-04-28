from tests.testing import *
from reem.datatypes import KeyValueStore
from reem.connection import RedisInterface
import logging
import numpy as np
import redis

# Logging Configuration
log_file_name = "logs/reem_testing_kvs_timed.log"
FORMAT = "%(asctime)20s %(filename)15s:%(lineno)3s  %(funcName)30s() %(levelname)10s     %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("reem")
logger.setLevel(logging.DEBUG)


image_array = np.random.rand(640, 480, 3)

flat_data = get_flat_data()
nested_data = get_nested_data()
image_dict = {"image": image_array}
hundred_key_dict = single_level_dictionary()
layered_dictionary = nested_level_dictionary(levels=3)

interface = RedisInterface(host="localhost")
interface.initialize()

server = KeyValueStore(interface)


# Can't-Do  Behavior Defining Tests

def test_store_under_non_existant_top_key():
    # Storing into a subkey of top level key that does not yet exist
    random_key_name = get_flat_data()["string"]  # A random key that does not exist with high probability
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


def test_key_names():
    server["data"] = {"foo": 5}
    try:
        server["data"] = {"foo*": 5}
        assert False
    except AssertionError as e:
        pass

    try:
        server["data"] = {"foo.": 5}
        assert False
    except AssertionError as e:
        pass

    try:
        server["data"] = {"fo&&&&o": 5}
        assert False
    except AssertionError as e:
        pass

    try:
        server["data*"].read()
        assert False
    except AssertionError as e:
        pass

    try:
        server["data"]["data*"].read()
        assert False
    except AssertionError as e:
        pass

    # server["data"][0] = flat_data
    # assert str(server["data"][0].read() == str(flat_data))
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
    print("In House then read")
    print(layered_dictionary)
    print(server["layered_dict"].read())
    assert str(layered_dictionary) == str(server["layered_dict"].read())


# Test Updating Elements inside the existing dictionaries
def test_kvs_update():
    """
    Test Cases: See Comments
    """
    test_kvs_upload_all()

    # Add a new dictionary as a subkey
    server["layered_dict"]["update"] = flat_data
    assert str(layered_dictionary) != str(server["layered_dict"].read())
    assert str(flat_data) == str(server["layered_dict"]["update"].read())

    # Overwrite an existing dictionary subkey with a value
    server["layered_dict"]["update"] = image_array
    assert np.array_equal(image_array, server["layered_dict"]["update"].read())

    # Overwrite an existing value with a dictionary
    server["layered_dict"]["update"] = flat_data
    assert str(layered_dictionary) != str(server["layered_dict"].read())
    assert str(flat_data) == str(server["layered_dict"]["update"].read())

    # Overwrite everything
    server["layered_dict"] = {}
    assert(len(server["layered_dict"].read().keys()) == 0)


def test_kvs_schema_track():
    test_kvs_upload_all()
    server.track_schema_changes(False)  # Skipping Metadata Checking means setting a new key should fail

    # Try setting a new non-serializable
    try:
        server["layered_dict"]["update"] = image_array
    except TypeError as e:
        pass

    # Try setting a new dictionary that contains a non-serializable
    try:
        server["layered_dict"]["update"] = image_dict
    except TypeError as e:
        pass
    server.track_schema_changes(True)
    server["layered_dict"]["update2"] = image_dict
    assert np.array_equal(image_array, server["layered_dict"]["update2"]["image"].read())
    server["layered_dict"]["update2"] = image_array
    assert np.array_equal(image_array, server["layered_dict"]["update2"].read())


def test_store_non_dict():
    # Set a new top key as a non-dictionary
    server["non_dict_test"] = image_array
    assert np.array_equal(image_array, server["non_dict_test"].read())

    # Overwrite an existing value with a dictionary
    server["non_dict_test"] = flat_data
    assert str(flat_data) == str(server["non_dict_test"].read())

    # Overwrite an existing dictionary with a value
    server["non_dict_test"] = image_array
    assert np.array_equal(image_array, server["non_dict_test"].read())


def test_new_key_read():
    server["image_dict"] = image_dict
    kvs_new = KeyValueStore(interface)
    logger.debug("Set KVS Gets Metadata: {}".format(server.interface.client.jsonget(server.entries["image_dict"][1].metadata_key_name)))
    logger.debug("Get KVS Gets Metadata: {}".format(kvs_new.interface.client.jsonget(server.entries["image_dict"][1].metadata_key_name)))
    assert np.array_equal(kvs_new["image_dict"]["image"].read(), image_array)
