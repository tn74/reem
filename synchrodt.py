from collections.abc import MutableMapping
from queue import Queue
from threading import Thread
import rejson


DB_WRITE_QUEUE = Queue()
REDIS_CLIENT = rejson.Client(host='localhost')


class ClientThread(Thread):
    def __init__(self, db_write_queue):
        self.db_write_queue = db_write_queue
        super(ClientThread, self).__init__()
        self.setDaemon(True)


    def run(self):
        while True:
            func, args, kwargs = self.db_write_queue.get(block=True)
            func(*args, **kwargs)
            print("Executed {} {} {} ".format(func, args, kwargs))


class SynchroDict(MutableMapping):
    def __init__(self, *args, **kwargs):

        # Ensure that this dictionary knows what it's key in its parent dictionary is
        if 'super_key' not in kwargs.keys():
            raise KeyError("No key name for initialization of SynchroDict")
        self.super_key = kwargs['super_key']

        # Ensure that this dictionary has access to it's parent dictionary
        self.parent_dictionary = None
        if 'parent_dictionary' in kwargs.keys():
            if type(kwargs['parent_dictionary']) is not type(self):
                raise ValueError("Parent Dictionary is not of type SynchroDict")
            self.parent_dictionary = kwargs['parent_dictionary']

        # Map value types to their set handlers
        self.set_handlers = {
            str: self.handle_set_string,
            dict: self.handle_set_dict,
            type(dict): self.handle_set_type
        }

        # Map String representations to class they represent
        self.type_string_to_key_type = {}
        for class_type in self.set_handlers.keys():
            self.type_string_to_key_type[str(class_type)] = class_type

        # Dictionary that stores local copy of information for fast access
        self.local_copy_dictionary = {}
        self.user_key_to_redis_key_map = {}

        # Seperator between variable name and type in redis key name
        self.separator = "!@#$%^&"

    @staticmethod
    def build_from_schema(schema, redis_key):
        sd = SynchroDict(super_key=redis_key)
        for k, v in schema.items():
            sd[k] = v
        return sd

    def get_redis_base_key(self):
        if self.parent_dictionary is not None:
            return "{}.{}".format(self.parent_dictionary.get_redis_base_key(), self.super_key)
        else:
            return self.super_key

    def __getitem__(self, item):
        return self.local_copy_dictionary[item]

    def __delitem__(self, key):
        return self.local_copy_dictionary.pop(key, None)

    def __iter__(self):
        return self.local_copy_dictionary.keys()

    def __len__(self):
        return len(self.local_copy_dictionary)

    def __setitem__(self, item, value):
        if type(value) not in self.set_handlers.keys():
            raise ValueError("Value of Type {} not currently accepted".format(type(value)))
        if type(value) in [type(dict), dict]:
            self.set_handlers[type(value)](item, value)
            return

        try:
            redis_key_name = self.user_key_to_redis_key_map[item]
            type_string = redis_key_name.split(self.separator)[1]
            required_type = self.type_string_to_key_type[type_string]
            return self.set_handlers[required_type](item, value)
        except Exception as e:
            raise KeyError("Key {} not found in schema or value does not match schema type".format(item))

    def handle_set_string(self, item, value):
        self.local_copy_dictionary[item] = value
        DB_WRITE_QUEUE.put((REDIS_CLIENT.set, (item, value), {}))

    def handle_set_dict(self, item, value):
        synchro_equivalent = SynchroDict(super_key=item, parent_dictionary=self)
        for k, v in value.items():
            synchro_equivalent[k] = v
        self.local_copy_dictionary[item] = synchro_equivalent

    def handle_set_type(self, item, value):
        # Cannot set it to the class 'type' produces or one we don't know how to handle
        if value == type(dict) or value not in self.set_handlers.keys():
            raise ValueError("Type: {} cannot be incorporated in the schema".format(value))
        self.user_key_to_redis_key_map[item] = "{}{}{}".format(item, self.separator, value)
        self.local_copy_dictionary[item] = None

    def __str__(self):
        return str(self.local_copy_dictionary)

    def __repr__(self):
        return repr(self.local_copy_dictionary)


redis_thread = ClientThread(DB_WRITE_QUEUE)
redis_thread.start()