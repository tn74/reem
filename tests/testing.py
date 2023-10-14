import datetime
import numpy as np
import random
import string
from matplotlib import pyplot as plt
import multiprocessing


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


nested_data = {
    'name': 'Jack',
    'age': 26,
    'stats': {
        'points': 30,
        'rebounds': 20
    }
}


def get_flat_data():
    flat_data = {}
    flat_data["number"] = random.randint(0, 100000)
    flat_data["string"] = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
    return flat_data


def get_nested_data():
    data = {
        "flat": get_flat_data(),
        "flat_nested": {
            "nested": get_flat_data()
        }
    }
    return data


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


def plot_performance(info):
    """
    Plot a graphic representing the plot described by info
    :param info: {"title": "name", "plots": [ {plot1}, {times: [8,9]}] }
    :return:
    """
    plots = info["plots"]
    fig, axes = plt.subplots(1, 1, sharey=True)
    datas = []
    tick_labels = []
    for i, plot in enumerate(plots):
        datas.append(plot["times"])
        if "ticker_label" in plot:
            tick_labels.append(plot["ticker_label"])
        else:
            tick_labels.append("")
    axes.boxplot(datas)
    axes.set_xticklabels(tick_labels)
    axes.set_ylabel("Milliseconds")

    if "y_label" in info:
        axes.set_ylabel(info["y_label"])
    if "y_scale" in info:
        axes.set_yscale(info["y_scale"])
    if "x_label" in info:
        axes.set_xlabel(info["x_label"])

    fig.suptitle(info["title"])
    plt.show()


def run_as_processes(processes):
    """
    Run a set of functions, each in a different processes
    Waits until last process finishes
    :param processes: Tuples of (function, args, kwargs)
    :return: None
    """
    spawned_processes = []
    for func, args, kwargs in processes:
        spawned_processes.append(multiprocessing.Process(target=func, args=args, kwargs=kwargs))
        spawned_processes[-1].start()
    spawned_processes[-1].join()