from synchrodt import SynchroDict
import rejson

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
    synchros_built['key0'] = "Trishul2"
    assert redisclient.get('key0') == b"Trishul2"
    print(synchros_built)

