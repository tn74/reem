Advanced Usage
================================

This section explains less common functionality of REEM.

Custom Datatypes
*****************

REEM is designed to be customizable. Out of the box, it supports transferring native python types and numpy arrays.
You can, however, define how any type of data is stored in Redis using a ``Marshaller`` object.

Inside the module, ``reem.marshallers`` is the abstract class ``SpecialDatatypeMarshaller``. If you define your own marshaller, you must
subclass ``SpecialDatatypeMarshaller`` and fill in the methods. The class's documentation is below

.. autoclass:: reem.ships.SpecialDatatypeMarshaller
    :members:

To use a marshaller, include it as an argument when creating a ``RedisInterface`` object.

.. code-block:: python

    from reem import RedisInterface
    interface = RedisInterface(host="localhost", ships=[CustomMarshaller()])

This interface object can be passed to ``KeyValueStore``, ``PublishSpace``, or the ``XSubscriber`` classes instead of an IP address.


**Numpy Arrays**

Numpy Arrays are stored in Redis through marshalling. If you want to keep the default marshaller for numpy arrays when including
your custom marshallers, you must include the default numpy marshaller in the initializer.

.. code-block:: python

    interface = RedisInterface(host="localhost", ships=[reem.marshallers.NumpyMarshaller(), CustomMarshaller()])


See the implementation of the Numpy marshaller below

.. literalinclude:: ../reem/marshalling.py
   :lines: 114-
