"""Velruse WSGI App

The Velruse WSGI app acts to handle authentication using the configured plugins
specified in the YAML file.

Example YAML config file::
    
    Store:
        Type: Redis
    Facebook:
        API Key: eb7cf817bab6e28d3b941811cf1b014e
        Application Secret: KMfXjzsA2qVUcnnRn3vpnwWZ2pwPRFZdb
        Application ID: ULZ6PkJbsqw2GxZWCIbOEBZdkrb9XwgXNjRy
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
    Live:
        Application ID: 00000000004242234EA4
        Secret Key: eoCrFwnpBWXjbim5dyG6EP7HzjhQzFsMAcQOEK
        Policy URL: http://YOURDOMAIN/policy.html
        Offers: Contacts.View
    OpenID Store:
        Type: openidredis:RedisStore

Note that some providers take optional parameters, if a provider takes parameters, they
should be provided, or if no additional parameters will be used, indicating true is
suffficient for the provider to be available.

OpenID based providers such as Google/Yahoo required the OpenID Store parameter to be
configured.

Default URL mapping to trigger provider authentication processing::
    
    Google
        /google/auth
    Yahoo
        /yahoo/auth
    OpenID
        /openid/auth
    Twitter
        /twitter/auth
    Windows Live
        /live/auth

If this WSGI application is mounted under a prefix, ie. 'velruse', the prefix should be
moved to ``environ['SCRIPT_NAME']`` before the velruse WSGI app is called.

.. note::
    
    The Velruse app relies on being able to set session specific information, using
    Beaker. Beaker should be loaded and configured in front of the Velruse WSGI App,
    or if using the :class:`~velruse.app.VelruseResponder`, the Beaker session should
    be available as the 'session' attribute on the :class:`~webob.Request` object
    passed in.

"""
import webob
import webob.exc as exc
import yaml

from beaker.middleware import SessionMiddleware

import velruse.providers as providers
import velruse.store as store
from velruse.utils import path_info_pop, load_package_obj

PROVIDERS = {
    'Facebook': providers.FacebookResponder,
    'Google': providers.GoogleResponder,
    'Live': providers.LiveResponder,
    'OpenID': providers.OpenIDResponder,
    'Twitter': providers.TwitterResponder,
    'Yahoo': providers.YahooResponder,
}

STORAGE = {
    'Memory': store.MemoryStore,
    'Redis': store.RedisStore,
    'MongoDB': store.MongoDBStore,
}


def parse_config_file(config_file):
    """Parse a YAML config file to load and configure
    the appropriate auth providers"""
    f = open(config_file, 'r')
    content = f.read()
    f.close()
    config = yaml.load(content)
    
    # Initialize the UserStore(s) first for use with the providers
    store_config = config['Store']
    store_type = store_config.pop('Type')
    if store_type in STORAGE: 
        config['UserStore'] = STORAGE[store_type].load_from_config(store_config)
    else:
        obj = load_package_obj(store_type)
        config['UserStore'] = obj.load_from_config(store_config)

    # Check for and load the OpenID Store if present
    oid_store = config.pop('OpenID Store', None)
    if oid_store:
        obj = load_package_obj(oid_store.pop('Type'))
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

def parse_session_options(config_file):
    """Parse a YAML config file to load and configure
    the appropriate auth providers"""
    f = open(config_file, 'r')
    content = f.read()
    f.close()
    config = yaml.load(content)
    options = {}
    if 'beaker' not in config:
        return options
    
    for k, v in config['beaker']:
        options['beaker.%s' % k] = v
    return options

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
    """Velruse WSGI App
    
    The Velruse WSGI App mounts several Auth Providers as specified in the
    YAML configuration file they're passed.
    
    """
    def __init__(self, config_file):
        self.config = parse_config_file(config_file)
    
    def __call__(self, environ, start_response):
        req = webob.Request(environ)
        req.session = environ['beaker.session']
        provider = path_info_pop(environ)
        if provider not in self.config:
            return exc.HTTPNotFound()(environ, start_response)
        else:
            return self.config[provider](req)(environ, start_response)


def make_app(config_file):
    """Construct a complete WSGI app solely from a YAML config file"""
    app = VelruseApp(config_file)
    app = SessionMiddleware(app, parse_session_options(config_file))
    return app

    
def make_velruse_app(global_conf, config_file, **app_conf):
    """Construct a complete WSGI app ready to serve by Paste
    
    Example INI file:
    
    .. code-block:: ini
        
        [server:main]
        use = egg:Paste#http
        host = 0.0.0.0
        port = 80

        [composite:main]
        use = egg:Paste#urlmap
        / = YOURAPP
        /velruse = velruse

        [app:velruse]
        use = egg:velruse
        config_file = %(here)s/LOCATION_TO/CONFIG.yaml
        beaker.session.data_dir = %(here)s/data/sdata
        beaker.session.lock_dir = %(here)s/data/slock
        beaker.session.key = velruse
        beaker.session.secret = somesecret
        beaker.session.type = cookie
        beaker.session.validate_key = STRONG_KEY_HERE
        beaker.session.cookie_domain = .yourdomain.com

        [app:YOURAPP]
        use = egg:YOURAPP
        full_stack = true
        static_files = true
        
    """
    app = VelruseApp(config_file)
    app = SessionMiddleware(app, app_conf)
    return app
