from remi import datatypes, shippers
import numpy as np
import time

flat_data = {'points': 30, 'rebounds': 10}

nested_data = {
    'name': 'Jack',
    'age': 26,
    'stats': {
        'points': 30,
        'rebounds': 10
    }
}


# ---------------------- Simple Set Tests ----------------------

def test_flat_root_set():
    path = "."
    writer = datatypes.TWriter("test_set")
    writer.send_to_redis(path, flat_data)


def test_nested_root_set():
    path = "."
    writer = datatypes.TWriter("nested_set")
    writer.send_to_redis(path, nested_data)


def test_deeper_set():
    writer = datatypes.TWriter("nested_set")
    writer.send_to_redis(".", nested_data)
    writer.send_to_redis(".second_set", nested_data)


def test_flat_root_read():
    reader = datatypes.TReader("test_set")
    ret = reader.read_from_redis(".")
    print("Ret: {}".format(ret))


def test_nested_root_read():
    reader = datatypes.TReader("nested_set")
    ret = reader.read_from_redis(".")
    print("Ret: {}".format(ret))


def test_deeper_read():
    reader = datatypes.TReader("nested_set")
    ret = reader.read_from_redis(".second_set")
    print("Ret: {}".format(ret))

# ---------------------- Nonnative Object Tests ----------------------


nparr = np.arange(10)


def test_nested_np():
    writer = datatypes.TWriter("np_set", special_case_handlers=[shippers.NumpyHandler()])
    nested_data['nparr'] = nparr
    writer.send_to_redis(".", nested_data)


def test_nested_np_read():
    reader = datatypes.TReader("np_set", special_case_handlers=[shippers.NumpyHandler()])
    print("Read in: {}".format(reader.read_from_redis(".")))


# Write and Read Sequences

def test_sequence_1():
    writer = datatypes.TWriter("Sequence1", special_case_handlers=[shippers.NumpyHandler()])
    reader = datatypes.TReader("Sequence1", special_case_handlers=[shippers.NumpyHandler()])

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

    # writer.send_to_redis(".nparr", {"arr": nparr})
    # time.sleep(0.5)
    # print(reader.read_from_redis("."))
    # print(reader.read_from_redis(".nparr"))

