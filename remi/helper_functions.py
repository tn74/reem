from rejson import Path
from functools import reduce


def path_to_key_sequence(path):
    if path == Path.rootPath():
        return []
    return path.split(".")[1:]


def key_sequence_to_path(sequence):
    return Path.rootPath() + ".".join(sequence)


def copy_dictionary_without_paths(dictionary, key_sequences):
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


def extract_object(dictionary, key_sequence):
    ret = dictionary
    for k in key_sequence:
        ret = ret[k]
    return ret


def filter_paths_by_prefix(all_paths, prefix):
    return [path for path in all_paths if path[:len(prefix)] == prefix]


def insert_into_dictionary(dictionary, path, value):
    key_sequence = path_to_key_sequence(path)
    parent = dictionary
    for key in key_sequence[:-1]:
        if key not in parent.keys():
            parent[key] = {}
        parent = parent[key]
    parent[key_sequence[-1]] = value