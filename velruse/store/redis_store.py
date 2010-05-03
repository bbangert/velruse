"""Redis UserStore implementation"""
try:
    import cPickle as pickle
except ImportError:
    import pickle

import redis
from redis.exceptions import RedisError

from velruse.store.interface import UserStore
from velruse.utils import cached_property

class RedisStorage(UserStore):
    """Redis Storage for Auth Provider"""
    def __init__(self, host='localhost', port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
    
    @cached_property
    def _conn(self):
        """The Redis connection, cached for this call"""
        return redis.Redis(host=self.host, port=self.port, db=self.db)
    
    def retrieve(self, key):
        data = self._conn.get(key)
        if data:
            return pickle.loads(data)
        else:
            return None
    
    def store(self, key, value, expires=None):
        try:
            self._conn.set(key, pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
            if expires:
                self._conn.expire(key, expires)
        except RedisError:
            return False
        else:
            return True
