
import copy
import logging
import os
import re

from pyramid.config import Configurator
from pyramid.exceptions import ConfigurationError
from pyramid.response import Response
from pyramid.view import view_config

from velruse.utils import generate_token
from velruse.utils import redirect_form
from velruse.utils import splitlines


log = logging.getLogger(__name__)
re_flags = re.U|re.X|re.S

def auth_providers_list(request):
    """Return a JSON mapping of the velruse offered providers.
    This is to be used inside velruse front ends:
    Something like ::

        {
            'velruse.providers.github': {
                      'login'   : 'http://velrusehost/velruse/github/login',
                      'process' : 'http://velrusehost/velruse/github/process',
            },
        }


    """
    settings = request.registry.settings
    ifs = copy.deepcopy(
        settings['velruse.providers_infos']
    )
    url_keys = ['login', 'process']
    for item in ifs:
        for key in ifs[item]:
            for pattern in url_keys:
                if re.compile(pattern, re_flags).search(key):
                    ifs[item][pattern] = request.route_url(ifs[item][key])
    return ifs

@view_config(context='velruse.api.AuthenticationComplete')
def auth_complete_view(context, request):
    endpoint = context.profile.get(
        'endpoint', request.registry.settings.get('velruse.endpoint'))
    token = generate_token()
    storage = request.registry.velruse_store
    result_data = {
        'profile': context.profile,
        'credentials': context.credentials,
    }
    storage.store(token, result_data, expires=300)
    form = redirect_form(endpoint, token)
    return Response(form)


@view_config(context='velruse.exceptions.AuthenticationDenied')
def auth_denied_view(context, request):
    endpoint = request.POST.get(
        'endpoint', request.GET.get(
            'endpoint', request.GET.get(
                'return_to', request.registry.settings.get(
                    'velruse.endpoint'))))
    token = generate_token()
    storage = request.registry.velruse_store
    error_dict = {
        'code': getattr(context, 'code', None),
        'description': getattr(context, 'description', 
                               getattr(context, 'message', '')),
    }
    storage.store(token, error_dict, expires=300)
    form = redirect_form(endpoint, token)
    return Response(body=form)


@view_config(name='auth_info', request_param='format=json', renderer='json')
def auth_info_view(request):
    storage = request.registry.velruse_store
    token = request.GET['token']
    return storage.retrieve(token)


def default_setup(config):
    from pyramid.session import UnencryptedCookieSessionFactoryConfig

    log.info('Using an unencrypted cookie-based session. This can be '
             'changed by pointing the "velruse.setup" setting at a different '
             'function for configuring the session factory.')

    settings = config.registry.settings
    secret = settings.get('velruse.session.secret')
    if secret is None:
        log.warn('Configuring unencrypted cookie-based session with a '
                 'random secret which will invalidate old cookies when '
                 'restarting the app.')
        secret = ''.join('%02x' % ord(x) for x in os.urandom(16))
    factory = UnencryptedCookieSessionFactoryConfig(secret)
    config.set_session_factory(factory)

def providers_lookup(config):
    """Lookup for the providers to activate
    Can be overridden by settings
    velruse.providers_lookup = mymodule.hook
    This can be useful for example if your authentication information
    is stored on a relational database.
    """
    settings = config.registry.settings
    providers_hook = settings.get('velruse.providers_hook', '')
    if providers_hook:
        providers_hook = config.maybe_dotted(providers_hook)
        providers_hook(config)
    providers = []
    for a in splitlines(
        settings.get('velruse.providers', '')
    ):
        providers.append(a)
        settings['velruse.providers_infos'][a] = {}
    return providers

def includeme(config, do_setup=True):
    """Configuration function to make a pyramid app a velruse one."""
    settings = config.registry.settings
    # setup application
    setup = settings.get('velruse.setup', default_setup)
    if do_setup:
        config.include(setup)

    if not settings.get('velruse.endpoint'):
        raise ConfigurationError(
            'missing required setting "velruse.endpoint"')

    # setup backing storage
    store = settings.get('velruse.store')
    if store is None:
        raise ConfigurationError(
            'invalid setting velruse.store: {0}'.format(store))
    config.include(store)

    # include providers
    if not 'velruse.providers_infos' in settings:
        settings['velruse.providers_infos'] = {}
    providers = providers_lookup(config)
    for provider in providers:
        config.include(provider)

    # add the error views
    config.scan(__name__)
    config.add_route("auth_providers_list", "/auth_providers_list")
    config.add_view(auth_providers_list, route_name="auth_providers_list", renderer='json')


def make_app(**settings):
    config = Configurator(settings=settings)
    includeme(config)
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

        velruse.endpoint = http://example.com/logged_in

        velruse.store = velruse.store.redis
        velruse.store.host = localhost
        velruse.store.port = 6379
        velruse.store.db = 0
        velruse.store.key_prefix = velruse_ustore

        velruse.providers =
            velruse.providers.facebook
            velruse.providers.twitter

        velruse.facebook.app_secret = KMfXjzsA2qVUcnnRn3vpnwWZ2pwPRFZdb
        velruse.facebook.app_id = ULZ6PkJbsqw2GxZWCIbOEBZdkrb9XwgXNjRy
        velruse.twitter.consumer_key = ULZ6PkJbsqw2GxZWCIbOEBZdkrb9XwgXNjRy
        velruse.twitter.consumer_secret = eoCrFwnpBWXjbim5dyG6EP7HzjhQzFsMAcQOEK

        [app:YOURAPP]
        use = egg:YOURAPP
        full_stack = true
        static_files = true

    """
    return make_app(**settings)
