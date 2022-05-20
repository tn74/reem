import redis

if redis.__version__ >= '4.0.0':
    from redis.commands.json.path import Path

    ROOT_PATH = Path.root_path()
    
    class RejsonCompat:
        """Patches a 4.x+ Redis instance to act like an old rejson.Client
        with jsonX methods.
        """
        def __init__(self,r):
            self._r = r
        def __getattr__(self,attr):
            if attr.startswith('json'):
                return getattr(self._r.json(),attr[4:])
            return getattr(self._r,attr)
        def pipeline(self):
            return RejsonCompat(self._r.pipeline())

    def make_redis_client(host='localhost',port=6379,db=0):
        """Return plain redis client + rejson client"""
        r = redis.Redis(host,port=port,db=db)
        j = RejsonCompat(redis.Redis(host,port=port,db=db))
        return r,j
else:
    #versions < 4.0.0 don't have rejson built in
    import rejson
    from rejson import Path

    ROOT_PATH = Path.rootPath()

    def make_redis_client(host='localhost',port=6379,db=0):
        """Return plain redis client + rejson client"""
        r = rejson.Client(host=host, port=port, db=db, decode_responses=False)
        j = rejson.Client(host=host, port=port, db=db, decode_responses=True)
        return r,j
