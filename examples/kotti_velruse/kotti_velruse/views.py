from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound


log = __import__('logging').getLogger(__name__)


def includeme(config):
    config.add_route('login',      '/login')
    config.add_route('logging_in', '/logging_in')
    config.add_route('logged_in',  '/logged_in')
    config.add_route('logout',     '/logout')

    config.add_static_view(name='static', path='kotti_velruse:static')
    config.add_static_view(name='',       path='kotti_velruse:openid-selector')


@view_config(route_name='login',
             request_method='GET',
             renderer='kotti_velruse:templates/login.mako')
def login_view(request):
    settings = request.registry.settings
    project = settings['kotti.site_title']
    login_url = request.route_url('logging_in')
    from velruse.app import find_providers
    providers = find_providers(settings)
    return {
        'project' : project,
        'login_url': login_url,
        'providers': providers,
    }


@view_config(route_name='logging_in',
             renderer='json')
def logging_in(request):
    provider=request.cookies['openid_provider']
    print('--------------------------------------------------------')
    print(provider)
    #print('+++++++++++++++')
    #print(request.params)
    #print('+++++++++++++++')
    #print('{}'.format(request))

    from velruse.api import login_url
    if provider in [ 'yahoo', 'twitter' ]:
        url = login_url(request, provider)
    elif 'facebook' == provider:
        request.params['scope'] = 'email,publish_stream,read_stream,create_event,offline_access'
    elif 'google' == provider:
        url = login_url(request, 'google_oauth2')
    elif 'winliveid' == provider:
        url = login_url(request, 'live')
    else:
        url = login_url(request, 'openid')
    print(url)
    print('--------------------------------------------------------')
    return HTTPFound(location=url)

@view_config(route_name='logged_in',
             renderer='json')
def logged_in(request):
    import requests
    token = request.POST['token']
    payload = { 'format': 'json', 'token': token }
    response = requests.get(request.host_url + '/auth_info', params=payload)
    return { 'result': response.json() }


@view_config(route_name='logout',
             permission='view')
def logout(request):
    from pyramid.security import forget
    request.session.invalidate()
    request.session.flash('Session logoff.')
    headers = forget(request)
    return HTTPFound(location=request.route_url('home'), headers=headers)
