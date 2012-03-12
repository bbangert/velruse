import json

from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.view import view_config

from velruse.api import login_url


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
    context='velruse.api.AuthenticationComplete',
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
    context='velruse.api.AuthenticationDenied',
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
    config.include('velruse')

    config.set_session_factory(session_factory)

    if 'facebook' in providers:
        config.add_facebook_login(
            settings['facebook.app_id'],
            settings['facebook.app_secret'],
        )

    if 'github' in providers:
        config.add_github_login(
            settings['github.app_id'],
            settings['github.app_secret'],
        )

    if 'twitter' in providers:
        config.add_twitter_login(
            settings['twitter.consumer_key'],
            settings['twitter.consumer_secret'],
        )

    if 'live' in providers:
        config.add_live_login(
            settings['live.client_id'],
            settings['live.client_secret'],
        )

    if 'bitbucket' in providers:
        config.add_bitbucket_login(
            settings['bitbucket.consumer_key'],
            settings['bitbucket.consumer_secret'],
        )

    if 'google' in providers:
        config.add_google_login(
            realm=settings['google.realm'],
            consumer_key=settings['google.consumer_key'],
            consumer_secret=settings['google.consumer_secret'],
        )

    if 'yahoo' in providers:
        config.add_yahoo_login(
            realm=settings['yahoo.realm'],
            consumer_key=settings['yahoo.consumer_key'],
            consumer_secret=settings['yahoo.consumer_secret'],
        )

    config.scan(__name__)
    return config.make_wsgi_app()
