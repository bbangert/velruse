from pyramid.view import view_config

from velruse.api import login_url

@view_config(
    context='velruse.api.AuthenticationComplete',
    renderer='json',
)
def auth_complete_view(context, request):
    return {
        'profile': context.profile,
        'credentials': context.credentials,
    }

@view_config(
    context='velruse.exceptions.AuthenticationDenied',
    renderer='json',
)
def auth_denied_view(context, request):
    return context.args

@view_config(
    name='login',
    renderer='demo:templates/login.mako',
)
def login_view(request):
    return {
        'login_url': lambda name: login_url(request, name),
    }
