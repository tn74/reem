from .helper_functions import *


class Writer:
    def __init__(self, top_key_name, interface):
        self.interface = interface
        self.top_key_name = top_key_name

        self.separator = "&&&&"
        self.metadata = {"special_paths": {}, "required_labels": self.interface.shipper_labels}
        self.sp_to_label = self.metadata["special_paths"]
        self.update_metadata_flag = False
        self.pipeline = self.interface.client.pipeline()

        self.metadata_key_name = "{}{}metadata".format(self.top_key_name, self.separator)
        self.interface.client.jsonset(self.metadata_key_name, Path.rootPath(), self.metadata)

    def send_to_redis(self, path, value):
        self.update_metadata(path, value)
        # print("Metadata: {}".format(self.metadata))
        self.publish_non_serializables(path, value)
        self.publish_serializables(path, value)
        self.pipeline.execute()

    def update_metadata(self, path, value):
        if path == Path.rootPath():
            path = ""
        self.update_metadata_flag = False
        self.update_special_paths(path, value)  # Update the local dictionary we have of special paths

        if self.update_metadata_flag:
            self.pipeline.jsonset(self.metadata_key_name, ".special_paths", self.sp_to_label)
            channel, message = "__keyspace@0__:{}".format(self.metadata_key_name), "set"
            self.pipeline.publish(channel, message)  # Homemade key-space notification for metadata updates

    def update_special_paths(self, path, value):
        if type(value) is not dict:  # Not a dictionary so put this thing in redis
            # If this path is something we have seen, check if the current handler is correct
            if path in self.sp_to_label.keys():
                if self.sp_to_label[path].check_fit(value):
                    return

            # If it is not correctly set, find and set the correct one if it exists
            self.update_metadata_flag = True
            for ship in self.interface.shippers:
                if ship.check_fit(value):
                    self.sp_to_label[path] = ship.get_label()
                    return

            # Return if no special case handlers assumed - assumed it works with json normally
            return

        else:  # Recurse finding if there are special paths to worry about
            if path in self.sp_to_label.keys():
                self.sp_to_label.pop(path)
                self.pipeline.delete("{}{}".format(self.top_key_name, path))
            for k, v in value.items():
                self.update_metadata("{}.{}".format(path, k), v)

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
            intrusive_paths = [p for p in self.sp_to_label.keys() if p[:len(path)] == path]
            intrusive_paths = [path_to_key_sequence(p[len(path) - 1:]) for p in intrusive_paths]
            excised_copy = copy_dictionary_without_paths(value, intrusive_paths)
            # print("Excised Copy: {}".format(excised_copy))
            self.pipeline.jsonset(self.top_key_name, path, excised_copy)
        elif path not in self.sp_to_label.keys():
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

        self.metadata_key_name = "{}{}metadata".format(self.top_key_name, self.separator)
        self.interface.metadata_listener.add_listener(self.metadata_key_name, self)
        self.pull_metadata = True

    def read_from_redis(self, path):
        """
        Return dictionary value of what was stored at the stated path
        :param path: path inside the json
        :return:
        """
        self.update_metadata(path)
        if path in self.sp_to_label:
            return self.handle_non_json_path(path)
        self.queue_reads(path)
        return self.build_dictionary(path)

    def update_metadata(self, path):
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
            self.interface.label_to_shipper[self.sp_to_label[path]].read(special_name, self.pipeline)

    def build_dictionary(self, path):
        responses = self.pipeline.execute()
        return_val = responses[0]
        special_paths = filter_paths_by_prefix(self.sp_to_label.keys(), path)
        for i, path in enumerate(special_paths):
            value = self.interface.label_to_shipper[self.sp_to_label[path]].interpret_read(responses[i + 1: i + 2])
            insert_into_dictionary(return_val, path, value)
        return return_val

    def handle_non_json_path(self, path):
        shipper = self.interface.label_to_shipper[self.sp_to_label[path]]
        special_name = "{}{}".format(self.top_key_name, path)
        shipper.read(special_name, self.pipeline)
        responses = self.pipeline.execute()
        return shipper.interpret_read(responses)


class TPublisher:
    pass


class TSubscriber:
    pass