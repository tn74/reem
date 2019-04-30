from tests.testing import *
from reem.datatypes import *
from reem.connection import RedisInterface
import numpy as np
import logging
import time
import os
import shutil
from redis import Redis
from pottery import RedisDict

base = os.path.dirname(os.path.abspath(__file__))
log_file_name = os.path.join(base, "logs/reem_testing_kvs_timed.log")
FORMAT = "%(asctime)20s %(filename)30s:%(lineno)3s  %(funcName)20s() %(levelname)10s     %(message)s"
logging.basicConfig(format=FORMAT, filename=log_file_name, filemode='w')
logger = logging.getLogger("reem.datatypes")
logger.setLevel(logging.DEBUG)


interface = RedisInterface()
kvs = KeyValueStore(interface)
publisher = PublishSpace(interface)


def set(keys, value):
    setter = kvs
    for k in keys[:-1]:
        setter = setter[k]
    setter[keys[-1]] = value


def get(keys):
    setter = kvs
    for k in keys[:-1]:
        setter = setter[k]
    setter[keys[-1]].read()


def key_growth_strings():
    info = {"title": "Average Latency vs Number of 100 Character String Entries", "plots": [], "x_label": "Number of Keys"}
    for copies in [max(1, 100 * i) for i in range(5)]:
        data = single_level_dictionary(copies=copies, data={"single_key": "".join(["A" for i in range(10**2)])})
        p = {
            "ticker_label": copies,
            "times": multitrial_time_test(set, {"keys": ["key_growth"], "value": data}, iterations=100)
        }
        info["plots"].append(p)
        print("Completed: {}".format(copies))
    plot_performance(info)


def key_growth_numpy():
    info = {"title": "Average Latency vs Number of Numpy Entries", "plots": [], "x_label": "Number of Keys"}
    for copies in [max(1, 10 * i) for i in range(5)]:
        data = single_level_dictionary(copies=copies, data={"single_key": np.random.rand(3, 4)})
        p = {
            "ticker_label": copies,
            "times": multitrial_time_test(set, {"keys": ["key_growth_numpy"], "value": data}, iterations=100)
        }
        info["plots"].append(p)
        print("Completed: {}".format(copies))
    plot_performance(info)


def set_key_vs_set_dict():
    info = {"title": "Setting a Key vs Setting a Dictionary", "plots": [], "x_label": "Action"}
    arr = np.random.rand(100, 400)
    generated_string = generate_data('string', 300000)
    sets = [
        ("Set foo = {'bar': <np.ndarray>}", ["foo"], {"bar": arr}),
        ("Set foo.bar = <np.ndarray>", ["foo", "bar"], arr),
        ("Set foo = {'bar': <string>}", ["foo"], {"bar": generated_string}),
        ("Set foo.bar = <string>", ["foo", "bar"], generated_string)
    ]
    for label, keys, value in sets:
        p = {
            "ticker_label": label,
            "times": multitrial_time_test(set, {"keys": keys, "value": value}, iterations=300)
        }
        info["plots"].append(p)
    plot_performance(info)


def numpy_set_frame_rates():
    info = {"title": "Numpy Array Set Frame Rates", "plots": [], "x_label": "Image Shape", "y_label": "Frames/Second", "y_scale":'log'}
    # sets = [np.random.rand(640, 480, 3), np.random.rand(720, 480, 3), np.random.rand(1080, 720, 3)]
    sets = [np.random.rand(max(10, 200 * i), max(10, 200 * i)) for i in range(6)]
    for arr in sets:
        trials = multitrial_time_test(set, {"keys": ["np_frame_rate_test", "key"], "value": arr}, iterations=50)
        trials = [1000.0/t for t in trials]
        p = {
            "ticker_label": arr.shape,
            "times": trials
        }
        info["plots"].append(p)
    plot_performance(info)


def numpy_get_frame_rates():
    info = {"title": "Numpy Array Get Frame Rates", "plots": [], "x_label": "Image Shape", "y_label": "Frames/Second", "y_scale":'log'}
    # sets = [np.random.rand(640, 480, 3), np.random.rand(720, 480, 3), np.random.rand(1080, 720, 3)]
    sets = [np.random.rand(max(10, 200 * i), max(10, 200 * i)) for i in range(6)]
    for arr in sets:
        kvs["read_frame_rate_test"]["subkey"] = arr
        trials = multitrial_time_test(get, {"keys": ["read_frame_rate_test", "subkey"]}, iterations=50)
        trials = [1000.0 / t for t in trials]
        p = {
            "ticker_label": arr.shape,
            "times": trials
        }
        info["plots"].append(p)
    plot_performance(info)


def read_keys_individually(set_val, getset):
    for k, v in set_val["whole_dict"].items():
        if getset == "get":
            kvs["HundredKeyGet"]["whole_dict"][k].read()
        else:
            kvs["HundredKeySet"]["whole_dict"][k] = v


def hundred_key_sets():
    info = {"title": "How To Set 100 Keys", "plots": [], "x_label": "Method", "y_scale":"log"}
    generated_string = generate_data('string', 10000)
    copies = 100
    set_val = {}
    set_val["whole_dict"] = single_level_dictionary(copies=copies, data={"single_key": generated_string})
    set_val["list"] = [generated_string for i in range(copies)]
    kvs["HundredKeySet"] = set_val
    sets = [
        ("Dictionary", ["HundredKeySet", "whole_dict"], set_val["whole_dict"]),
        ("List", ["HundredKeySet", "list"], set_val["list"]),
    ]
    info["plots"].append({"ticker_label": "Read Individually", "times":multitrial_time_test(read_keys_individually, {"set_val": set_val, "getset": "set"}, iterations=100)})
    for label, keys, value in sets:
        p = {
            "ticker_label": label,
            "times": multitrial_time_test(set, {"keys": keys, "value": value}, iterations=100)
        }
        info["plots"].append(p)
    plot_performance(info)


def hundred_key_gets():
    info = {"title": "How To Get 100 Keys", "plots": [], "x_label": "Method", "y_scale":"log"}
    generated_string = generate_data('string', 10000)
    copies = 100
    set_val = {}
    set_val["whole_dict"] = single_level_dictionary(copies=copies, data={"single_key": generated_string})
    set_val["list"] = [generated_string for i in range(copies)]
    kvs["HundredKeyGet"] = set_val
    info["plots"].append({"ticker_label": "Read Individually",
                          "times": multitrial_time_test(read_keys_individually, {"set_val": set_val, "getset": "get"},
                                                        iterations=100)})
    sets = [
        ("Dictionary", ["HundredKeyGet", "whole_dict"], set_val["whole_dict"]),
        ("List", ["HundredKeyGet", "list"], set_val["list"]),
    ]
    for label, keys, value in sets:
        p = {
            "ticker_label": label,
            "times": multitrial_time_test(get, {"keys": keys}, iterations=100)
        }
        info["plots"].append(p)
    plot_performance(info)


# --------------------------- Subscriber Overhead Testing ---------------------------


PULSE_GAP = 0.02
TRIALS = 200


def append_time_to_list(data, updated_path, times):
    times.append(time.time() - data["timestamp"])


def overhead_testing_subscriber(test_name, timeout=10):
    times = []
    interface = RedisInterface()
    subscriber = CallbackSubscriber("overhead_test", interface, append_time_to_list, {"times": times})
    subscriber.listen()
    time.sleep(timeout)
    base = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base, "logs", "overhead_test", test_name)
    save_path = os.path.join(save_dir, "subscriber_{}.txt".format(os.getpid()))
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    with open(save_path, "w") as f:
        for t in times:
            f.write("{}\n".format(t))


def overhead_testing_publisher():
    interface = RedisInterface()
    publisher = PublishSpace(interface)
    for i in range(TRIALS):
        publisher["overhead_test"] = {"timestamp": time.time()}
        time.sleep(PULSE_GAP)


def generate_subscriber_overhead_data(num_subscriber_list):
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "overhead_test")
    shutil.rmtree(base)
    for num_subscribers in num_subscriber_list:
        processes = [(overhead_testing_publisher, (), {})]
        test_name = "subs={}".format(num_subscribers)
        save_dir = os.path.join(base, test_name)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        for i in range(num_subscribers):
            processes.append((overhead_testing_subscriber, (test_name, PULSE_GAP * TRIALS), {}))

        run_as_processes(processes)
        print("Completed test with {} subscribers".format(num_subscribers))


def plot_overhead_data():
    time_data = {}
    base = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base, "logs", "overhead_test")
    for dirpath, dirs, files in os.walk(save_dir):
        if "subs" not in dirpath:
            continue
        num_subscribers = int(dirpath.split("subs=")[1])
        time_data[num_subscribers] = []
        for fpath in files:
            with open(os.path.join(dirpath, fpath), 'r') as file:
                for line in file:
                    time_data[num_subscribers].append(float(line) * 1000)   # Seconds to milliseconds conversion
    plot_info = {
        "title": "# of Publishers vs Message Latency ({} Messages Published)".format(TRIALS),
        "x_label": "# of Subscribers",
        "y_label": "Latency (ms)",
        "y_scale": "log",
        "plots": []
    }
    for key, value in sorted(time_data.items(), key=lambda kv: kv[0]):
        plot_info["plots"].append({"ticker_label": key, "times": value})
    plot_performance(plot_info)


def overhead_tests_main():
    generate_subscriber_overhead_data([1, 10, 100, 1000])
    plot_overhead_data()


# ------------------- Pottery Testing -----------------------------


def set_pottery(redis_dict, value):
    redis_dict["data"] = value


def compare_to_potteryx():
    client = Redis.from_url('redis://localhost:6379/')
    pottery_dict = RedisDict(redis=client, key='pottery')

    info = {"title": "REEM vs Pottery", "plots": [],
            "x_label": "Package"}

    data = single_level_dictionary(
        copies=100,
        data={
            "single_key": "".join(["A" for i in range(10 ** 2)]),
            "nested_data": {
                "subkey": "".join(["A" for i in range(10 ** 2)])
            }
        }
    )

    # REEM
    p = {
        "ticker_label": "REEM",
        "times": multitrial_time_test(set, {"keys": ["key_growth"], "value": data}, iterations=100)
    }
    info["plots"].append(p)

    # Pottery
    p = {
        "ticker_label": "Pottery",
        "times": multitrial_time_test(set_pottery, {"redis_dict": pottery_dict, "value": data}, iterations=100)
    }
    info["plots"].append(p)
    plot_performance(info)


if __name__ == "__main__":
    # key_growth_strings()
    # key_growth_numpy()
    # set_key_vs_set_dict()
    # numpy_set_frame_rates()
    # numpy_get_frame_rates()
    # hundred_key_sets()
    # hundred_key_gets()
    # overhead_tests_main()
    compare_to_potteryx()