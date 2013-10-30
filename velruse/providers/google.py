"""This module exists as a bw-compat shim for google_hybrid."""
from .google_hybrid import (
    add_google_hybrid_login,
)

from ..settings import ProviderSettings


def includeme(config):
    config.add_directive('add_google_login', add_google_login)
    config.add_directive('add_google_login_from_settings',
                         add_google_login_from_settings)


def add_google_login_from_settings(config, prefix='velruse.google.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('login_path')
    p.update('callback_path')
    config.add_google_login(**p.kwargs)


def add_google_login(config,
                     attrs=None,
                     realm=None,
                     storage=None,
                     consumer_key=None,
                     consumer_secret=None,
                     scope=None,
                     login_path='/login/google',
                     callback_path='/login/google/callback',
                     name='google'):
    add_google_hybrid_login(config,
                            attrs, 
                            realm,
                            storage,
                            consumer_key,
                            consumer_secret,
                            scope,
                            login_path,
                            callback_path,
                            name)
