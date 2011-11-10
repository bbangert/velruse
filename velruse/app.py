from pyramid.config import Configurator
from pyramid.exceptions import ConfigurationError
from pyramid.response import Response
from pyramid.view import view_config

from velruse.utils import generate_token
from velruse.utils import redirect_form
from velruse.utils import splitlines


@view_config(context='velruse.exceptions.AuthenticationComplete')
def auth_complete_view(context, request):
    end_point = request.session['end_point']
    token = generate_token()
    storage = request.registry.velruse_store
    result_data = {
        'profile': context.profile,
        'credentials': context.credentials,
    }
    storage.store(token, result_data, expires=300)
    form = redirect_form(end_point, token)
    return Response(body=form)


@view_config(context='velruse.exceptions.AuthenticationDenied')
def auth_denied_view(context, request):
    end_point = request.session['end_point']
    token = generate_token()
    storage = request.registry.velruse_store
    error_dict = {
        'code': context.code,
        'description': context.description,
    }
    storage.store(token, error_dict, expires=300)
    form = redirect_form(end_point, token)
    return Response(body=form)


@view_config(name='auth_info', request_param='format=json', renderer='json')
def auth_info_view(request):
    token = request.GET['token']
    data = request.registry.velruse_store.retrieve(token)
    return data


def default_setup(config):
    from pyramid_beaker import session_factory_from_settings
    settings = config.registry.settings
    factory = session_factory_from_settings(settings)
    config.set_session_factory(factory)


def make_app(**settings):
    config = Configurator(settings=settings)

    # setup application
    setup = settings.get('velruse.setup', default_setup)
    config.include(setup)

    # setup backing storage
    store = settings.get('velruse.store')
    try:
        config.include(store)
    except ImportError:
        raise ConfigurationError('invalid velruse store: {0}'.format(store))

    # include providers
    providers = settings.get('velruse.providers', '')
    providers = splitlines(providers)

    for provider in providers:
        config.include(provider)

    # add the error views
    config.scan(__name__)
    return config.make_wsgi_app()


def make_velruse_app(global_conf, **settings):
    """Construct a complete WSGI app ready to serve by Paste

    Example INI file:

    .. code-block:: ini

        [server:main]
        use = egg:Paste#http
        host = 0.0.0.0
        port = 80

        [composite:main]
        use = egg:Paste#urlmap
        / = YOURAPP
        /velruse = velruse

        [app:velruse]
        use = egg:velruse

        velruse.store = velruse.store.redis
        velruse.store.host = localhost
        velruse.store.port = 6379
        velruse.store.db = 0
        velruse.store.key_prefix = velruse_ustore

        velruse.providers =
            velruse.providers.facebook
            velruse.providers.twitter

        velruse.facebook.api_key = eb7cf817bab6e28d3b941811cf1b014e
        velruse.facebook.app_secret = KMfXjzsA2qVUcnnRn3vpnwWZ2pwPRFZdb
        velruse.facebook.app_id = ULZ6PkJbsqw2GxZWCIbOEBZdkrb9XwgXNjRy
        velruse.twitter.consumer_key = ULZ6PkJbsqw2GxZWCIbOEBZdkrb9XwgXNjRy
        velruse.twitter.consumer_secret = eoCrFwnpBWXjbim5dyG6EP7HzjhQzFsMAcQOEK

        beaker.session.data_dir = %(here)s/data/sdata
        beaker.session.lock_dir = %(here)s/data/slock
        beaker.session.key = velruse
        beaker.session.secret = somesecret
        beaker.session.type = cookie
        beaker.session.validate_key = STRONG_KEY_HERE
        beaker.session.cookie_domain = .yourdomain.com

        [app:YOURAPP]
        use = egg:YOURAPP
        full_stack = true
        static_files = true

    """
    return make_app(**settings)
