from reem import PublishSpace, CallbackSubscriber
import time

# Initialize a publisher
publisher = PublishSpace("localhost")


# Callback Function
def callback(data, updated_path, foo):
    print("Foo = {}".format(foo))
    print("Updated Path = {}".format(updated_path))
    print("Data = {}".format(data))


# # Initialize a callback subscriber
subscriber = CallbackSubscriber(channel="callback_channel",
                                interface="localhost",
                                callback_function=callback,
                                kwargs={"foo": 5})
subscriber.listen()

publisher["callback_channel"] = {"number": 5, "string": "REEM"}
publisher["callback_channel"]["number"] = 6
time.sleep(.01)
