"""Redis UserStore implementation"""
try:
    import cPickle as pickle
except ImportError:
    import pickle

import redis
from redis.exceptions import RedisError

from velruse.store.interface import UserStore
from velruse.utils import cached_property

class RedisStore(UserStore):
    """Redis Storage for Auth Provider"""
    def __init__(self, host='localhost', port=6379, db=0, key_prefix='velruse_ustore'):
        self.host = host
        self.port = port
        self.db = db
        self.key_prefix = key_prefix
    
    @classmethod
    def load_from_config(cls, config):
        """Load the RedisStore based on the config"""
        if config == 'true' or config == True:
            return cls()
        else:
            params = {}
            for k, v in config.items():
                key = k.lower()
                if key not in ['host', 'port', 'db', 'key_prefix']:
                    continue
                if key == 'db':
                    params['db'] = int(v)
                else:
                    params[key] = v
            return cls(**params)
    
    @cached_property
    def _conn(self):
        """The Redis connection, cached for this call"""
        return redis.Redis(host=self.host, port=self.port, db=self.db)
    
    def retrieve(self, key):
        data = self._conn.get('%s:%s' % (self.key_prefix, key))
        if data:
            return pickle.loads(data)
        else:
            return None
    
    def store(self, key, value, expires=None):
        key = '%s:%s' % (self.key_prefix, key)
        try:
            self._conn.set(key, pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
            if expires:
                self._conn.expire(key, expires)
        except RedisError:
            return False
        else:
            return True
    
    def delete(self, key):
        try:
            self._conn.delete('%s:%s' % (self.key_prefix, key))
        except RedisError:
            return False
        else:
            return True
