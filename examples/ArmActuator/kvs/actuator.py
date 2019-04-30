from reem.datatypes import KeyValueStore
from reem.connection import RedisInterface
import time
import logging

# Logging Configuration
logging.basicConfig(
    format="%(asctime)20s %(filename)30s:%(lineno)3s  %(funcName)20s() %(levelname)10s     %(message)s",
    filename="actuator_kvs.log",
    filemode='w')
logger = logging.getLogger("script")
logger.setLevel(logging.INFO)

TIME_TO_RUN = 5.0  # seconds
start_time = time.time()

# --------------------------- Main -----------------------------------

interface = RedisInterface(host="localhost")
kvs = KeyValueStore(interface)

polling_frequency = 1000  # Hz
polling_period = 1.0/polling_frequency

while time.time() < start_time + TIME_TO_RUN:
    next_iteration = time.time() + polling_period
    command = kvs["set_point"].read()
    logger.info("Read Set Point: {}".format(command))
    time.sleep(max(0.0, next_iteration - time.time()))