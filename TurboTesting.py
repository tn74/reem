import TurboDT, TurboHandlers
import numpy as np

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
    writer = TurboDT.TWriter("test_set")
    writer.send_to_redis(path, flat_data)


def test_nested_root_set():
    path = "."
    writer = TurboDT.TWriter("nested_set")
    writer.send_to_redis(path, nested_data)


def test_deeper_set():
    writer = TurboDT.TWriter("nested_set")
    writer.send_to_redis(".", nested_data)
    writer.send_to_redis(".second_set", nested_data)


# ---------------------- Complex Tests ----------------------


nparr = np.arange(10)

def test_nested_np():
    writer = TurboDT.TWriter("np_set", special_case_handlers=[TurboHandlers.NumpyHandler()])
    nested_data['nparr'] = nparr
    writer.send_to_redis(".", nested_data)


