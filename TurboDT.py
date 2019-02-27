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
        excised_copy = self.make_excised_copy(list(map(lambda path: path.split(".")[1:], paths_to_update)), value)
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
        print("Set path: {}\nExtract Path: {}".format(set_path, extract_path))
        extract_path = extract_path[len(set_path):]        # Get rid of leading path so I can work inside value they set
        if extract_path == "":                             # Extraction path matches path they are setting - return val
            return set_value

        ret = set_value
        if "." in extract_path:
            dive_levels = extract_path.split(".")          # Need to go down keys to find object we desire
        else:
            dive_levels = [extract_path]                   # The object is in one of the direct keys of this dict

        print("Dive Levels: {}".format(dive_levels))
        dive_levels = list(filter(lambda key: key != "", dive_levels))      # Get rid of empty space surrounding .

        for k in dive_levels:
            ret = ret[k]

        return ret


class TReader:
    def __init__(self, top_key_name, special_case_handlers=[]):
        self.special_case_handlers = special_case_handlers
        self.top_key_name = top_key_name
        self.separator = "&&&&"
        self.external_mapped_paths = {}

    def read_from_redis(self, path):
        """
        Return dictionary value of what was stored at the stated path
        :param path: path inside the json
        :return:
        """

        if path in self.external_mapped_paths.keys():
            return self.external_mapped_paths[path].read(path)

        result = REDIS_CLIENT.get(self.top_key_name, path)
        if type(result) is str and self.separator in result:
            identifier = result.split(self.separator)[1]
            for handler in self.special_case_handlers:
                if handler.get_identifier() == identifier:
                    self.external_mapped_paths[result] = handler
                    return handler.read(path)
        return result


class MetadataListener(Thread):
    def __init__(self):
        super().__init__()


class TPublisher:
    pass


class TSubscriber:
    pass