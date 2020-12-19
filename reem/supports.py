from __future__ import print_function

from threading import Thread, Lock
import rejson
from .utilities import *

_ROOT_VALUE_READ_NAME = "{}ROOT{}".format(ROOT_VALUE_SEQUENCE, ROOT_VALUE_SEQUENCE)

class MetadataListener:
    def __init__(self, interface):
        self.client = rejson.Client(host=interface.hostname)
        self.pubsub = self.client.pubsub()
        self.pubsub.psubscribe(['__keyspace@0__:*'])
        self.listeners = {}

    def add_listener(self, key_name, reader):
        listen_name = "__keyspace@0__:{}".format(key_name)
        self.listeners.setdefault(listen_name,[]).append(reader)

    def flush(self):
        while True:
            item = self.pubsub.get_message()
            if item is None:
                break
            channel = item['channel'].decode("utf_8")
            try:
                for listener in self.listeners[channel]:
                    listener.pull_metadata = True
            except KeyError:
                pass


class PathHandler:
    def __init__(self, writer, reader, initial_path=[]):
        self.writer = writer
        self.reader = reader
        self.path = initial_path
        self.path_str = None  #caches path string

    def __getitem__(self, item):
        assert check_valid_key_name(item)
        return self.__class__(self.writer,self.reader,self.path+[item])

    def __setitem__(self, instance, value):
        assert check_valid_key_name(instance)
        if self.path_str is None:
            self.path_str = key_sequence_to_path(self.path)
        path = self.path_str + '.' + instance
        self.writer.send_to_redis(path, value)


class ReadablePathHandler(PathHandler):
    def read(self):
        if self.path_str is None:
            self.path_str = key_sequence_to_path(self.path)
        server_value = self.reader.read_from_redis(self.path_str)
        try:
            return server_value[_ROOT_VALUE_READ_NAME]
        except Exception:
            pass
        return server_value


class ActiveSubscriberPathHandler(PathHandler):
    def read(self):
        return_val = self.reader.local_copy
        dissect_path = self.path[1:]  #skip initial .
        if len(dissect_path) == 0:
            pass
        else:
            for key in dissect_path:
                return_val = return_val[key]
        if type(return_val) == dict:
            return copy_dictionary_without_paths(return_val, [])
        return return_val

    def __setitem__(self, instance, value):
        raise Exception("Cannot set value for a subscriber")


class ChannelListener(Thread):
    def __init__(self, interface, channel_name, callback_function, kwargs):
        Thread.__init__(self)
        self.client = rejson.Client(host=interface.hostname)
        self.pubsub = self.client.pubsub()
        self.pubsub.psubscribe([channel_name])
        self.callback_function = callback_function
        self.kwargs = kwargs
        self.first_item_seen = False

    def run(self):
        for item in self.pubsub.listen():
            # First Item is a generic message that we need to get rid of
            if not self.first_item_seen:
                self.first_item_seen = True
                continue
            channel = item['channel'].decode("utf_8")
            message = item['data']
            self.callback_function(channel=channel, message=message, **self.kwargs)

"""
Naming:
Rapid Extendable Middleware
Redis Medium Extendable Middleware
Redis Robotic Communication

Redis Extendable Middleware

Extendable Efficient Redis Middleware
Redis Extendable Efficient Middleware
reem
"""
