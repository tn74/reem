from remi import datatypes, shippers, supports
import numpy as np
import time
import logging
import datetime

# Logging Configuration
FORMAT = "%(filename)s:%(lineno)s  %(funcName)20s() %(levelname)10s     %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("reem.datatypes")
logger.setLevel(logging.DEBUG)


# Testing Help
intf = supports.RedisInterface(host='localhost', shippers=[shippers.NumpyHandler()])
intf.initialize()

flat_data = {'points': 30, 'rebounds': 20}

nested_data = {
    'name': 'Jack',
    'age': 26,
    'stats': {
        'points': 30,
        'rebounds': 20
    }
}


def compare_equality(d1, d2):
    return "{}".format(d1) == "{}".format(d2)


# ---------------------- Simple Set Tests ----------------------

def test_flat_root_set():
    path = "."
    writer = datatypes.Writer("test_set", intf)
    writer.send_to_redis(path, flat_data)


def test_nested_root_set():
    path = "."
    writer = datatypes.Writer("nested_set", intf)
    writer.send_to_redis(path, nested_data)


def test_deeper_set():
    writer = datatypes.Writer("nested_set", intf)
    nested_data["stats"]["points"] = nested_data["stats"]["points"] + 5
    writer.send_to_redis(".stats", nested_data["stats"])


def test_flat_root_read():
    test_flat_root_set()
    reader = datatypes.Reader("test_set", intf)
    ret = reader.read_from_redis(".")
    assert compare_equality(ret, flat_data)


def test_nested_root_read():
    test_nested_root_set()
    reader = datatypes.Reader("nested_set", intf)
    ret = reader.read_from_redis(".")
    assert compare_equality(ret, nested_data)


def test_deeper_read():
    test_deeper_set()
    reader = datatypes.Reader("nested_set", intf)
    ret = reader.read_from_redis(".stats")
    assert compare_equality(ret, nested_data["stats"])  # Pairs with test_deeper_set in which nested_data was set under this key

    # print("Ret: {}".format(ret))

# ---------------------- Nonnative Object Tests ----------------------


nparr = np.arange(10)


def test_nested_np():
    writer = datatypes.Writer("np_set", intf)
    nested_data['nparr'] = nparr
    writer.send_to_redis(".", nested_data)


def test_nested_np_read():
    reader = datatypes.Reader("np_set", intf)
    print("Read in: {}".format(reader.read_from_redis(".")))


# Write and Read Sequences

def test_sequence_1():
    writer = datatypes.Writer("Sequence1", intf)
    reader = datatypes.Reader("Sequence1", intf)

    writer.send_to_redis(".", flat_data)
    time.sleep(0.5)
    print("1. Full Data: {}".format(reader.read_from_redis(".")))

    writer.send_to_redis(".", nested_data)
    time.sleep(0.5)
    print("2. Full Data: {}".format(reader.read_from_redis(".")))

    writer.send_to_redis(".nparr", nparr)
    time.sleep(0.5)
    print("3. Full Data: {}".format(reader.read_from_redis(".")))
    print("3. NpArr: {}".format(reader.read_from_redis(".nparr")))
    print("3. Stats: {}".format(reader.read_from_redis(".stats")))

    writer.send_to_redis(".nparr", {"arr": nparr})
    time.sleep(0.5)
    print(reader.read_from_redis("."))
    print(reader.read_from_redis(".nparr"))


# ------------------------ Key Value Store Testing -------------------------
server = datatypes.KeyValueStore(intf)


def test_kvs_flat():
    server["flat_data"] = flat_data
    assert compare_equality(server["flat_data"].read(), flat_data)


def test_kvs_nested_set():
    server["nested_data"] = nested_data
    assert compare_equality(server["nested_data"].read(), nested_data)


def test_kvs_nested_deep_set():
    current_time = str(datetime.datetime.now())
    server["nested_data"]["deep_set"] = current_time
    assert compare_equality(server["nested_data"]["deep_set"].read(), current_time)


def test_np_read_write():
    random_array = np.random.rand(3, 4)
    # random_array = nparr
    server["seq1"] = {"nparr": random_array}
    print(server["seq1"].read())
    print({"nparr": random_array})
    assert compare_equality(server["seq1"].read(), {"nparr": random_array})
    assert compare_equality(server["seq1"]["nparr"].read(), random_array)


def test_sequence1():
    current_time = str(datetime.datetime.now())
    random_array = np.random.rand(3, 4)
    test = {}
    for i in range(20):
        test["time_{}".format(i)] = current_time
        test["numpy_{}".format(i)] = random_array
    subdict = {}
    test["subpath"] = subdict
    for k in range(10):
        subdict["sub_{}".format(k)] = {}
        subdict = subdict["sub_{}".format(k)]
    subdict["nparr"] = random_array
    subdict["time"] = current_time
    server["test_sequence_1"] = test

    get = server["test_sequence_1"].read()
    print(get)
    print(test)
    # assert compare_equality(test, server["test_sequence_1"].read())


def test_skip_metadata():
    current_time = str(datetime.datetime.now())
    random_array = np.random.rand(3, 4)
    test = {}
    for i in range(20):
        test["time_{}".format(i)] = current_time
        test["numpy_{}".format(i)] = random_array
    subdict = {}
    test["subpath"] = subdict
    for k in range(10):
        subdict["sub_{}".format(k)] = {}
        subdict = subdict["sub_{}".format(k)]
    subdict["nparr"] = random_array
    subdict["time"] = current_time

    server["test_skip_metadata"] = test
    server.set_metadata_write(["test_skip_metadata"], True)
    server["test_skip_metadata"] = test


### Publish Subscribe Testing ###

def test_publish():
    p = datatypes.Publisher("test_publish", intf)
    p.send_to_redis(".", flat_data)
    p.send_to_redis(".subkey", nparr)


def test_pubsub():
    p = datatypes.Publisher("test_pubsub", intf)
    active = datatypes.ActiveSubscriber("test_pubsub", intf)
    active.listen()
    p.send_to_redis(".", flat_data)
    time.sleep(1)
    logger.info(active.read_root())
    logger.info(active["points"])

