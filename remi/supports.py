from threading import Thread
import rejson


class RedisInterface():
    def __init__(self, host='localhost', shippers=[]):
        """
        Define a connection to redis with certain translators
        :param host: hostname of redis server connection
        :param translators: list of translators used by connections with this interface
        """
        self.hostname = host
        self.shippers = shippers
        self.client = rejson.Client(host=host, decode_responses=True)
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
            if channel in self.listeners.keys():
                self.listeners[channel].pull_metadata = True


### Naming
"""
Rapid Extendable Middleware
Redis Medium Extendable Middleware
Redis Robotic Communication

Redis Extendable Middleware
"""