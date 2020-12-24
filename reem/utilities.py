from __future__ import print_function

from rejson import Path
from functools import reduce
import json
import logging
from six import itervalues,iteritems
import sys

logger = logging.getLogger("reem")

SEPARATOR_CHARACTER = "&&&&"
ROOT_VALUE_SEQUENCE = "%%%%"

ROOT_PATH = Path.rootPath()


def path_to_key_sequence(path):
    """
    Turn a ReJSON subpath string into a sequence of key accesses
    :param path (str): a path string of form: ".", ".subkey1.subkey2"
    :return: list of key accesses below a top level key in redis
    :rtype: List[str]
    """
    if path == ROOT_PATH:
        return []
    return path.split(".")[1:]

def key_sequence_to_path(sequence):
    """
    Convert a sequence of key accesses into a path string representing a path below the top level key in redis
    :param sequence (List[str]): list of strings representing key accesses
    :return: a subpath string
    """
    return ROOT_PATH + ".".join(sequence)

def key_sequence_to_path_ext(sequence):
    """
    Convert a sequence of key accesses or array accesses into a path string representing a path below the top level key in redis
    :param sequence (List[str or int]): list of strings representing key accesses or indices representing array accesses
    :return: a subpath string
    """
    if len(sequence) == 0:
        return ROOT_PATH
    #if isinstance(sequence[0],int):
    #    raise ValueError("Top-level key cannot be an integer")
    seps_keys = []
    for k in sequence:
        if isinstance(k,int):
            seps_keys.append('[%d]'%(k,))
        else:
            seps_keys.append('.')
            seps_keys.append(k)
    return ''.join(seps_keys)


def copy_dictionary_without_paths(dictionary, key_sequence):
    """
    Return a copy of dictionary with the paths formed by key_sequences removed
    :param dictionary (Dict): The dictionary to copy
    :param key_sequence (List[List[str]]): 2D List of Strings where each internal list is a sequence of key accesses from dictionary root
    :return: dictionary with paths represented by lists inside key_sequences removed
    :rtype: dict
    """
    ret = {}
    possibles = [ks for ks in key_sequence if len(ks) == 1]
    possibles = set(reduce(lambda x, y: x + y, possibles, []))
    for k, v in iteritems(dictionary):
        if k in possibles:
            continue
        if type(v) == dict:
            ret[k] = copy_dictionary_without_paths(v, [ks[1:] for ks in key_sequence if len(ks) > 1])
        else:
            ret[k] = v
    return ret


def extract_object(dictionary, key_sequence):
    """
    Extract the object inside the dictionary at a specific path
    :param dictionary (Dict): dictionary to extract from
    :param key_sequence (List[str]): list of strings represetning key accesses
    :return: the value inside dictionary specified by key_sequence
    """
    ret = dictionary
    for k in key_sequence:
        ret = ret[k]
    return ret


def filter_paths_by_prefix(paths, prefix):
    """
    Given a list of paths and a prefix, return the paths that start with prefix.
    :param paths (Iterable[str]): list of paths
    :param prefix (str): prefix to filter on
    :return: list of paths that begin with the specified prefix and the subsequent paths after the prefix
    :rtype: List[str], List[str]
    """
    if prefix == ROOT_PATH:
        paths = list(paths)
        return paths, paths
    full_paths, suffixes = [], []
    for p in paths:
        if p.startswith(prefix):
            suffixes.append(p[len(prefix):])
            full_paths.append(p)
    return full_paths, suffixes


def insert_into_dictionary(dictionary, key_sequence, value):
    """
    Insert value into dictionary at path specified by key_sequence. If the sequence of keys does not exist, it will be made
    :param dictionary (Dict): dictionary to insert into
    :param key_sequence (List[str]): specify the path inside the dictionary
    :param value: value to insert
    :return: None - the method will modify dictionary
    :rtype: None
    """
    parent = dictionary
    for key in key_sequence[:-1]:
        parent = parent.setdefault(key,{})
    parent[key_sequence[-1]] = value


def get_special_paths(set_path, set_value, sp_to_label, label_to_ship):
    """
    Get info on how to update sp_to_label according to the user uploading `set_value` in location `set_path`
    :param set_path (str): ".key0.key1" subpath
    :param set_value: anything to be inserted into data. Needs to uploadable to redis
    :param sp_to_label (Dict): dictionary mapping current special paths to their ships
    :param label_to_ship (Dict): dictionary mapping ship labels to ship objects
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
        for ship in itervalues(label_to_ship):
            if ship.check_fit(set_value):
                additions.add( (set_path, ship.get_label()) )

    # If this is a dict, recursively build the set of additional paths
    else:
        for k, v in iteritems(set_value):
            assert check_valid_key_name(k), "Invalid Key: {}".format(k)
            if set_path != ROOT_PATH:
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
    if not isinstance(name,str):
        return False
    bad_chars = ["*", ".", "&&&&"]
    if any(k in name for k in bad_chars):
        return False
    return True

def check_valid_key_name_ext(name):
    """
    Ensure the key / index name provided is legal
    :param name: a potential key name or index
    :return: boolean indicating legality of name
    :rtype: bool
    """
    if isinstance(name,int):
        return True
    if not isinstance(name,str):
        return False
    bad_chars = ["*", ".", "&&&&"]
    if any(k in name for k in bad_chars):
        return False
    return True

if sys.version_info[0] < 3:
    def json_recode_str(input):
        if isinstance(input, dict):
            return {json_recode_str(key): json_recode_str(value)
                    for key, value in input.iteritems()}
        elif isinstance(input, list):
            return [json_recode_str(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input
else:
    def json_recode_str(input):
        return input