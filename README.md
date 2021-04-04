# REEM

Trishul Nagenalli, updates by Kris Hauser

REEM (Redis Extendable Efficient Middleware) is a centralized middleware package for communication across distributed systems (e.g., robots). It is designed to be a single-package solution for passing information anywhere in the system while emphasizing ease of use and efficiency.

To make it easy, we chose to model information as a nested data structure that closely resembles python dictionaries. To the user, working with a database feels like working with a python dictionary. Out of the box, REEM supports communicating all native python types and numpy arrays.

To make it fast, we used [Redis](https://redis.io/) (an in-memory key-value database) running [ReJSON](https://oss.redislabs.com/redisjson/) (enabling Redis to store JSON data) as a central information store. To get maximum performance, we give users the power to control exactly how information is passed between the local program and Redis by defining their own encoder/decoder objects.

REEM currently offers two communication paradigms:
- get/set database
- publish-subscribe

To install the python package (and its dependencies), run
```
pip install reem
```
See the docs on [read the docs](https://reem.readthedocs.io)



Version history

0.1.1:
    - added `get()` and `set()` to KeyValueStore for direct access to Rejson's JSON.GET / JSON.SET.

0.1.0: fork by Kris Hauser
    - Can now access items by array index. 
    - Much easier to work with items like normal Python objects.  Can:
        - Can treat accesssors as variables using `read()` and `write()`, e.g., `var = server['key']; var.read(); var.write(x)`. (See bug fix note below).  
        - Delete items via `del server['key']` or `del server['key']['subkey']` (uses Rejson's JSON.DEL)
        - Increment/decrement values via  `server['key']['subkey'] += 1` or `-=` (uses Rejson's JSON.NUMINCRBY).  Note: does not work for Numpy arrays.
        - Multiply/divide values via `server['key']['subkey'] *= 2` or `/=` (uses Rejson's JSON.NUMMULTBY).  Note: does not work for Numpy arrays.
        - Append to arrays via `server['key'].append(x)` or `server['key']['subkey'].append(x)` (uses Rejson's JSON.ARRAPPEND)
        - Multiple append to arrays via `server['key'] += [x,y,z]` or `server['key']['subkey'] += [x,y,z]` (uses Rejson's JSON.ARRAPPEND)
        - Get sizes of arrays/objects using `len(server['key'])` or `len(server['key']['subkey'])` (uses Rejson's JSON.OBJLEN or JSON.ARRLEN)
        - Get types of items using `server['key'].type()` or `server['key']['subkey'].type()` (uses Rejson's JSON.TYPE)
    - KeyValueStore, PublishSpace, SilentSubscriber, and CallbackSubscriber are now in the global reem namespace.  Also, they can be given a string host rather than separately having to create a RedisInterface object.
    - KeyValueStore and PublishSpace are now thread safe. (Note: not thoroughly tested yet).
    - Objects retrieved by ['key'] no longer get clobbered when accessing ['subkey'].  E.g.,
       ```
       kvs['topkey'] = {'subkey':{'foo':3}}
       a = kvs['topkey']
       b = a['subkey']
       b['foo'] = 4
       print(a.read())  #prior version unexpected prints {'subkey':{'foo':3},'foo':4}, new version prints {'subkey'{'foo':4}} as expected.
       ```
    - Slight performance improvements for deeply nested accesses
    - Python 2 version automatically returns json objects with keys / values as str instead of unicode.

0.0.x: original from Trishul Nagenalli