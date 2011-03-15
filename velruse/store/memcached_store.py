"""Memcached UserStore implementation"""

import logging
log = logging.getLogger(__name__)

try:
    import memcache
except ImportError:
    # fall back for Google App Engine -- hasnt been tested though
    from google.appengine.api import memcache

#from redis.exceptions import RedisError  #unused afaik -- bayle

from velruse.store.interface import UserStore
from velruse.utils import cached_property

class MemcachedStore(UserStore):
    """Memcached Storage for Auth Provider"""

    def __init__(self, servers=None, key_prefix='velruse_ustore'):
        self.key_prefix = key_prefix
        self.servers = servers or ['localhost:11211']
    
    @classmethod
    def load_from_config(cls, config):
        """Load the MemcachedStore based on the config"""
        params = {}
        for k, v in config.items():
            key = k.lower()
            if key not in ('servers', 'key_prefix'):
                continue
            elif key == 'servers':
                params[key] = v.split(',')
            else:
                params[key] = v
        return cls(**params)
    
    @cached_property
    def _conn(self):
        """The Memcached connection, cached for this call"""
        return memcache.Client(self.servers)

    def _key(self, key):
        return str('%s:%s' % (self.key_prefix, key))
    
    def retrieve(self, key):
        return self._conn.get(self._key(key))
    
    def store(self, key, value, expires=None):
        log.debug('Servers %s storing %s=%s' % (`self.servers`, `self._key(key)`, `value`))
        
        self._conn.set(self._key(key), value, expires or 0)
        return True
    
    def delete(self, key):
        log.debug('Deleting %s', `key`)
        self._conn.delete(self._key(key))
    
    def purge_expired(self):
        pass
