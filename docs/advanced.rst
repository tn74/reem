Advanced Usage
================================

This section explains less common functionality of REEM.

Custom Datatypes
*****************

REEM is designed to be customizable. Out of the box, it supports transferring native python types and numpy arrays.
You can, however, define how any type of data is stored in Redis using a ``Ship`` object.

Inside the module, ``reem.ships`` is the abstract class ``SpecialDatatypeShip``. If you define your own ship, you must
subclass ``SpecialDatatypeShip`` and fill in the methods. The class's documentation is below

.. autoclass:: reem.ships.SpecialDatatypeShip
    :members:

To use a ship, include it as an argument when creating a ``RedisInterface`` object.

.. code-block:: python

    interface = RedisInterface(host="localhost", ships=[CustomShip()])


**Numpy Arrays**

Numpy Arrays are stored in Redis through ships. If you want to keep the default ship for numpy arrays when including
your custom ships, you must include the default numpy ship in your list of ships.

.. code-block:: python

    interface = RedisInterface(host="localhost", ships=[reem.ships.NumpyShip(), CustomShip()])


See the implementation of the Numpy Ship below

.. literalinclude:: ../reem/ships.py
   :lines: 90-