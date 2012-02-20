"""Github Authentication Views

http://develop.github.com/p/oauth.html
https://github.com/account/applications
"""
from json import loads
from urlparse import parse_qs

import requests

from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

from velruse.api import AuthenticationComplete
from velruse.api import register_provider
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url


class GithubAuthenticationComplete(AuthenticationComplete):
    """Github auth complete"""

def includeme(config):
    config.add_directive('add_github_login', add_github_login)

def add_github_login(config,
                     consumer_key,
                     consumer_secret,
                     scope=None,
                     login_path='/login/github',
                     callback_path='/login/github/callback',
                     name='github'):
    """
    Add a Github login provider to the application.
    """
    provider = GithubProvider(name, consumer_key, consumer_secret, scope)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider.login, route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)

class GithubProvider(object):
    def __init__(self, name, consumer_key, consumer_secret, scope):
        self.name = name
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a github login"""
        scope = request.POST.get('scope', self.scope)
        gh_url = flat_url(
            'https://github.com/login/oauth/authorize',
            scope=scope,
            client_id=self.consumer_key,
            redirect_uri=request.route_url(self.callback_route))
        return HTTPFound(location=gh_url)

    def callback(self, request):
        """Process the github redirect"""
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error', 'No reason provided.')
            return AuthenticationDenied(reason)

        # Now retrieve the access token with the code
        access_url = flat_url(
            'https://github.com/login/oauth/access_token',
            client_id=self.consumer_key,
            client_secret=self.consumer_secret,
            redirect_uri=request.route_url(self.callback_route),
            code=code)
        r = requests.get(access_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        access_token = parse_qs(r.content)['access_token'][0]

        # Retrieve profile data
        graph_url = flat_url('https://github.com/api/v2/json/user/show',
                             access_token=access_token)
        r = requests.get(graph_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        data = loads(r.content)['user']

        profile = {}
        profile['accounts'] = [{
            'domain':'github.com',
            'username':data['login'],
            'userid':data['id']
        }]
        profile['displayName'] = data['name']
        profile['preferredUsername'] = data['login']

        # We don't add this to verifiedEmail because ppl can change email
        # addresses without verifying them
        if 'email' in data:
            profile['emails'] = [{'value':data['email']}]

        cred = {'oauthAccessToken': access_token}
        return GithubAuthenticationComplete(profile=profile,
                                            credentials=cred)
