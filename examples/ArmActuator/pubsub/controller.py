from reem import PublishSpace
import time
import logging

# Logging Configuration
logging.basicConfig(
    format="%(asctime)20s %(filename)30s:%(lineno)3s  %(funcName)20s() %(levelname)10s     %(message)s",
    filename="controller_silent_subcsriber.log",
    filemode='w')
logger = logging.getLogger("script")
logger.setLevel(logging.INFO)

TIME_TO_RUN = 10.0  # seconds


# --------------------------- Main -----------------------------------


pspace = PublishSpace("localhost")

set_frequency = 100  # Hz
set_period = 1.0/set_frequency

print("Writting to channel 'command' for",TIME_TO_RUN,"seconds...")
print("(Run actuator.py at the same time)")
num_messages = 0
start_time = time.time()
next_iteration = time.time()
while time.time() < start_time + TIME_TO_RUN:
    #this does the publishing
    command = time.time()
    pspace["command"] = command
    logger.info("Published Set Point: {}".format(command))

    #intelligently sleeps
    next_iteration += set_period
    t_now = time.time()
    time.sleep(max(0.0, next_iteration - t_now))
    if next_iteration < t_now:
        next_iteration = t_now + set_period
    num_messages += 1
print("Quitting, published",num_messages,"messages")