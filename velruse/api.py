"""Velruse Authentication API"""
from velruse import (
    AuthenticationComplete,
    AuthenticationDenied,
    login_url,
)  # bw compat


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
