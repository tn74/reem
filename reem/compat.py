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
            if attr == "jsondel":
                return self._r.delete
            elif attr.startswith('json'):
                return getattr(self._r.json(),attr[4:])
            return getattr(self._r,attr)
        def __enter__(self):
            return self._r.__enter__()
        def __exit__(self, *args, **kwargs):
            return self._r.__exit__(*args, **kwargs)
        def pipeline(self):
            return RejsonCompat(self._r.pipeline())

    def make_redis_client(host='localhost',port=6379,db=0,*args,**kwargs):
        """Return plain redis client + rejson client"""
        r = redis.Redis(host,port=port,db=db,*args,**kwargs)
        j = RejsonCompat(redis.Redis(host,port=port,db=db,*args,**kwargs))
        return r,j
else:
    #versions < 4.0.0 don't have rejson built in
    import rejson
    from rejson import Path

    ROOT_PATH = Path.rootPath()

    def make_redis_client(host='localhost',port=6379,db=0,*args,**kwargs):
        """Return plain redis client + rejson client"""
        r = rejson.Client(host=host, port=port, db=db, decode_responses=False, *args, **kwargs)
        j = rejson.Client(host=host, port=port, db=db, decode_responses=True, *args, **kwargs)
        return r,j
