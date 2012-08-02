import json

from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.view import view_config

from velruse import login_url


@view_config(
    name='login',
    request_method='GET',
    renderer='testapp:templates/login.mako',
)
def login_view(request):
    return {
        'login_url': lambda name: login_url(request, name),
        'providers': request.registry.settings['login_providers'],
    }


@view_config(
    context='velruse.AuthenticationComplete',
    renderer='testapp:templates/result.mako',
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
    renderer='testapp:templates/result.mako',
)
def login_denied_view(request):
    return {
        'result': 'denied',
    }


def main(global_conf, **settings):
    session_factory = UnencryptedCookieSessionFactoryConfig('seekrit')

    providers = settings.get('login_providers', '')
    providers = filter(None, [p.strip()
                              for line in providers.splitlines()
                              for p in line.split(', ')])
    settings['login_providers'] = providers

    config = Configurator(settings=settings)
    config.set_session_factory(session_factory)

    if 'facebook' in providers:
        config.include('velruse.providers.facebook')
        config.add_facebook_login(
            settings['velruse.facebook.app_id'],
            settings['velruse.facebook.app_secret'],
        )

    if 'github' in providers:
        config.include('velruse.providers.github')
        config.add_github_login(
            settings['velruse.github.app_id'],
            settings['velruse.github.app_secret'],
        )

    if 'twitter' in providers:
        config.include('velruse.providers.twitter')
        config.add_twitter_login(
            settings['velruse.twitter.consumer_key'],
            settings['velruse.twitter.consumer_secret'],
        )

    if 'live' in providers:
        config.include('velruse.providers.live')
        config.add_live_login(
            settings['velruse.live.client_id'],
            settings['velruse.live.client_secret'],
        )

    if 'bitbucket' in providers:
        config.include('velruse.providers.bitbucket')
        config.add_bitbucket_login(
            settings['velruse.bitbucket.consumer_key'],
            settings['velruse.bitbucket.consumer_secret'],
        )

    if 'google' in providers:
        config.include('velruse.providers.google')
        config.add_google_login(
            realm=settings['velruse.google.realm'],
            consumer_key=settings['velruse.google.consumer_key'],
            consumer_secret=settings['velruse.google.consumer_secret'],
        )

    if 'yahoo' in providers:
        config.include('velruse.providers.yahoo')
        config.add_yahoo_login(
            realm=settings['velruse.yahoo.realm'],
            consumer_key=settings['velruse.yahoo.consumer_key'],
            consumer_secret=settings['velruse.yahoo.consumer_secret'],
        )

    config.scan(__name__)
    return config.make_wsgi_app()
