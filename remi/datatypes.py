from functools import reduce
from rejson import Path


class TWriter:
    def __init__(self, top_key_name, interface):
        self.interface = interface
        self.top_key_name = top_key_name

        self.separator = "&&&&"
        self.metadata = {"special_paths": {}, "required_labels": self.interface.shipper_labels}
        self.update_metadata_flag = False
        self.pipeline = self.interface.client.pipeline()

        self.metadata_key_name = "{}{}metadata".format(self.top_key_name, self.separator)
        self.interface.client.jsonset(self.metadata_key_name, Path.rootPath(), self.metadata)

    def send_to_redis(self, path, value):
        self.update_metadata(path, value)
        self.publish_non_serializables(path, value)
        self.publish_serializables(path, value)
        self.pipeline.execute()

    def get_key_sequence(self, path):
        if path == Path.rootPath():
            return []
        return path.split(".")[1:]

    def update_metadata(self, path, value):
        self.update_metadata_flag = False
        self.update_special_paths(path, value)  # Update the local dictionary we have of special paths

        if self.update_metadata_flag:
            self.pipeline.jsonset(self.metadata_key_name, ".special_paths", self.metadata["special_paths"])
            channel, message = "__keyspace@0__:{}".format(self.metadata_key_name), "set"
            self.pipeline.publish(channel, message)  # Homemade key-space notification for metadata updates

    def update_special_paths(self, path, value):
        if type(value) is not dict:  # Not a dictionary so put this thing in redis
            # If this path is something we have seen, check if the current handler is correct
            if path in self.metadata["special_paths"].keys():
                if self.metadata["special_paths"][path].check_fit(value):
                    return

            # If it is not correctly set, find and set the correct one if it exists
            self.update_metadata_flag = True
            for ship in self.interface.shippers:
                if ship.check_fit(value):
                    self.metadata["special_paths"][path] = ship.get_label()
                    return

            # Return if no special case handlers assumed - assumed it works with json normally
            return

        else:  # Recurse finding if there are special paths to worry about
            if path in self.metadata["special_paths"].keys():
                self.metadata["special_paths"].pop(path)
                self.pipeline.delete("{}{}".format(self.top_key_name, path))
            for k, v in value.items():
                self.update_metadata("{}.{}".format(path, k), v)

    def publish_non_serializables(self, path, value):
        publish_paths = list(filter(lambda special_path: path == special_path[:len(path)], self.metadata["special_paths"].keys()))

        for update_path in publish_paths:
            special_name = "{}{}".format(self.top_key_name, update_path)
            self.interface.label_to_shipper[self.metadata["special_paths"][update_path]].write(
                key=special_name,
                value=self.extract_object(value, path, update_path),
                client=self.pipeline
            )
    def extract_object(self, value, set_path, update_path):
        key_accesses = update_path[len(set_path):]
        


    def publish_serializables(self, path, value):
        pass

    def make_excised_copy(self, paths, dictionary):
        ret = {}
        possibles = list(filter(lambda l: len(l) == 1, paths))
        possibles = reduce(lambda x, y: x + y, possibles, [])
        for k, v in dictionary.items():
            if k in possibles:
                continue
            if type(v) == dict:
                ret[k] = self.make_excised_copy(list(map(lambda p: p[1:], paths)), v)
            else:
                ret[k] = v
        return ret


class TReader:
    def __init__(self, top_key_name, special_case_handlers=[]):
        self.special_case_handlers = special_case_handlers
        self.top_key_name = top_key_name
        self.separator = "&&&&"
        self.metadata = None
        self.pull_metadata = True
        self.client = READ_REDIS_CLIENT
        self.pipeline = self.client.pipeline()
        self.metadata_name = "{}{}metadata".format(self.top_key_name, self.separator)

        self.identifier_to_handler = {}
        for sch in special_case_handlers:
            self.identifier_to_handler[sch.get_identifier()] = sch

        READ_METADATA_LISTENER.add_listener(self.metadata_name, self)

    def read_from_redis(self, path):
        """
        Return dictionary value of what was stored at the stated path
        :param path: path inside the json
        :return:
        """
        # Step 1: Pull Metadata if I need to
        if self.pull_metadata:
            self.metadata = self.client.jsonget(self.metadata_name, ".")
        if self.metadata is None:
            return None
        self.pull_metadata = False

        if path in self.metadata["special_paths"]:
            return self.handle_non_json_path(path)

        # Step 2: Pull the overarching JSON
        self.pipeline.jsonget(self.top_key_name, path)

        # Step 3: Get objects inside each of the special paths
        special_path_tuples = self.metadata["special_paths"].items()
        for path, identifier in special_path_tuples:
            special_name = "{}{}".format(self.top_key_name, path)
            self.identifier_to_handler[identifier].read(special_name, self.pipeline)

        # Step 4: Gather redis responses into a local data structure
        responses = self.pipeline.execute()
        return_val = responses[0]
        special_object_map = {}
        for i, tup in enumerate(special_path_tuples):
            special_object_map[tup[0]] = self.identifier_to_handler[identifier].interpret_read([responses[i+1]])

        # Step 5: Insert special keys into dictionary
        self.insertion(return_val, special_object_map)
        return return_val

    def insertion(self, primary_dictionary, path_obj_map):
        for path, obj in path_obj_map.items():
            key_trail = path.split(".")[1:]
            containing_dict = primary_dictionary
            for k in key_trail[:-1]:
                containing_dict = primary_dictionary[k]

            containing_dict[key_trail[-1]] = obj

    def handle_non_json_path(self, path):
        # print(self.metadata)
        handler = self.identifier_to_handler[self.metadata["special_paths"][path]]
        special_name = "{}{}".format(self.top_key_name, path)
        handler.read(special_name, self.pipeline)
        responses = self.pipeline.execute()
        return handler.interpret_read(responses)

class TPublisher:
    pass


class TSubscriber:
    pass