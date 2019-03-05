from remi import datatypes, shippers, supports
import numpy as np
import time


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
    writer.send_to_redis(".", nested_data)
    writer.send_to_redis(".second_set", nested_data)


def test_flat_root_read():
    reader = datatypes.Reader("test_set", intf)
    ret = reader.read_from_redis(".")
    print("Ret: {}".format(ret))


def test_nested_root_read():
    reader = datatypes.Reader("nested_set", intf)
    ret = reader.read_from_redis(".")
    print("Ret: {}".format(ret))


def test_deeper_read():
    reader = datatypes.Reader("nested_set", intf)
    ret = reader.read_from_redis(".second_set")
    print("Ret: {}".format(ret))

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

