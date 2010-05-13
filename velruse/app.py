"""Velruse WSGI App

The Velruse WSGI app acts to handle authentication using the configured plugins
specified in the YAML file.

Example YAML config file::
    
    Store:
        Redis: true
    Facebook:
        Consumer Key: KMfXjzsA2qVUcnnRn3vpnwWZ2pwPRFZdb
        Consumer Secret: ULZ6PkJbsqw2GxZWCIbOEBZdkrb9XwgXNjRy
    Google:
        OAuth Consumer Key: yourdomain.com
        OAuth Consumer Secret: KMfXjzsA2qVUcnnRn3vpnwWZ2pwPRFZdb
    Yahoo:
        Consumer Key: eoCrFwnpBWXjbim5dyG6EP7HzjhQzFsMAcQOEK
        Consumer Secret: ULZ6PkJbsqw2GxZWCIbOEBZdkrb9XwgXNjRy
    Twitter:
        Consumer Key: ULZ6PkJbsqw2GxZWCIbOEBZdkrb9XwgXNjRy
        Consumer Secret: eoCrFwnpBWXjbim5dyG6EP7HzjhQzFsMAcQOEK
    OpenID:
        Realm: http://*.example.com
        Endpoint Regex: http://example.com/.*
    OpenID Store:
        Type: openidredis:RedisStore

Note that some providers take optional parameters, if a provider takes parameters, they
should be provided, or if no additional parameters will be used indicating true is
suffficient for the provider to be available.

OpenID based providers such as Google/Yahoo required the OpenID Store parameter to be
configured.

Default URL mapping to trigger provider authentication processing:
    
    Google
        /google/auth
    Yahoo
        /yahoo/auth
    OpenID
        /openid/auth
    Twitter
        /twitter/auth

If this WSGI application is mounted under a prefix, ie. 'velruse', the prefix should be
moved to ``environ['SCRIPT_NAME']`` before the velruse WSGI app is called.

.. note::
    
    The Velruse app relies on being able to set session specific information, using
    Beaker. Beaker should be loaded and configured in front of the Velruse WSGI App,
    or if using the :class:`~velruse.app.VelruseResponder`, the Beaker session should
    be available as the 'session' attribute on the :class:`~webob.Request~ object
    passed in.

"""
import sys
import webob
import webob.exc as exc
import yaml

import velruse.providers as providers
import velruse.store as store
from velruse.utils import path_info_pop

PROVIDERS = {
    'Facebook': providers.FacebookResponder,
    'Google': providers.GoogleResponder,
    'Yahoo': providers.YahooResponder,
    'OpenID': providers.OpenIDResponder,
    'Twitter': providers.TwitterResponder,
}

STORAGE = {
    'Redis': store.RedisStore,
}


def parse_config_file(config_file):
    """Parse a YAML config file to load and configure
    the appropriate auth providers"""
    f = open(config_file, 'r')
    content = f.read()
    f.close()
    config = yaml.load(content)
    
    # Initialize the UserStore(s) first for use with the providers
    stores = config['Store']
    for k, v in STORAGE.items():
        if k in stores:
            config['UserStore'] = STORAGE[k].load_from_config(stores[k])
    
    # Check for and load the OpenID Store if present
    oid_store = config.pop('OpenID Store')
    if oid_store:
        type_string = oid_store.pop('Type')
        package_name, obj_name = type_string.split(':')
        __import__(package_name)
        obj = getattr(sys.modules[package_name], obj_name)
        config['OpenID Store'] = obj(**oid_store)
        
    # The loaded providers
    auth_providers = {}
    
    # Initialize the providers
    for k, v in PROVIDERS.items():
        if k not in config:
            continue
        params = PROVIDERS[k].parse_config(config)
        auth_providers[k.lower()] = PROVIDERS[k](**params)    
    return auth_providers


class VelruseResponder(object):
    """Velruse Responder
    
    Works in the same manner as the :class:`~velruse.app.VelruseApp` except
    utilizing the :term:`responder` API.
    
    """
    def __init__(self, config_file):
        self.providers = parse_config_file(config_file)
    
    def __call__(self, request):
        provider = path_info_pop(request.environ).lower()
        if provider not in self.providers:
            return exc.HTTPNotFound()
        else:
            return self.providers[provider](request)


class VelruseApp(object):
    def __init__(self, config_file):
        self.config = parse_config_file(config_file)
    
    def __call__(self, environ, start_response):
        req = webob.Request(environ)
        provider = path_info_pop(environ)
        if provider not in self.config:
            return exc.HTTPNotFound()(environ, start_response)
        else:
            return self.config['provider'](req)(environ, start_response)
