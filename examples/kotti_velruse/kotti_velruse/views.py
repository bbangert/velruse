from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.request import Request

from velruse.api import login_url
from velruse.app import find_providers


log = __import__('logging').getLogger(__name__)


def includeme(config):
    config.add_view(login,
                    route_name='login',
                    request_method='GET',
                    renderer='kotti_velruse:templates/login.mako')
    config.add_view(login_,
                    route_name='login_',
                    renderer='json')
    config.add_view(logged_in,
                    route_name='logged_in',
                    renderer='json')
    config.add_view(logout,
                    route_name='logout',
                    permission='view')

    config.add_route('login',     '/login')
    config.add_route('login_',    '/login_')
    config.add_route('logged_in', '/logged_in')
    config.add_route('logout',    '/logout')

    config.add_static_view(name='static', path='kotti_velruse:static')

    ####################################################################################
    # This route named '' MUST BE THE LAST ONE in the global list of routes.
    # It means that plugin kotti_velruse MUST BE THE LAST ONE in the list of includes.
    #
    # It's definitely a bad idea to employ a route named ''.
    # But, in order to avoid this, we would have to change openid-selector too much :(
    # ... which is outside of our requirements for this demo.
    ####################################################################################
    config.add_static_view(name='',       path='kotti_velruse:openid-selector')


def login(request):
    settings = request.registry.settings
    project = settings['kotti.site_title']
    return {
        'project' : project,
        'login_url': request.route_url('login_'),
    }


def login_(request):
    ####################################################################################
    # Let's clarify the difference between "provider" and "method":
    #
    # * Conceptually, methods can be understood pretty much like protocols or transports.
    #   So, methods would be for example: OpenID, OAuth2, CAS, LDAP.
    # * A provider is simply an entity, like Verisign, Google, Yahoo, Launchpad and
    #   hundreds of other entities which employ popular methods like OpenID and OAuth2.
    # * In particular, certain entities implement their own methods (or protocols) or
    #   they eventually offer several authentication methods. For this reason, there are
    #   specific methods for "yahoo", "tweeter", "google_hybrid", "google_oauth2", etc.
    #
    # For the SAKE OF SIMPLICITY we arbitrarity consider providers and methods simply
    # as entities in this function in particular.
    ####################################################################################
    provider=request.params['method']

    settings = request.registry.settings
    if not provider in find_providers(settings):
        raise HTTPNotFound('Provider "{}" is not configured'.format(provider)).exception

    velruse_url = login_url(request, provider)

    payload = dict(request.params)
    if 'yahoo'    == provider: payload['oauth'] = 'true'
    if 'facebook' == provider: payload['scope'] = 'email,publish_stream,read_stream,create_event,offline_access'
    if 'openid'   == provider: payload['use_popup'] = 'false'
    payload['format'] = 'json'

    redirect = Request.blank(velruse_url, POST=payload)
    try:
        response = request.invoke_subrequest( redirect )
        return response
    except:
        message = 'Provider "{}" is probably misconfigured'.format(provider)
        raise HTTPNotFound(message).exception


def logged_in(request):
    token = request.params['token']
    storage = request.registry.velruse_store
    try:
        return storage.retrieve(token)
    except KeyError:
        message = 'invalid token "{}"'.format(token)
        log.error(message)
        return { 'error' : message }


def logout(request):
    from pyramid.security import forget
    request.session.invalidate()
    request.session.flash('Session logoff.')
    headers = forget(request)
    return HTTPFound(location=request.route_url('login'), headers=headers)
