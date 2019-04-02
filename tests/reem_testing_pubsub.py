from tests.testing import *
from reem.datatypes import PublishSpace, SilentSubscriber, CallbackSubscriber
from reem.connection import RedisInterface
import logging
import numpy as np
import time
from queue import Queue

# Logging Configuration
FORMAT = "%(asctime)20s %(filename)s:%(lineno)3s  %(funcName)20s() %(levelname)10s     %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("reem.datatypes")
logger.setLevel(logging.DEBUG)

image_array = np.random.rand(640, 480, 3)

flat_data = get_flat_data()
nested_data = get_nested_data()
image_dict = {"image": image_array}
hundred_key_dict = single_level_dictionary()
layered_dictionary = nested_level_dictionary(levels=3)

interface = RedisInterface(host="localhost")
interface.initialize()

pspace = PublishSpace(interface)
pspace.track_schema_changes(True)
active = SilentSubscriber("channel", interface)
active.listen()


def test_active_update_basic():
    pspace["channel"] = flat_data
    time.sleep(.05)
    assert str(active.value()) == str(flat_data)


def test_active_update_sequence():
    test_active_update_basic()
    pspace["channel"]["subkey"] = flat_data
    time.sleep(.01)
    # print("\n\n\nFlat_Data: {}".format(flat_data))
    # print("Read:      {}\n\n\n".format(str(active["subkey"].read())))
    assert str(active.value()) != str(flat_data)
    assert str(active["subkey"].read()) == str(flat_data)

    assert active["number"].read() == flat_data["number"]


def test_update_with_nparrays():
    test_active_update_sequence()
    pspace["channel"]["nparr1"] = image_dict
    time.sleep(.05)
    assert np.array_equal(image_dict["image"], active["nparr1"]["image"].read())
    time.sleep(.05)
    try:
        pspace["channel"]["nparr2"] = image_dict
        assert False
    except Exception:
        pass


# Callback Subscriber Testing
def print_data(data, updated_path):
    print("Updated Path: {}, Data: {}".format(updated_path, data))


def test_callback_subscriber():
    update_subscriber = CallbackSubscriber("channel", interface, print_data, {})
    update_subscriber.listen()
    test_update_with_nparrays()



"""
Subscribing to N Topics:
What is the overhead?
Writing to redis on callback
Quit subscriber by using a timeout to check if flag is set inside

Bigger Distributed System:
Server needs to distribute work to smaller servers and gather responses back
A input data B processes it C reads it
Implement RPC - Make sure responses are given to the right recipients
"""





