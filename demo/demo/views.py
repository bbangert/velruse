from pyramid.view import view_config


@view_config(
    context='velruse.AuthenticationComplete',
    renderer='json',
)
def auth_complete_view(context, request):
    return {
        'profile': context.profile,
        'credentials': context.credentials,
    }

@view_config(
    context='velruse.AuthenticationDenied',
    renderer='json',
)
def auth_denied_view(context, request):
    return context.reason
