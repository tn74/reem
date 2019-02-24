import rejson
from functools import reduce

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
            "required_handlers": [handler.get_identifier for handler in self.special_case_handlers]
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
            self.pipeline.jsonset(
                ".{}{}metadata".format(self.top_key_name, self.separator),
                ".special_paths",
                self.metadata["special_paths"]
            )

        # Step 3: Push special objects to redis
        paths_to_update = list(filter(lambda special_path: path in special_path, self.metadata["special_paths"].keys()))
        for path in paths_to_update:
            special_name = "{}.{}".format(self.top_key_name, path)
            self.identifier_to_handler[self.metadata["special_paths"][path]].write(
                key=special_name,
                value=value,
                client=self.pipeline
            )

        # Step 4, 5: Excise special keys from dict and store
        excised_copy = self.make_excised_copy(list(map(lambda path: path.split("."), paths_to_update)), value)
        self.pipeline.jsonset(self.top_key_name, path, excised_copy)

    def update_metadata(self, path, value):

        if type(value) is not dict:  # Not a dictionary so put this thing in redis
            # If this path is something we have seen, check if the current handler is correct
            if path in self.metadata["special_paths"].keys():
                if self.metadata["special_paths"][path].check_fit(value):
                    return

            # If it is not correctly set it, do it if handler exists
            self.update_metadata_flag = True
            for sch in self.special_case_handlers:
                if sch.check_fit(value):
                    self.metadata["special_paths"][path] = sch.get_identifier()
                    return

            # Return if no special case handlers assumed - assumed it works with json normally
            return

        else:  # Recurse finding if there are special paths to worry about
            for k, v in value.items():
                self.update_metadata("{}.{}".format(path, k), v)

    def make_excised_copy(self, paths, dictionary):
        ret = {}
        possibles = filter(lambda l: len(l) == 1, paths)
        possibles = reduce(lambda x, y: x + y, possibles)
        for k, v in dictionary.items():
            if k in possibles:
                continue
            if type(v) == dict:
                ret[k] = self.make_excised_copy(paths[:, 1:], v)
            else:
                ret[k] = v
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


class TPublisher:
    pass


class TSubscriber:
    pass