class AuthenticationComplete(object):
    """ An AuthenticationComplete context object"""

    def __init__(self,
                 profile=None,
                 credentials=None,
                 provider_name=None,
                 provider_type=None):
        """Create an AuthenticationComplete object with user data"""
        self.profile = profile
        self.credentials = credentials
        self.provider_name = provider_name
        self.provider_type = provider_type


class AuthenticationDenied(object):
    """ An AuthenticationDenied context object. Used when the provider
    returned successfully but without proper credentials. This may be
    the case if the user cancels the login."""

    def __init__(self,
                 reason=None,
                 provider_name=None,
                 provider_type=None):
        self.reason = reason
        self.provider_name = provider_name
        self.provider_type = provider_type


def login_url(request, name):
    """ Generate the login URL for a provider."""
    registry = request.registry
    provider = registry.velruse_providers[name]
    return request.route_url(provider.login_route)
