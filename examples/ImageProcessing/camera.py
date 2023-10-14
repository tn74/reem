from reem import  PublishSpace
import numpy as np
import time
import logging

# Logging Configuration
logging.basicConfig(
    format="%(asctime)20s %(filename)30s:%(lineno)3s  %(funcName)20s() %(levelname)10s     %(message)s",
    filename="camera.log",
    filemode='w')
logger = logging.getLogger("script")
logger.setLevel(logging.INFO)

TIME_TO_RUN = 5.0  # seconds
start_time = time.time()


# --------------------------- Main -----------------------------------


pspace = PublishSpace("localhost")

image_count = 0
while time.time() < start_time + TIME_TO_RUN:
    image = np.random.rand(640, 480, 3)
    data = {
        "image": image,
        "images_sent": image_count,
        "time_stamp": time.time(),
    }
    pspace["raw_image"] = data
    logger.info("Published Image {}".format(image_count))
    image_count += 1
