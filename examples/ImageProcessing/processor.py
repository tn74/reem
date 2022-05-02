from reem import PublishSpace, CallbackSubscriber
import numpy as np
import time
import logging

# Logging Configuration
logging.basicConfig(
    format="%(asctime)20s %(filename)30s:%(lineno)3s  %(funcName)20s() %(levelname)10s     %(message)s",
    filename="processor.log",
    filemode='w')
logger = logging.getLogger("script")
logger.setLevel(logging.INFO)

TIME_TO_RUN = 5.0  # seconds


# --------------------------- Main -----------------------------------


pspace = PublishSpace("localhost")


def callback(data, updated_path):
    pspace["processed_info"] = {
        "mean": np.mean(data["image"]),
        "time_stamp": time.time(),
        "images_sent": data["images_sent"]
    }
    logger.info("Processed image {}".format(data["images_sent"]))


subscriber = CallbackSubscriber(
    channel="raw_image",
    interface="localhost",
    callback_function=callback,
    kwargs={}
)

subscriber.listen()
time.sleep(TIME_TO_RUN)