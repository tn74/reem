from rejson import Path
from functools import reduce
from typing import List, Dict, Iterable
import json
import logging

logger = logging.getLogger("reem")

SEPARATOR_CHARACTER = "&&&&"
ROOT_VALUE_SEQUENCE = "%%%%"


def append_to_path(existing, addition):
    """
    Append an key to an existing subpath
    :param existing: a subpath string
    :param addition: a new key in the subpath
    :return: a path string
    :rtype: str
    """
    if existing == Path.rootPath():
        return Path.rootPath() + addition
    return "{}.{}".format(existing, addition)


def path_to_key_sequence(path: str):
    """
    Turn a ReJSON subpath string into a sequence of key accesses
    :param path: a path string of form: ".", ".subkey1.subkey2"
    :return: list of key accesses below a top level key in redis
    :rtype: List[str]
    """
    if path == Path.rootPath():
        return []
    return path.split(".")[1:]


def key_sequence_to_path(sequence: List[str]):
    """
    Convert a sequence of key accesses into a path string representing a path below the top level key in redis
    :param sequence: list of strings representing key accesses
    :return: a subpath string
    """
    return Path.rootPath() + ".".join(sequence)


def copy_dictionary_without_paths(dictionary: Dict, key_sequence: List[List[str]]):
    """
    Return a copy of dictionary with the paths formed by key_sequences removed
    :param key_sequence: 2D List of Strings where each internal list is a sequence of key accesses from dictionary root
    :param dictionary: The dictionary to copy
    :return: dictionary with paths represented by lists inside key_sequences removed
    :rtype: dict
    """
    ret = {}
    possibles = [ks for ks in key_sequence if len(ks) == 1]
    possibles = set(reduce(lambda x, y: x + y, possibles, []))
    for k, v in dictionary.items():
        if k in possibles:
            continue
        if type(v) == dict:
            ret[k] = copy_dictionary_without_paths(v, [ks[1:] for ks in key_sequence if len(ks) > 1])
        else:
            ret[k] = v
    return ret


def extract_object(dictionary: Dict, key_sequence: List[str]):
    """
    Extract the object inside the dictionary at a specific path
    :param dictionary: dictionary to extract from
    :param key_sequence: list of strings represetning key accesses
    :return: the value inside dictionary specified by key_sequence
    """
    ret = dictionary
    for k in key_sequence:
        ret = ret[k]
    return ret


def filter_paths_by_prefix(paths: Iterable[str], prefix: str):
    """
    Given a list of paths and a prefix, return the paths that
    :param paths: list of paths
    :param prefix: prefix to filter on
    :return: list of paths that begin with the specified prefix and the subsequent paths after the prefix
    :rtype: List[str], List[str]
    """
    if prefix == Path.rootPath():
        return paths, paths
    full_paths, suffixes = [], []
    for p in paths:
        if p.startswith(prefix):
            suffixes.append(p[len(prefix):])
            full_paths.append(p)
    return full_paths, suffixes


def insert_into_dictionary(dictionary: Dict, key_sequence: List[str], value):
    """
    Insert value into dictionary at path specified by key_sequence. If the sequence of keys does not exist, it will be made
    :param dictionary: dictionary to insert into
    :param key_sequence: specify the path inside the dictionary
    :param value: value to insert
    :return: None - the method will modify dictionary
    :rtype: None
    """
    parent = dictionary
    for key in key_sequence[:-1]:
        if key not in parent.keys():
            parent[key] = {}
        parent = parent[key]
    parent[key_sequence[-1]] = value


def get_special_paths(set_path: str, set_value, sp_to_label: Dict, label_to_ship: Dict):
    """
    Get info on how to update sp_to_label according to the user uploading `set_value` in location `set_path`
    :param set_path: ".key0.key1" subpath
    :param set_value: anything to be inserted into data. Needs to uploadable to redis
    :param sp_to_label: dictionary mapping current special paths to their ships
    :param label_to_ship: dictionary mapping ship labels to ship objects
    :return: A set of tuples: (path, corresponding ship's label)
    :rtype: set
    """
    additions = set()
    if type(set_value) is not dict:
        # If this path is already labelled as special, then check that the ship matched with it does fit
        if set_path in sp_to_label:
            if label_to_ship[sp_to_label[set_path]].check_fit(set_value):
                return additions

        # If this is something a ship covers, add it as a special path
        for ship in label_to_ship.values():
            if ship.check_fit(set_value):
                additions.add( (set_path, ship.get_label()) )

    # If this is a dict, recursively build the set of additional paths
    else:
        for k, v in set_value.items():
            assert check_valid_key_name(k), "Invalid Key: {}".format(k)
            if set_path != Path.rootPath():
                child_path = "{}.{}".format(set_path, k)
            else:
                child_path = ".{}".format(k)
            child_add = get_special_paths(child_path, v, sp_to_label, label_to_ship)
            additions = additions.union(child_add)

    return additions


def check_valid_key_name(name):
    """
    Ensure the key name provided is legal
    :param name: a potential key name
    :return: boolean indicating legality of name
    :rtype: bool
    """
    if type(name) not in [str]:
        return False
    bad_chars = ["*", ".", "&&&&"]
    for k in bad_chars:
        if k in name:
            return False
    return True