from .helper_functions import *
from .supports import ReadablePathHandler, PathHandler, ChannelListener, ActiveSubscriberPathHandler
from rejson import Path, Client
import logging

logger = logging.getLogger("reem.datatypes")


class Writer:
    def __init__(self, top_key_name, interface):
        self.interface = interface
        self.top_key_name = top_key_name

        self.separator = "&&&&" # If changed, ensure it is changed in helper_functions too
        self.metadata = {"special_paths": {}, "required_labels": self.interface.shipper_labels}
        self.sp_to_label = self.metadata["special_paths"]
        self.pipeline = self.interface.client.pipeline()

        self.metadata_key_name = "{}{}metadata".format(self.top_key_name, self.separator)
        self.interface.client.jsonset(self.metadata_key_name, Path.rootPath(), self.metadata)

        self.do_metadata_update = True
        self.first_update_not_complete = True

    def send_to_redis(self, path, value):
        logger.info("SET {} {} = {}".format(self.top_key_name, path, type(value)))
        # logger.debug("SET {} {} = {}".format(self.top_key_name, path, value))
        self.process_metadata(path, value)
        logger.debug("SET {} {} Metadata: {}".format(self.top_key_name, path, self.metadata))
        self.publish_non_serializables(path, value)
        logger.debug("SET {} {} Non-Serializables Pipelined".format(self.top_key_name, path))
        self.publish_serializables(path, value)
        logger.debug("SET {} {} Serializables Pipelined".format(self.top_key_name, path))
        self.pipeline.execute()
        logger.debug("SET {} {} Pipeline Executed".format(self.top_key_name, path))

    def process_metadata(self, path, value):
        if self.do_metadata_update or (self.first_update_not_complete and path == Path.rootPath()):
            self.update_metadata(path, value)
            self.first_update_not_complete = True

    def update_metadata(self, path, value):
        if path == Path.rootPath():
            path = ""

        adds, dels = get_special_path_updates(path, value, self.sp_to_label, self.interface.label_to_shipper)
        for path in dels:
            self.pipeline.delete("{}.{}".format(self.top_key_name, path))
            self.sp_to_label.pop(path)
        for path, label in adds:
            self.sp_to_label[path] = label
        if len(adds) > 0:
            self.pipeline.jsonset(self.metadata_key_name, ".special_paths", self.sp_to_label)
            channel, message = "__keyspace@0__:{}".format(self.metadata_key_name), "set"
            self.pipeline.publish(channel, message)  # Homemade key-space notification for metadata updates

    def publish_non_serializables(self, path, value):
        publish_paths = list(filter(lambda special_path: path == special_path[:len(path)], self.sp_to_label.keys()))
        for update_path in publish_paths:
            special_name = "{}{}".format(self.top_key_name, update_path)
            extract_path = update_path[len(path) - 1:]  # Get rid of leading path to work with paths inside `value`
            self.interface.label_to_shipper[self.sp_to_label[update_path]].write(
                key=special_name,
                value=extract_object(value, path_to_key_sequence(extract_path)),
                client=self.pipeline
            )

    def publish_serializables(self, path, value):
        if type(value) is dict:
            intrusive_paths = [p for p in self.sp_to_label if p[:len(path)] == path]
            intrusive_paths = [path_to_key_sequence(p[len(path) - 1:]) for p in intrusive_paths]
            excised_copy = copy_dictionary_without_paths(value, intrusive_paths)
            self.pipeline.jsonset(self.top_key_name, path, excised_copy)
        elif path not in self.sp_to_label:
            self.pipeline.jsonset(self.top_key_name, path, value)


class Reader:
    def __init__(self, top_key_name, interface):
        self.interface = interface
        self.top_key_name = top_key_name

        self.separator = "&&&&"
        self.metadata = {"special_paths": {}, "required_labels": self.interface.shipper_labels}
        self.sp_to_label = self.metadata["special_paths"]
        self.update_metadata_flag = False
        self.pipeline = self.interface.client.pipeline()
        self.pipeline_no_decode = self.interface.client_no_decode.pipeline()

        self.metadata_key_name = "{}{}metadata".format(self.top_key_name, self.separator)
        self.interface.metadata_listener.add_listener(self.metadata_key_name, self)
        self.pull_metadata = True

    def read_from_redis(self, path):
        """
        Return dictionary value of what was stored at the stated path
        :param path: path inside the json
        :return:
        """
        logger.info("GET {} {}".format(self.top_key_name, path))

        self.update_metadata()
        logger.debug("GET {} {} Metadata: {}".format(self.top_key_name, path, self.metadata))
        if path in self.sp_to_label:
            return self.pull_special_path(path)
        self.queue_reads(path)
        logger.debug("GET {} {} Reads Queued".format(self.top_key_name, path))
        return self.build_dictionary(path)

    def update_metadata(self):
        if self.pull_metadata:
            self.metadata = self.interface.client.jsonget(self.metadata_key_name, ".")
            self.sp_to_label = self.metadata["special_paths"]
        if self.metadata is None:
            return None
        self.pull_metadata = False

    def queue_reads(self, path):
        self.pipeline.jsonget(self.top_key_name, path)
        special_paths = filter_paths_by_prefix(self.sp_to_label.keys(), path)
        for path in special_paths:
            special_name = "{}{}".format(self.top_key_name, path)
            self.interface.label_to_shipper[self.sp_to_label[path]].read(special_name, self.pipeline_no_decode)

    def build_dictionary(self, path):
        if path == Path.rootPath():
            path = ""
        return_val = self.pipeline.execute()[0]
        logger.debug("GET {} {} Pipeline Executed".format(self.top_key_name, path))
        responses = self.pipeline_no_decode.execute()
        special_paths = filter_paths_by_prefix(self.sp_to_label.keys(), path)
        for i, sp in enumerate(special_paths):
            value = self.interface.label_to_shipper[self.sp_to_label[sp]].interpret_read(responses[i: i + 1])
            insertion_path = sp[len(path):]
            insert_into_dictionary(return_val, insertion_path, value)
        logger.debug("GET {} {} Dictionary Built".format(self.top_key_name, path))
        return return_val

    def pull_special_path(self, path):
        shipper = self.interface.label_to_shipper[self.sp_to_label[path]]
        special_name = "{}{}".format(self.top_key_name, path)
        shipper.read(special_name, self.pipeline_no_decode)
        responses = self.pipeline_no_decode.execute()
        return shipper.interpret_read(responses)


class KeyValueStore:
    def __init__(self, interface):
        self.interface = interface
        self.entries = {}

    def __setitem__(self, key, value):
        assert type(value) == dict, "Top level entries must be json"
        assert type(key) == str, "Key Names must be strings"
        self.ensure_key_existence(key)
        writer, reader = self.entries[key]
        writer.send_to_redis(Path.rootPath(), value)

    def __getitem__(self, item):
        assert type(item) == str
        logger.debug("KVS Get Item Accessed: {}".format(item))
        self.ensure_key_existence(item)
        writer, reader = self.entries[item]
        return ReadablePathHandler(writer=writer, reader=reader, initial_path=Path.rootPath())

    def ensure_key_existence(self, key):
        if not check_valid_key_name(key):
            raise ValueError("Invalid Key Name: {}".format(key))
        if key not in self.entries:
            self.entries[key] = (Writer(key, self.interface), Reader(key, self.interface))

    def track_schema_changes(self, set_value, keys=None):
        if keys is None:
            keys = self.entries.keys()
        for k in keys:
            self.entries[k][0].do_metadata_update = set_value


class Publisher(Writer):
    def __init__(self, top_key_name, interface):
        super().__init__(top_key_name, interface)
        self.message = "Publish"

    def send_to_redis(self, path, value):
        logger.info("PUBLISH {} {} = {}".format(self.top_key_name, path, value))
        self.process_metadata(path, value)
        self.publish_non_serializables(path, value)
        self.publish_serializables(path, value)

        # Addition to Writer class
        if path == Path.rootPath():
            path = ""
        channel_name = "__pubspace@0__:{}{}".format(self.top_key_name, path)
        self.pipeline.publish(channel_name, self.message)

        # Resume Writer Class
        self.pipeline.execute()


class PublishSpace(KeyValueStore):
    def __getitem__(self, item):
        assert type(item) == str
        self.ensure_key_existence(item)
        writer, reader = self.entries[item]
        return PathHandler(writer=writer, reader=reader, initial_path=Path.rootPath())

    def ensure_key_existence(self, key):
        if key not in self.entries:
            self.entries[key] = (Publisher(key, self.interface), None)


class PassiveSubscriber:
    def __init__(self, channel_name, interface, callback_function, kwargs):
        self.listening_channel = '__pubspace@0__:{}'.format(channel_name)
        self.listener = ChannelListener(interface, self.listening_channel, callback_function, kwargs)
        self.listener.setDaemon(True)

    def listen(self):
        self.listener.start()


class ActiveSubscriber(Reader):
    def __init__(self, top_key_name, interface):
        super().__init__(top_key_name, interface)
        self.local_copy = {}
        self.passive_subscriber = PassiveSubscriber(top_key_name + "*", interface, self.update_local_copy, {})
        self.prefix = "__pubspace@0__:{}".format(self.top_key_name)

    def update_local_copy(self, channel, message):
        logger.debug("Update Local Copy: Channel = {}, Prefix = {}, Message = {}".format(channel, self.prefix, message))
        try:
            message = message.decode("utf-8")
        except Exception as e:
            return
        if message != "Publish":
            return

        if channel == self.prefix:
            self.local_copy = self.read_from_redis(Path.rootPath())
            return
        path = channel[len(self.prefix):]

        redis_value = self.read_from_redis(path)
        logger.debug("Active Subscriber Read from Redis: {}".format(redis_value))
        insert_into_dictionary(self.local_copy, path, redis_value)

    def listen(self):
        self.passive_subscriber.listen()

    def value(self):
        return copy_dictionary_without_paths(self.local_copy, [])

    def __getitem__(self, item):
        assert type(item) == str, "Key name must be string"
        return ActiveSubscriberPathHandler(None, self, "{}{}".format(Path.rootPath(), item))