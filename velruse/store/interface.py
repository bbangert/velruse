"""UserStore Interface

All backend stores for userdata should implement the UserStore interface
as defined here.

"""
class UserStore(object):
    """This is the interface for storing retrieved and normalized userdata"""
    def retrieve(self, key):
        """This method retrieves the data for a key from the storage.
        
        The stored data is a JSON serialized dict and should be deserialized
        using :func:`simplejson.loads` before being returned.
        
        :param key: The key to retrieve. Keys are always ascii-safe strings.
        :returns: User information
        :rtype: dict
        
        """
        raise NotImplementedError
    
    def store(self, key, value, expires=None):
        """This method stores a users data dict in the storage.
        
        The supplied value will be a dict and should be JSON serialized with the
        :func:`simplejson.dumps` function before being stored. 
        
        :param key: The key to store the value under.
        :param value: The userdata to store
        :param expires: Optional expiration time in seconds from now before the
                        stored data should be removed.
        :type value: dict
        :returns: True if the data was stored successfully, False otherwise.
        :rtype: boolean
        
        """
        raise NotImplementedError
