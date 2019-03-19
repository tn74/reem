from threading import Thread
import rejson
from .helper_functions import append_to_path


class RedisInterface:
    def __init__(self, host='localhost', shippers=[]):
        """
        Define a connection to redis with certain translators
        :param host: hostname of redis server connection
        :param translators: list of translators used by connections with this interface
        """
        self.hostname = host
        self.shippers = shippers
        self.client = rejson.Client(host=host, decode_responses=True)
        self.client_no_decode = rejson.Client(host=host)
        self.metadata_listener = MetadataListener(self)

        self.label_to_shipper = {}
        for sh in self.shippers:
            self.label_to_shipper[sh.get_label()] = sh

        self.shipper_labels = [sh.get_label() for sh in shippers]

    def initialize(self):
        """
        Call before doing anything with this connection
        :return:
        """
        self.metadata_listener.setDaemon(True)
        self.metadata_listener.start()


class MetadataListener(Thread):
    def __init__(self, interface):
        self.client = rejson.Client(host=interface.hostname)
        self.pubsub = self.client.pubsub()
        self.pubsub.psubscribe(['__keyspace@0__:*'])
        self.listeners = {}
        super().__init__()

    def add_listener(self, key_name, reader):
        self.listeners["__keyspace@0__:{}".format(key_name)] = reader

    def run(self):
        for item in self.pubsub.listen():
            channel = item['channel'].decode("utf_8")
            if channel in self.listeners:
                self.listeners[channel].pull_metadata = True


class PathHandler:
    def __init__(self, writer, reader, initial_path):
        self.writer = writer
        self.reader = reader
        self.path = initial_path

    def __getitem__(self, item):
        assert type(item) == str
        self.path = append_to_path(self.path, item)
        return self

    def __setitem__(self, instance, value):
        assert type(instance) == str
        self.path = append_to_path(self.path, instance)
        self.writer.send_to_redis(self.path, value)


class ReadablePathHandler(PathHandler):
    def read(self):
        return self.reader.read_from_redis(self.path)


class ChannelListener(Thread):
    def __init__(self, interface, channel_name, callback_function, kwargs):
        self.client = rejson.Client(host=interface.hostname)
        self.pubsub = self.client.pubsub()
        self.pubsub.psubscribe([channel_name])
        self.callback_function = callback_function
        self.kwargs = kwargs
        self.first_item_seen = False
        super().__init__()

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