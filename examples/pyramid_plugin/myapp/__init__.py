import json
import logging

from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.view import view_config

from velruse import login_url

log = logging.getLogger(__name__)

@view_config(
    name='login',
    renderer='myapp:templates/login.mako',
)
def login_view(request):
    return {
        'login_url': login_url,
        'providers': request.registry.settings['login_providers'],
    }

@view_config(
    context='velruse.AuthenticationComplete',
    renderer='myapp:templates/result.mako',
)
def login_complete_view(request):
    context = request.context
    result = {
        'profile': context.profile,
        'credentials': context.credentials,
    }
    return {
        'result': json.dumps(result, indent=4),
    }

@view_config(
    context='velruse.AuthenticationDenied',
    renderer='myapp:templates/result.mako',
)
def login_denied_view(request):
    return {
        'result': 'denied',
    }

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application."""
    # velruse requires session support
    session_factory = UnencryptedCookieSessionFactoryConfig(
        settings['session.secret'],
    )

    # determine which providers we want to configure
    providers = settings.get('login_providers', '')
    providers = filter(None, [p.strip()
                              for line in providers.splitlines()
                              for p in line.split(', ')])
    settings['login_providers'] = providers
    if not any(providers):
        log.warn('no login providers configured, double check your ini '
                 'file and add a few')

    config = Configurator(settings=settings)
    config.set_session_factory(session_factory)
    config.add_static_view('static', 'static', cache_max_age=3600)

    if 'facebook' in providers:
        config.include('velruse.providers.facebook')
        config.add_facebook_login_from_settings(prefix='facebook.')

    if 'github' in providers:
        config.include('velruse.providers.github')
        config.add_github_login_from_settings(prefix='github.')

    if 'twitter' in providers:
        config.include('velruse.providers.twitter')
        config.add_twitter_login_from_settings(prefix='twitter.')

    if 'live' in providers:
        config.include('velruse.providers.live')
        config.add_live_login_from_settings(prefix='live.')

    if 'bitbucket' in providers:
        config.include('velruse.providers.bitbucket')
        config.add_bitbucket_login_from_settings(prefix='bitbucket.')

    if 'google' in providers:
        config.include('velruse.providers.google')
        config.add_google_login(
            realm=settings['google.realm'],
            consumer_key=settings['google.consumer_key'],
            consumer_secret=settings['google.consumer_secret'],
        )

    if 'yahoo' in providers:
        config.include('velruse.providers.yahoo')
        config.add_yahoo_login(
            realm=settings['yahoo.realm'],
            consumer_key=settings['yahoo.consumer_key'],
            consumer_secret=settings['yahoo.consumer_secret'],
        )

    config.scan()
    return config.make_wsgi_app()
