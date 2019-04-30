from reem.datatypes import PublishSpace
from reem.connection import RedisInterface
import time
import logging

# Logging Configuration
logging.basicConfig(
    format="%(asctime)20s %(filename)30s:%(lineno)3s  %(funcName)20s() %(levelname)10s     %(message)s",
    filename="controller_silent_subcsriber.log",
    filemode='w')
logger = logging.getLogger("script")
logger.setLevel(logging.INFO)

TIME_TO_RUN = 5.0  # seconds
start_time = time.time()


# --------------------------- Main -----------------------------------


interface = RedisInterface(host="localhost")
pspace = PublishSpace(interface=interface)

set_frequency = 100  # Hz
set_period = 1.0/set_frequency

while time.time() < start_time + TIME_TO_RUN:
    next_iteration = time.time() + set_period
    command = time.time()
    pspace["command"] = command
    logger.info("Published Set Point: {}".format(command))
    time.sleep(max(0.0, next_iteration - time.time()))