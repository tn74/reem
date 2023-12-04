from __future__ import annotations
from .connection import RedisInterface,KeyValueStore
import weakref
import redis
import time
from typing import Union,Optional,Any

class TolerantKeyValueStore(KeyValueStore):
    """TolerantKeyValueStore acts almost like a normal KeyValueStore, except
    for the following advantages when using the :func:`var`, :func:`set`,
    and :func:`get` methods:
    
    - More tolerant of uninitialized keys and will fill in empty
      dicts as needed.
    - Can accept paths in the form of string paths ``['key1','key2']`` or
      period- separated keys ``'key1.key2'``

    .. note::

        Does not accept path strings that include integer array indices, yet.
        To access arrays, you will need to pass in arrays, e.g.
        ``['key1','key2',3]``

    There are also some performance enhancements when using :func:`var`:

    - If you are accessing a sub-key many times in success to obtain its
      sub-objects, storing a :func:`var` once and accessing its sub-keys is
      much faster because it will cache the object and avoid making many
      calls to the server.
    - If you are accessing a sub-key of a large object, use
      ``var(path_to_item)`` rather than ``var(key1)[key2][...]``. The latter
      will retrieve the whole object referenced by key1.
    - You may play around with the cache refresh time with the second
      argument to :func:`var` or with the attribute ``defaultVarRefreshRate``.
      If you have a slow item that only updates
      occasionally, e.g., by user input, set a larger refresh, e.g.
      ``var(path,2)`` will make at most one query to the server per 2 seconds.

    """
    def __init__(self,
                 interface: Union[str,RedisInterface,KeyValueStore]='localhost',
                 refreshRate : float=0,
                 *args,
                 **kwargs):
        KeyValueStore.__init__(self,interface,*args,**kwargs)
        self.defaultVarRefreshRate = refreshRate

    def var(self,
            path : Union[str,list],
            refreshRate : Optional[float]=None) -> TolerantKVSVar:
        """Given a path (period-separated str or list of str), returns a
        :class:`TolerantKVSVar` object that accesses the key using get()/set().

        All parent keys in path will be created as empty dictionaries
        if they don't exist.

        If refreshRate!=0, values will be cached, only refreshing after
        refreshRate seconds elapse.  This minimizes server traffic.
        """
        return TolerantKVSVar(self,path,(refreshRate if refreshRate is not None else self.defaultVarRefreshRate))

    def get(self,
            path : Union[str,list]) -> Any:
        """Given a path (period-separated str or list of str), returns a JSON
        object or numpy array at path by recursively descending into self.
        """
        return TolerantKVSVar(self,path).get()

    def set(self,
            path : Union[str,list], value : Any):
        """Given a path (period-separated str or list of str), sets a value in
        the state server.  The item must be json-encodable or a numpy array.

        If you are accessing a path with multiple subkeys that don't
        exist, the subkeys will be added.
        """
        return TolerantKVSVar(self,path).set(value)


class TolerantKVSVar:
    """An accessor for a TolerantKeyValueStore.  Can be more convenient than accessing
    the server via ``server[key].read() / write()`` because it will create
    parent keys from a period-separated path, and can be more efficient on
    reads due to caching and pre-creation of path strings.

    Supports operators [], del [], type(), len(), +=, -=, *=, /=, and append().
    """
    def __init__(self, server : TolerantKeyValueStore, path : Union[str,list], refreshRate : float=0):
        self.server = weakref.proxy(server)
        if isinstance(path,str):
            path = path.split('.')
        else:
            assert isinstance(path,(list,tuple))
            assert len(path) > 0
        self.path = path
        res = server
        for p in path:
            res = res[p]
        self.node = res
        self.refreshRate = refreshRate
        self.cachedTime = 0
        self.cachedValue = None
        self.cacheWrites = 0
        self.cacheHits = 0
        self.cacheMisses = 0

    def _ensureKeys(self):
        res = KeyValueStore.__getitem__(self.server,self.path[0])
        try:
            res.type()
        except Exception:
            if isinstance(self.path[0],int):
                raise KeyError("Invalid Redis index into array {}".format(self.path))
            self.server.set(self.path[0],{})

        for p in self.path[1:-1]:
            prev = res
            res = res[p]
            try:
                res.type()
            except Exception:
                if isinstance(p,int):
                    raise KeyError("Invalid Redis index into array {}".format(self.path))
                #key doesn't exist
                try:
                    prev.write({p:dict()})
                except ValueError:
                    print("Uh... didn't successfully write keys in",self.path,"up to",p)
                    raise
                except redis.exceptions.ResponseError:
                    print("Uh... didn't successfully write keys in",self.path,"up to",p)
                    raise
                res = prev[p]

    def _rawRead(self):
        try:
            return self.node.read()
        except ValueError:
            pass
        except redis.exceptions.ResponseError:
            pass
        raise KeyError("Redis path %s does not exist"%('.'.join(str(v) for v in self.path)))

    def _rawWrite(self,value):
        try:
            return self.node.write(value)
        except ValueError:
            pass
        except redis.exceptions.ResponseError:
            pass
        self._ensureKeys()
        return self.node.write(value)

    def _cachedRead(self,func):
        t = time.time()
        if self.cachedValue is not None and t < self.cachedTime + self.refreshRate:
            self.cacheHits += 1
            return func(self.cachedValue)
        self.cachedValue = self._rawRead()
        self.cachedTime = t
        self.cacheMisses += 1
        return func(self.cachedValue)

    def get(self):
        """Reads the value at the given key from the state server"""
        if self.refreshRate:
            return self._cachedRead(lambda x:x)
        else:
            return self._rawRead()

    def set(self,value):
        """Sets the value at the given key into the state server.
        """
        if self.refreshRate:
            self.cachedValue = value
            self.cachedTime = time.time()
            self.cacheWrites += 1
        self._rawWrite(value)

    def __getitem__(self,key):
        return TolerantKVSVarSubkey(self,self,key)

    def __setitem__(self,key,value):
        return TolerantKVSVarSubkey(self,self,key).set(value)

    def __delitem__(self,key):
        del self.node[key]
        if self.cachedValue is not None:
            try:
                del self.cachedValue[key]
            except KeyError:
                pass

    def __str__(self):
        return '.'.join(str(v) for v in self.path)+'='+str(self.get())

    def type(self):
        if self.refreshRate:
            return self._cachedRead(lambda x:x.__class__)
        else:
            return self.node.type()

    def __len__(self):
        if self.refreshRate:
            return self._cachedRead(lambda x:len(x))
        else:
            return len(self.node)

    def __iadd__(self,rhs):
        if self.refreshRate:
            self.cachedValue += rhs
            self.cachedTime = time.time()
            self.cacheWrites += 1
        self.node += rhs
        return self

    def __isub__(self,rhs):
        if self.refreshRate:
            self.cachedValue -= rhs
            self.cachedTime = time.time()
            self.cacheWrites += 1
        self.node -= rhs
        return self

    def __imul__(self,rhs):
        if self.refreshRate:
            self.cachedValue *= rhs
            self.cachedTime = time.time()
            self.cacheWrites += 1
        self.node *= rhs
        return self

    def __idiv__(self,rhs):
        if self.refreshRate:
            self.cachedValue /= rhs
            self.cachedTime = time.time()
            self.cacheWrites += 1
        self.node /= rhs
        return self

    def append(self,rhs):
        if self.refreshRate:
            self.cachedValue.append(rhs)
            self.cachedTime = time.time()
            self.cacheWrites += 1
        self.node.append(rhs)


class TolerantKVSVarSubkey:
    """Accessor for sub-keys of TolerantKVSVar's.  Respects cache, and
    refreshes the cache of the original object referenced by var().

    Performs copy-on-write semantics.

    Supports operators [], del [], type(), len(), +=, -=, *=, /=, and append().
    """
    def __init__(self,root : TolerantKVSVar, parentnode, key : str):
        self.root = root
        self.parent = parentnode
        self.key = key
        if isinstance(self.parent,TolerantKVSVar):
            self.path = [key]
            self.node = self.parent.node[key]
        else:
            self.path = self.parent.path + [key]
            self.node = self.parent.node[key]

    def get(self):
        val = self.root.get()
        for k in self.path:
            val = val[k]
        return val

    def _setCachedValue(self,value):
        if self.root.cachedValue is None: return None
        t = time.time()
        if t >= self.root.cachedTime + self.root.refreshRate: return None
        cachedParent = None
        cachedValue = self.root.cachedValue
        for k in self.path:
            cachedParent = cachedValue
            if k not in cachedValue:
                cachedValue[k] = {}
            cachedValue = cachedValue[k]
        assert cachedParent is not None
        cachedParent[self.key] = value

    def _getCachedValue(self):
        if self.root.cachedValue is None: return None
        t = time.time()
        if t >= self.root.cachedTime + self.root.refreshRate: return None
        cachedValue = self.root.cachedValue
        for k in self.path:
            cachedValue = cachedValue[k]
        self.root.cacheWrites += 1
        self.root.cachedTime = t
        return cachedValue

    def set(self,value):
        if isinstance(value,(TolerantKVSVar,TolerantKVSVarSubkey)):
            if value is self:  #this happens with incremental add/sub/mul/div operators
                return
            value = value.get()
        try:
            self.node.write(value)
        except ValueError:
            #create nodes up to this one
            self.parent.set({})
            self.node.write(value)
        except redis.exceptions.ResponseError:
            #create nodes up to this one
            self.parent.set({})
            self.node.write(value)
        if self._setCachedValue(value) is None:
            self.root.cacheWrites += 1

    def __getitem__(self,key) -> 'TolerantKVSVarSubkey':
        return TolerantKVSVarSubkey(self.root,self,key)
    def __setitem__(self,key,value):
        TolerantKVSVarSubkey(self.root,self,key).set(value)
    def __delitem__(self,key):
        del self.node[key]
        cv = self._getCachedValue()
        if cv is not None:
            del cv[key]

    def __str__(self):
        return '.'.join(str(v) for v in self.path)+'='+str(self.get())
    def type(self):
        return self.get().__class__
    def __len__(self):
        return len(self.get())

    def __iadd__(self,rhs):
        self.node += rhs
        cv = self._getCachedValue()
        if cv is not None:
            cv += rhs
        return self

    def __isub__(self,rhs):
        self.node -= rhs
        cv = self._getCachedValue()
        if cv is not None:
            cv -= rhs
        return self

    def __imul__(self,rhs):
        self.node *= rhs
        cv = self._getCachedValue()
        if cv is not None:
            cv *= rhs
        return self

    def __idiv__(self,rhs):
        self.node /= rhs
        cv = self._getCachedValue()
        if cv is not None:
            cv /= rhs
        return self

    def append(self,rhs):
        self.node.append(rhs)
        cv = self._getCachedValue()
        if cv is not None:
            cv.append(rhs)
