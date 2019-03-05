from rejson import Path
from functools import reduce
from typing import List, Set, Dict

def path_to_key_sequence(path: str):
    if path == Path.rootPath():
        return []
    return path.split(".")[1:]


def key_sequence_to_path(sequence: List[str]):
    return Path.rootPath() + ".".join(sequence)


def copy_dictionary_without_paths(dictionary: Dict, key_sequences: List[List[str]]):
    """
    Return a copy of dictionary with the paths formed by key_sequences removed
    :param key_sequences: 2D List of Strings where each internal list is a sequence of key accesses from dictionary root
    :param dictionary: The dictionary to copy
    :return: dict
    """
    ret = {}
    possibles = [ks for ks in key_sequences if len(ks) == 1]
    possibles = set(reduce(lambda x, y: x + y, possibles, []))
    for k, v in dictionary.items():
        if k in possibles:
            continue
        if type(v) == dict:
            ret[k] = copy_dictionary_without_paths(v, [ks[1:] for ks in key_sequences if len(ks) > 1])
        else:
            ret[k] = v
    return ret


def extract_object(dictionary: Dict, key_sequence: List[str]):
    ret = dictionary
    for k in key_sequence:
        ret = ret[k]
    return ret


def filter_paths_by_prefix(all_paths: set[str], prefix: str):
    return [path for path in all_paths if path[:len(prefix)] == prefix]


def insert_into_dictionary(dictionary: dict, path: str, value):
    key_sequence = path_to_key_sequence(path)
    parent = dictionary
    for key in key_sequence[:-1]:
        if key not in parent.keys():
            parent[key] = {}
        parent = parent[key]
    parent[key_sequence[-1]] = value


def get_updates_for_special_paths(set_path: str, set_value, sp_to_label: Dict, label_to_ship: Dict[]):
    """
    Get info on how to update sp_to_label according to the user uploading `set_value` in location `set_path`
    :param set_path: ".key1.key0" kind of string indicating path within parent that set_value is supposed to be set
    :param set_value: anything to be inserted into data. Needs to be able to be sent to redis or a dict
    :param sp_to_label: dictionary we are going to be updating
    :param label_to_ship: dictionary giving the ship corresponding to a certain label
    :return: set( tuple(str:paths added, str:labels added) ), set( str:paths removed )
    """

    additions, deletions = set(), set()
    if type(set_value) is not dict:
        if set_path in sp_to_label.keys():
            if label_to_ship[sp_to_label[set_path]].check_fit(set_value):
                return additions, deletions

        # If this is something a ship covers, add it as a special path
        for ship in label_to_ship.values():
            if ship.check_fit(set_value):
                additions.add( (set_path, ship.get_label()) )

    else:
        if set_path in sp_to_label.keys():
            deletions.add ( set_path )
        for k, v in set_value.items():
            child_path = "{}.{}".format(set_path, k)
            child_add, child_del = get_updates_for_special_path_to_label(child_path, v, sp_to_label, label_to_ship)
            additions = additions.union(child_add)
            deletions = deletions.union(child_del)

    return additions, deletions