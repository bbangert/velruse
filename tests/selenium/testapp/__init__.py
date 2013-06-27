import json

from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.view import view_config

from velruse import login_url


@view_config(
    name='login',
    request_method='GET',
    renderer='{}:templates/login.mako'.format(__name__),
)
def login_view(request):
    return {
        'login_url': lambda name: login_url(request, name),
        'providers': request.registry.settings['login_providers'],
    }


@view_config(
    context='velruse.AuthenticationComplete',
    renderer='{}:templates/result.mako'.format(__name__),
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
    renderer='{}:templates/result.mako'.format(__name__),
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

    if 'google_hybrid' in providers:
        config.include('velruse.providers.google_hybrid')
        config.add_google_hybrid_login(
            realm=settings['velruse.google_hybrid.realm'],
            consumer_key=settings['velruse.google_hybrid.consumer_key'],
            consumer_secret=settings['velruse.google_hybrid.consumer_secret'],
            scope=settings.get('velruse.google_hybrid.scope'),
            login_path='/login/google_hybrid',
            callback_path='/login/google_hybrid/callback',
            name='google_hybrid',
        )

    if 'google_oauth2' in providers:
        config.include('velruse.providers.google_oauth2')
        config.add_google_oauth2_login(
            consumer_key=settings['velruse.google_oauth2.consumer_key'],
            consumer_secret=settings['velruse.google_oauth2.consumer_secret'],
            scope=settings.get('velruse.google_oauth2.scope'),
            login_path='/login/google_oauth2',
            callback_path='/login/google_oauth2/callback',
            name='google_oauth2',
        )

    if 'openid' in providers:
        config.include('velruse.providers.openid')
        config.add_openid_login(
            realm=settings['velruse.openid.realm'],
        )

    if 'yahoo' in providers:
        config.include('velruse.providers.yahoo')
        config.add_yahoo_login(
            realm=settings['velruse.yahoo.realm'],
            consumer_key=settings['velruse.yahoo.consumer_key'],
            consumer_secret=settings['velruse.yahoo.consumer_secret'],
        )

    if 'linkedin' in providers:
        config.include('velruse.providers.linkedin')
        config.add_linkedin_login(
            settings['velruse.linkedin.consumer_key'],
            settings['velruse.linkedin.consumer_secret'],
        )

    config.scan(__name__)
    return config.make_wsgi_app()
