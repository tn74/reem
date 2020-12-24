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


class KeyAccessor:
    def __init__(self, parent, writer, reader, initial_path=[]):
        self.parent = parent
        self.writer = writer
        self.reader = reader
        self.path = initial_path
        self.path_str = None  #caches path string

    def __getitem__(self, key):
        assert check_valid_key_name_ext(key),"{} is not a valid key under path {}".format(key,key_sequence_to_path(self.path) if self.path_str is None else self.path_str)
        return self.__class__(self,self.writer,self.reader,self.path+[key])

    def __setitem__(self, key, value):
        assert check_valid_key_name_ext(key),"{} is not a valid key under path {}".format(key,key_sequence_to_path(self.path) if self.path_str is None else self.path_str)
        if self.path_str is None:
            self.path_str = key_sequence_to_path_ext(self.path)
        if self.path_str.endswith('.'): #root
            if isinstance(key,int):
                raise ValueError("Can't treat top-level key as an array access")
            path = self.path_str + key
        else:
            if isinstance(key,int):
                path = self.path_str + '[%d]'%(key,)
            else:
                path = self.path_str + '.' + key
        self.writer.send_to_redis(path, value)

    def __delitem__(self,key):
        assert check_valid_key_name_ext(key),"{} is not a valid key under path {}".format(key,key_sequence_to_path(self.path) if self.path_str is None else self.path_str)
        if self.path_str is None:
            self.path_str = key_sequence_to_path_ext(self.path)
        if self.path_str.endswith('.'): #root
            if isinstance(key,int):
                raise ValueError("Can't treat top-level key as an array access")
            path = self.path_str + key
        else:
            if isinstance(key,int):
                path = self.path_str + '[%d]'%(key,)
            else:
                path = self.path_str + '.' + key
        self.writer.delete_from_redis(path)

    def read(self):
        if self.path_str is None:
            self.path_str = key_sequence_to_path_ext(self.path)
        server_value = self.reader.read_from_redis(self.path_str)
        #if it's special, then its value is under _ROOT_VALUE_READ_NAME
        try:
            return server_value[_ROOT_VALUE_READ_NAME]
        except:
            return server_value

    # def __delitem__(self, key):
    #     value = self.read()
    #     del value[key]
    #     if len(self.path) == 0:  #top level key
    #         self.parent.__setitem__(self.reader.top_key_name,value)
    #     else:
    #         self.parent.__setitem__(self.path[-1],value)


class WriteOnlyKeyAccessor(KeyAccessor):
    def __init__(self,*args,**kwargs):
        KeyAccessor.__init__(self,*args,**kwargs)
        del self.read
        del self.__delitem__


class ActiveSubscriberKeyAccessor(KeyAccessor):
    def __init__(self,*args,**kwargs):
        KeyAccessor.__init__(self,*args,**kwargs)
        del self.__setitem__
        del self.__delitem__

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
            item = json_recode_str(item)
            channel = item['channel']
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
