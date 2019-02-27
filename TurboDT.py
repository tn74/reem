import rejson
from functools import reduce
from threading import Thread

REDIS_CLIENT = rejson.Client(host='localhost')
REDIS_PIPELINE = REDIS_CLIENT.pipeline()


class TWriter:
    def __init__(self, top_key_name, special_case_handlers=[]):
        self.special_case_handlers = special_case_handlers
        self.identifier_to_handler = {}
        self.top_key_name = top_key_name
        self.separator = "&&&&"
        self.metadata = {
            "special_paths": {},
            "required_handlers": [handler.get_identifier() for handler in self.special_case_handlers]
        }
        self.update_metadata_flag = False
        self.redis_client = REDIS_CLIENT
        self.pipeline = self.redis_client.pipeline()

        self.redis_client.jsonset("{}{}metadata".format(self.top_key_name, self.separator), ".", self.metadata)
        for sch in special_case_handlers:
            self.identifier_to_handler[sch.get_identifier()] = sch

    def send_to_redis(self, path, value):
        # Step 1 and 2: Take care of updating object metadata

        # Special case with root
        if path == ".":
            path = ""
        self.update_metadata_flag = False
        self.update_metadata(path, value)
        if self.update_metadata_flag:
            metadata_key_name = "{}{}metadata".format(self.top_key_name, self.separator)
            self.pipeline.jsonset(
                metadata_key_name,
                ".special_paths",
                self.metadata["special_paths"]
            )
            channel = "__keyspace@0__:{}".format(metadata_key_name)
            message = "set"
            self.pipeline.publish(channel, message)
            # print("Posted Metadata Update")
        if path == "":
            path = "."

        # Step 3: Push special objects to redis
        paths_to_update = list(filter(lambda special_path: path in special_path, self.metadata["special_paths"].keys()))
        for update_path in paths_to_update:
            special_name = "{}{}".format(self.top_key_name, update_path)
            self.identifier_to_handler[self.metadata["special_paths"][update_path]].write(
                key=special_name,
                value=self.extract_object(value, path, update_path),
                client=self.pipeline
            )

        # Step 4, 5: Excise special keys from dict and store
        if type(value) is dict:
            excised_copy = self.make_excised_copy(list(map(lambda path: path.split(".")[1:], paths_to_update)), value)
            # print("Excised Copy: {}".format(excised_copy))
            self.pipeline.jsonset(self.top_key_name, path, excised_copy)

        # Step 6: Execute all db commands
        self.pipeline.execute()

    def update_metadata(self, path, value):
        if type(value) is not dict:  # Not a dictionary so put this thing in redis
            # If this path is something we have seen, check if the current handler is correct
            if path in self.metadata["special_paths"].keys():
                if self.metadata["special_paths"][path].check_fit(value):
                    return

            # If it is not correctly set, find and set the correct one if it exists
            self.update_metadata_flag = True
            for sch in self.special_case_handlers:
                if sch.check_fit(value):
                    self.metadata["special_paths"][path] = sch.get_identifier()
                    print(self.metadata)
                    return

            # Return if no special case handlers assumed - assumed it works with json normally
            return

        else:  # Recurse finding if there are special paths to worry about
            if path in self.metadata["special_paths"].keys():
                self.metadata["special_paths"].pop(path)
            for k, v in value.items():
                self.update_metadata("{}.{}".format(path, k), v)

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

    def extract_object(self, set_value, set_path, extract_path):
        """
        Extract the object from within the dictionary they sent us while
        knowing what the path of the thing to extract is
        :param set_value: The dictionary being set currently
        :param set_path: Path
        :param extract_path:
        :return:
        """
        # print("Set path: {}\nExtract Path: {}".format(set_path, extract_path))
        extract_path = extract_path[len(set_path):]        # Get rid of leading path so I can work inside value they set
        if extract_path == "":                             # Extraction path matches path they are setting - return val
            return set_value

        ret = set_value
        if "." in extract_path:
            dive_levels = extract_path.split(".")          # Need to go down keys to find object we desire
        else:
            dive_levels = [extract_path]                   # The object is in one of the direct keys of this dict

        # print("Dive Levels: {}".format(dive_levels))
        dive_levels = list(filter(lambda key: key != "", dive_levels))      # Get rid of empty space surrounding .

        for k in dive_levels:
            ret = ret[k]

        return ret


class MetadataListener(Thread):
    def __init__(self):
        self.client = rejson.Client(host='localhost')
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
                # print("Read Channel: {}",format(channel))


# Keep as global so this robot component has only one subscriber looking to read things
READ_METADATA_LISTENER = MetadataListener()
READ_METADATA_LISTENER.setDaemon(True)
READ_METADATA_LISTENER.start()
READ_REDIS_CLIENT = rejson.Client(host='localhost', decode_responses=True)


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