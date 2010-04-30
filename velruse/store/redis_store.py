"""Redis UserStore implementation"""
import redis
from redis.exceptions import RedisError

from velruse.store.interface import UserStore
from velruse.utils import cached_property
from velruse.utils import json

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
        return self._conn.get(key)
    
    def store(self, key, value, expires=None):
        try:
            self._conn.set(key, json.dumps(value))
            if expires:
                self._conn.expire(key, expires)
        except RedisError:
            return False
        else:
            return True
