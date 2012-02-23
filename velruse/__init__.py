"""Velruse Authentication API"""

class AuthenticationComplete(object):
    """ An AuthenticationComplete context object"""

    def __init__(self, profile=None, credentials=None):
        """Create an AuthenticationComplete object with user data"""
        self.profile = profile
        self.credentials = credentials

class AuthenticationDenied(object):
    """ An AuthenticationDenied context object. Used when the provider
    returned successfully but without proper credentials. This may be
    the case if the user cancels the login."""

    def __init__(self, reason=None):
        self.reason = reason

def register_provider(config, name, provider):
    """
    Add a provider to the registry. This will also provide conflict
    detection by detecting duplicate provider names.
    """

    def register():
        registry = config.registry

        if not hasattr(registry, 'velruse_providers'):
            providers = {}
            registry.velruse_providers = providers

        registry.velruse_providers[name] = provider

    config.action(('velruse-provider', name), register)

def login_url(request, name):
    """
    Generate the login URL for a provider.
    """
    registry = request.registry
    provider = registry.velruse_providers[name]
    return request.route_url(provider.login_route)

def includeme(config):
    config.include('velruse.providers.bitbucket')
    config.include('velruse.providers.douban')
    config.include('velruse.providers.facebook')
    config.include('velruse.providers.github')
    config.include('velruse.providers.google')
    config.include('velruse.providers.lastfm')
    config.include('velruse.providers.linkedin')
    config.include('velruse.providers.live')
    config.include('velruse.providers.openid')
    config.include('velruse.providers.qq')
    config.include('velruse.providers.renren')
    config.include('velruse.providers.taobao')
    config.include('velruse.providers.twitter')
    config.include('velruse.providers.weibo')
    config.include('velruse.providers.yahoo')
