Server Utilities
================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

REEM comes with some server-side utilities to help make debugging a little bit easier. They are located together
inside a `GitHub repository <https://github.com/tn74/reem-servery>`_. It is not a PyPi package. Download the repository and install dependencies with the below
script

.. code-block:: bash

   git clone git@github.com:tn74/reem-server.git
   cd reem-server
   pip3 install -r requirements.txt

Browser
###############

The browser allows you to view data inside a Redis server in a web format.
It is written with the python Django web framework. Make sure you have a
Redis server turned on before starting it. To start the browser's server,
run the following script starting at the ``reem-server`` directory

.. code-block:: bash

   cd browser
   python manage.py runserver

Some Notes:

1. The web-browser-server assumes that the Redis server is on the same machine and bound to the localhost interface.
If the browser is being launched from a different computer as the Redis server, change the REEM_HOSTNAME variable
at the bottom of the `django configuration file <https://github.com/tn74/reem-server/blob/master/browser/reem_browser/settings.py>`_

2. Running ``python manage.py runserver`` starts the server on the localhost interface. If you want to connect to
this web browser from other machines, run ``python manage.py runserver 0.0.0.0:8000`` and access the browser at the
ip address of the machine running the browser and port 8000.

3. To access data at a specific path in redis, go to ``http://localhost:8000/view/<reem-path>``.
For example, if you wanted to see what was stored at "foo.bar.subkey",
go to the url "http://127.0.0.1:8000/view/foo.bar.subkey"

4. Numpy data can be viewed in two ways

   1. A pretty printed list of numbers
   2. An image

   - If you try to view an image-sized numpy array as a list of pretty printed numbers, the server will be very slow.


A screen capture of what the browser looks like is below

.. image:: _static/browser_screen_cap.png


Logger
##########

We want to implement logging functionality that ultimately allows users to see how specific keys change in
Redis over time. Imagine having the above  browser with a slider bar that allows you to see how a key changes as
you drag the slider. We have begun testing two ways of doing this but neither is fully functional.


RDB Logger
^^^^^^^^^^^

Redis has two natural ways of storing data to persistent memory. It can use RDB files that snapshot the database
at a specific point in time and AOF files that track
all changes to Redis in an append only fashion.

RDB
----
Redis can be told to save the database to an RDB file periodically but it is configured to always write to the same
file. This poses a problem if we would like to save the state of data at previous points in time.

There is a script in the `reem-server repository <https://github.com/tn74/reem-server/blob/master/logger_rdb/reem-logger.py>`_
that copies the redis's dump file periodically to a folder so users can save snapshots of Redis data in time.
The script is called according to the syntax

``python reem-logger <path-to-directory-of-snapshots> <path-to-redis-dump-file> <seconds-between-snapshot>``

The next (unimplemented) step is to select a snapshot based on a timestamp and load a Redis server with it. After
that, we could use the REEM client to query the desired data.

There are some existing `tools <https://github.com/sripathikrishnan/redis-rdb-tools>`_
that allow the user to parse through RDB directly without starting a Redis server, but they generally
do not support parsing ReJSON commands since ReJSON is a young third-party module.


AOF
----

Ideally we would not have to copy data that doesn't change much like we do when we save so many RDB files. We would
like to be able to use the AOF file that tracks all changes made to the Redis server. It is played back by a Redis
server when it is used to restore a specific state. More research must be done into finding parsers for AOF files.

Custom Logger
^^^^^^^^^^^^^^^

Some work was done on developing a custom logger. This custom program would not use a standard Redis data saving
format but would use REEM to retrieve data from Redis periodically and use numpy to store it. The user would
be able to specify a particular frequency for a given key. The code is
`online here <https://github.com/tn74/reem-server/tree/master/logger_custom>`_

This `log function <https://github.com/tn74/reem-server/blob/master/logger_custom/reem-logger.py>`_ would take in a
`key file <https://github.com/tn74/reem-server/blob/master/logger_custom/test_key_files/key1.txt>`_
that specified a paths and periods (representing how frequently to read a specific path in Redis) and an output
directory to store saved data.


