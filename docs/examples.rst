Examples
==================


Image Processing System
#########################

Below is an example of what an image processing system might look like. In this robot, there are three components. The
robot's computation flow is as below

1. A camera takes an image and posts it to Redis
2. A computer processes that image and posts the result to Redis. Here, the process is just to compute the mean value of the image.
3. An actuator reads the result of the computation and does something with it.  Here, it just logs it.

All the code and each component's logs can be found in the `repository <https://github.com/krishauser/reem/tree/master/examples/ImageProcessing>`_

Camera
^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../examples/ImageProcessing/camera.py

Processor
^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../examples/ImageProcessing/processor.py

Actuator
^^^^^^^^^^^^^^^^^^
.. literalinclude:: ../examples/ImageProcessing/actuator.py



Arm Actuator
#########################

This examples tries to mimic a system where one computer is responsible for actuating motors at a specific frequency
while the set point is controlled by another computer at a different frequency.

We have implemented in two ways - using a database paradigm and a publish/subscribe paradigm.

All the code and each component's logs can be found in the `repository <https://github.com/krishauser/reem/tree/master/examples/ArmActuator>`_



Database
^^^^^^^^^

Controller
-----------
.. literalinclude:: ../examples/ArmActuator/kvs/controller.py

Actuator
-----------
.. literalinclude:: ../examples/ArmActuator/kvs/actuator.py


Publish/Subscribe
^^^^^^^^^^^^^^^^^^^^

Controller
-----------
.. literalinclude:: ../examples/ArmActuator/pubsub/controller.py

Actuator
-----------
.. literalinclude:: ../examples/ArmActuator/pubsub/actuator.py