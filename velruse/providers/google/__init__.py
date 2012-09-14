from pyramid.security import NO_PERMISSION_REQUIRED

from velruse.api import register_provider
from velruse.settings import ProviderSettings

from .hybrid import GoogleConsumer, GoogleOpenIDAuthenticationComplete
from .oauth2 import GoogleOAuth2Provider


# bw compat 1.0.2
GoogleConsumer = GoogleConsumer
GoogleAuthenticationComplete = GoogleOpenIDAuthenticationComplete


def includeme(config):
    config.add_directive('add_google_login', add_google_login)
    config.add_directive('add_google_login_from_settings',
                         add_google_login_from_settings)


def add_google_login_from_settings(config, prefix='velruse.google.'):
    settings = config.registry.settings
    protocol = settings.get(prefix + 'protocol', 'hybrid')
    if protocol == 'oauth2':
        p = ProviderSettings(settings, prefix)
        p.update('consumer_key', required=True)
        p.update('consumer_secret', required=True)
        p.update('scope')
        p.update('login_path')
        p.update('callback_path')
        config.add_google_login(protocol='oauth2', **p.kwargs)
    else:
        raise ValueError('cannot automatically load google provider from '
                         'settings, unsupported protocol')


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

    A Google provider can be configured to use different protocols to
    authenticate with Google. If ``protocol`` is ``hybrid`` (the default)
    then it will use OpenID+OAuth. Otherwise, if ``protocol`` is ``oauth2``
    then authentication will happen via Google's OAuth2 endpoints.

    The OpenID+OAuth (hybrid) protocol can be configured for purely
    authentication by specifying only OpenID parameters. If you also wish
    to authorize your application to access the user's information you
    may specify OAuth credentials.

    - OpenID parameters
      + ``attrs``
      + ``realm``
      + ``storage``
    - OAuth parameters
      + ``consumer_key``
      + ``consumer_secret``
      + ``scope``

    The OAuth2 endpoint only requires the ``consumer_key`` and
    ``consumer_secret`` with an optional ``scope``.
    """
    if protocol == 'oauth2':
        provider = GoogleOAuth2Provider(
            name,
            consumer_key,
            consumer_secret,
            scope)
    else:
        provider = GoogleConsumer(
            name,
            attrs,
            realm,
            storage,
            consumer_key,
            consumer_secret,
            scope)


    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)
