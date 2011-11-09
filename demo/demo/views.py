from pyramid.view import view_config

@view_config(context='velruse.api.AuthenticationComplete', renderer='json')
def auth_complete_view(context, request):
    return {
        'profile': context.profile,
        'credentials': context.credentials,
    }


@view_config(context='velruse.exceptions.AuthenticationDenied',
             renderer='json')
def auth_denied_view(context, request):
    return context.args
