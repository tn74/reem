from reem.datatypes import PublishSpace, CallbackSubscriber
from reem.connection import RedisInterface
import time

interface = RedisInterface(host="localhost")
interface.initialize()

# Initialize a publisher
publisher = PublishSpace(interface)


# Callback Function
def callback(data, updated_path, foo):
    print("Foo = {}".format(foo))
    print("Updated Path = {}".format(updated_path))
    print("Data = {}".format(data))


# # Initialize a callback subscriber
subscriber = CallbackSubscriber(channel="callback_channel",
                                interface=interface,
                                callback_function=callback,
                                kwargs={"foo": 5})
subscriber.listen()

publisher["callback_channel"] = {"number": 5, "string": "REEM"}
publisher["callback_channel"]["number"] = 6
time.sleep(.01)
