from synchrodt import SynchroDict
import rejson
import datetime
import time

redisclient = rejson.Client()

def test_simple_schema():
    schema = {
        'key0': str,
    }
    synchros_built = SynchroDict.build_from_schema(schema, 'test_simple_schema')
    assert "{\'key0\': None}" == str(synchros_built)


def test_nested_schema():
    schema = {
        'key0': str,
        'key1': {
            'nested_key_1': str,
            'nested_key_2': str,
        },
    }
    synchros_built = SynchroDict.build_from_schema(schema, 'test_nested_schema')
    print(synchros_built)


def test_wrong_type_set():
    schema = {
        'key0': str,
    }
    synchros_built = SynchroDict.build_from_schema(schema, 'test_wrong_type_set')
    try:
        synchros_built['key0'] = {}
        assert False
    except ValueError as e:
        print(e)
        print("Rejected setting wrong type")
    print(synchros_built)


def test_simple_string_put():
    schema = {
        'key0': str,
    }
    synchros_built = SynchroDict.build_from_schema(schema, 'test_simple_schema')
    input_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    synchros_built['key0'] = input_string
    synchros_built["key1"]
    time.sleep(0.1)
    assert redisclient.get('test_simple_schema::key0@@@class<"str">) == bytes(input_string,'utf-8')
    print(synchros_built)

