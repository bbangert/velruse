import json

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.view import view_config

import requests


@view_config(name='login', request_method='GET',
             renderer='testapp:templates/login.mako')
def login_view(request):
    return {}


@view_config(name='login_endpoint', request_method='POST')
def login_endpoint_view(request):
    token = request.params['token']
    url = '%s/velruse/auth_info?format=json&token=%s' % (
        request.host_url, token)
    response = requests.get(url)
    result = json.loads(response.content)

    request.session['result'] = result

    if 'profile' not in result:
        return HTTPFound(request.resource_url(request.root, 'login_denied'))

    return HTTPFound(request.resource_url(request.root, 'logged_in'))


@view_config(name='logged_in', renderer='testapp:templates/result.mako')
@view_config(name='login_denied', renderer='testapp:templates/result.mako')
def result_view(request):
    result = request.session['result']
    return {
        'result': json.dumps(result, indent=4),
    }

def main(global_conf, **settings):
    session_factory = UnencryptedCookieSessionFactoryConfig('seekrit')

    config = Configurator(settings=settings)
    config.set_session_factory(session_factory)

    config.scan(__name__)
    return config.make_wsgi_app()
