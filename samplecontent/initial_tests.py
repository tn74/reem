from rejson import Client, Path

rj = Client(host='localhost', port=6379, decode_responses=True)

# Set the key `obj` to some object
obj = {
    'answer': 42,
    'arr': [None, True, 3.14],
    'truth': {
        'coord': 'out there'
    }
}
rj.jsonset('obj', Path.rootPath(), obj)

print ('Is there anybody... {}?'.format(rj.jsonget('obj', Path.rootPath())))