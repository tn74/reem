from reem import PublishSpace, CallbackSubscriber
import time

# Initialize a publisher
publisher = PublishSpace("localhost")

t0 = None

# Callback Function
def callback(data, updated_path, foo):
    global t0
    print("Received message from publisher, delay",time.time()-t0)
    print("Foo = {}".format(foo))
    print("Updated Path = {}".format(updated_path))
    print("Data = {}".format(data))


# # Initialize a callback subscriber
subscriber = CallbackSubscriber(channel="callback_channel",
                                interface="localhost",
                                callback_function=callback,
                                kwargs={"foo": 5})
subscriber.listen()

t0 = time.time()
publisher["callback_channel"] = {"number": 5, "string": "REEM"}
#windows is sometimes ungodly slow at setting up an initial connection
time.sleep(2.0)
for i in range(6,20):
    publisher["callback_channel"]["number"] = i
    time.sleep(0.1)
print("Done.")
