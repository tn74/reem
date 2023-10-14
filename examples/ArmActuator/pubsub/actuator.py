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

TIME_TO_RUN = 10.0  # seconds
start_time = time.time()

# --------------------------- Main -----------------------------------

subscriber = SilentSubscriber(channel="command", interface="localhost")
subscriber.listen()

frequency = 100  # Hz
period = 1.0/frequency

print("Reading from channel 'command' for",TIME_TO_RUN,"seconds...")
print("(Run controller.py at the same time)")
while time.time() < start_time + TIME_TO_RUN:
    next_iteration = time.time() + period
    command = subscriber.value()
    logger.info("Read Set Point: {} at time {}".format(command,time.time()))
    time.sleep(max(0.0, next_iteration - time.time()))
print("Quitting.")