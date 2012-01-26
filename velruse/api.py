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

        providers[name] = provider

    config.action(('velruse-provider', name), register)
