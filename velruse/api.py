"""Velruse Authentication API"""

class AuthenticationComplete(object):
    """ An AuthenticationComplete context object"""

    def __init__(self, profile=None, credentials=None):
        """Create an AuthenticationComplete object with user data"""
        self.profile = profile
        self.credentials = credentials

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
