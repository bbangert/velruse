"""In Memory UserStore implementation"""
import time

from velruse.store.interface import UserStore

class MemoryStore(UserStore):
    """Memory Storage for Auth Provider"""
    def __init__(self):
        self._store = {}
    
    @classmethod
    def load_from_config(cls, config):
        """Load the Memory based on the config"""
        return cls()
    
    def retrieve(self, key):
        data = self._store.get(key)
        if data:
            return data[0]
        else:
            return None
    
    def store(self, key, value, expires=None):
        expiration = None
        if expires:
            expiration = time.time() + expires
        self._store[key] = (value, expiration)
        return True
    
    def delete(self, key):
        if key in self._store:
            del self._store[key]
            return True
        else:
            return False
    
    def purge_expired(self):
        now = time.time()
        to_delete = []
        
        # Record the keys to delete, there may be a lot, so we use iteritems
        # which doesn't let us change it while iterating
        for key, value in self._store.iteritems():
            if value[1] is not None and now > value[1]:
                to_delete.append(key)
        for key in to_delete:
            del self._store[key]
        return True
