from reem.connection import SilentSubscriber
import time
import logging

# Logging Configuration
logging.basicConfig(
    format="%(asctime)20s %(filename)30s:%(lineno)3s  %(funcName)20s() %(levelname)10s     %(message)s",
    filename="actuator_silent_subscriber.log",
    filemode='w')
logger = logging.getLogger("script")
logger.setLevel(logging.INFO)

TIME_TO_RUN = 5.0  # seconds
start_time = time.time()

# --------------------------- Main -----------------------------------

subscriber = SilentSubscriber(channel="command", interface="localhost")
subscriber.listen()

frequency = 1000  # Hz
period = 1.0/frequency

while time.time() < start_time + TIME_TO_RUN:
    next_iteration = time.time() + period
    command = subscriber.value()
    logger.info("Read Set Point: {}".format(command))
    time.sleep(max(0.0, next_iteration - time.time()))