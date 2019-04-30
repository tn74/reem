# REEM

REEM (Redis Extendable Efficient Middleware) is a centralized middleware package for robotic communication. It is designed to be a single-package solution for passing information anywhere in the robot while emphasizing ease of use and efficiency.

To make it easy, we chose to model information as a nested data structure that closely resembles python dictionaries. To the user, working with a database feels like working with a python dictionary. Out of the box, REEM supports communicating all native python types and numpy arrays.

To make it fast, we used [Redis](https://redis.io/) (an in-memory key-value database) running [ReJSON](https://oss.redislabs.com/redisjson/) (enabling Redis to store JSON data) as a central information store. To get maximum performance, we give users the power to control exactly how information is passed between the local program and Redis by defining their own encoder/decoder objects.

REEM currently offers two communication paradigms:
- get/set database
- publish-subscribe

To install the python package (and its dependencies), run
```
pip install reem rejson redis six numpy
```
See the docs on [read the docs](https://reem.readthedocs.io)


