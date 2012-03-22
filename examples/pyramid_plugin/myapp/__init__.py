from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.view import view_config

@view_config(
    name='login',
    renderer='myapp:templates/login.mako',
)
def login_view(request):
    return {}

@view_config(
    context='velruse.AuthenticationComplete',
    renderer='myapp:templates/result.mako',
)
def login_success_view(request):
    return {}

@view_config(
    context='velruse.AuthenticationDenied',
    renderer='myapp:templates/result.mako',
)
def login_failed_view(request):
    return {}

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application."""
    session_factory = UnencryptedCookieSessionFactoryConfig(
        settings['cookie.secret'],
    )
    config = Configurator(settings=settings)
    config.set_session_factory(session_factory)
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.scan()
    return config.make_wsgi_app()
