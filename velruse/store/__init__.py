from velruse.store.memstore import MemoryStore

__all__ = ['MemoryStore']

try:
    from velruse.store.memcached_store import MemcachedStore
    __all__.append('MemcachedStore')
except ImportError, e:
    pass

try:
    from velruse.store.redis_store import RedisStore
    __all__.append('RedisStore')
except ImportError, e:
    pass

try:
    from velruse.store.mongodb_store import MongoDBStore
    __all__.append('MongoDBStore')
except ImportError, e:
    pass

try:
    from velruse.store.sqlstore import SQLStore
    __all__.append('SQLStore')
except ImportError, e:
    pass
