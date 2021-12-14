from reem.connection import RedisInterface, PublishSpace, CallbackSubscriber
import time
import logging

# Logging Configuration
logging.basicConfig(
    format="%(asctime)20s %(filename)30s:%(lineno)3s  %(funcName)20s() %(levelname)10s     %(message)s",
    filename="actuator.log",
    filemode='w')
logger = logging.getLogger("script")
logger.setLevel(logging.INFO)

TIME_TO_RUN = 5.0  # seconds


# --------------------------- Main -----------------------------------


interface = RedisInterface(host="localhost")
pspace = PublishSpace(interface=interface)


def callback(data, updated_path):
    logger.info("Processed image {}".format(data["images_sent"]))


subscriber = CallbackSubscriber(
    channel="processed_info",
    interface=interface,
    callback_function=callback,
    kwargs={}
)

subscriber.listen()
time.sleep(TIME_TO_RUN)