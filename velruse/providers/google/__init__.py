from pyramid.security import NO_PERMISSION_REQUIRED

from velruse.api import register_provider
from velruse.settings import ProviderSettings

from hybrid import GoogleConsumer
from oauth2 import GoogleOAuth2Provider


def includeme(config):
    config.add_directive('add_google_login', add_google_login)
    config.add_directive('add_google_oauth2_login_from_settings',
                         add_google_oauth2_login_from_settings)


def add_google_oauth2_login_from_settings(config, prefix='velruse.google.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    if settings.get(prefix + 'protocol') == 'oauth2':
        p.update('consumer_key', required=True)
        p.update('consumer_secret', required=True)
        p.update('scope')
        p.update('login_path')
        p.update('callback_path')
        config.add_google_login(protocol='oauth2', **p.kwargs)


def add_google_login(config,
                     attrs=None,
                     realm=None,
                     storage=None,
                     consumer_key=None,
                     consumer_secret=None,
                     scope=None,
                     login_path='/login/google',
                     callback_path='/login/google/callback',
                     name='google',
                     protocol='hybrid'):
    """
    Add a Google login provider to the application.

    Supports two protocols: OAuth2 and Hybrid (OAuth + OpenID).

    OpenID parameters: attrs, realm, storage

    OAuth parameters: consumer_key, consumer_secret, scope
    """
    if protocol == 'oauth2':
        provider = GoogleOAuth2Provider(name, consumer_key, consumer_secret, scope)
    else:
        provider = GoogleConsumer(name, attrs, realm, storage,
                                  consumer_key, consumer_secret, scope)


    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)
