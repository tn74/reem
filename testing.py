import datetime
import rejson
import numpy as np


rejson_client = rejson.Client(host='localhost', port=6379, decode_responses=True)


def generate_data(format='string', strlen=100, b=0, kb=0, mb=0):
    date_string = str(datetime.datetime.now()) + " "
    if format == 'string':
        length = strlen
    elif format == 'binary':
        length = b + 1024 * kb + (1024 ** 2) * mb
    else:
        raise ValueError("format for generate data not recognized")

    data = "{}{}".format(date_string, "".join(["a" for i in range(length - len(date_string))]))

    if format == 'string':
        return data
    return data.encode()


def time_code_segment(func, kwargs):
    """ Time a function and return milliseconds it took to run"""
    start = datetime.datetime.now()
    func(**kwargs)
    return (datetime.datetime.now() - start).total_seconds() * 1000


def multitrial_time_test(func, kwargs, iterations=3):
    """ Run a segment of code @iterations number of times and return an array of
    times required to complete each iteration """

    times = []
    for i in range(iterations):
        times.append(time_code_segment(func, kwargs))
    return times


flat_data = {'points': 30, 'rebounds': 20}
nested_data = {
    'name': 'Jack',
    'age': 26,
    'stats': {
        'points': 30,
        'rebounds': 20
    }
}


def sample_data():
    return {"time": str(datetime.datetime.now()), "np_arr": np.random.rand(3, 4)}


def make_complex_dictionary(data=sample_data()):
    """
    Makes a dictionary with lots of breadth and depth
    :return: dict
    """
    test = {}
    test["hundred_key"] = single_level_dictionary(keys=50, data=data)
    test["ten_level_dictionary"] = nested_level_dictionary(levels=10, data=data)
    return test


def single_level_dictionary(copies=50, data=sample_data()):
    """
    Return a dictionary where `data` has been replicated `copies` number of times in the first level of the dictionary.
    If data has two keys and copies=50, then the dictionary returned will have 100 keys
    :param copies: number of copies of data. If
    :param data: data to copy
    :return: dict
    """
    test = {}
    for i in range(copies):
        for key in data:
            test["copy_{}_{}".format(i, key)] = data[key]
    return test


def nested_level_dictionary(levels=10, data=sample_data()):
    """
    Return a dictioanrny where `data` is buried `levels` deep
    :param levels: Number of levels to bury
    :param data: Data to bury
    :return: dict
    """
    test = {}
    subdict = test
    for k in range(levels):
        subdict["sub_{}".format(k)] = {}
        subdict = subdict["sub_{}".format(k)]
    for key in data:
        subdict[key] = data[key]
    return test

