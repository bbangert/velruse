from velruse.store.memstore import MemoryStore
from velruse.store.memcached_store import MemcachedStore
__all__ = ['MemoryStore', 'MemcachedStore']


try:
    from velruse.store.redis_store import RedisStore
    __all__.append('RedisStore')
except ImportError:
    pass

try:
    from velruse.store.redis_store import MongoDBStore
    __all__.append('MongoDBStore')
except ImportError:
    pass




