from pyramid.config import Configurator
from pyramid.view import view_config

@view_config(name='login', request_method='GET',
             renderer='testapp:templates/login.mako')
def login_view(request):
    return {}

@view_config(name='login_endpoint', request_method='POST')
def login_endpoint_view(request):
    return request.response

@view_config(name='logged_in')
def logged_in_view(request):
    return request.response

@view_config(name='login_denied')
def login_denied_view(request):
    return request.response

def main(global_conf, **settings):
    config = Configurator(settings=settings)
    config.scan(__name__)
    return config.make_wsgi_app()
