"""Github Authentication Views

http://develop.github.com/p/oauth.html
https://github.com/account/applications
"""
from json import loads
from urlparse import parse_qs

import requests

from pyramid.httpexceptions import HTTPFound

from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url


class GithubAuthenticationComplete(AuthenticationComplete):
    """Github auth complete"""

def includeme(config):
    config.add_directive('add_github_login', GithubProvider().setup)

class GithubProvider(object):

    def setup(
        self,
        config,
        consumer_key,
        consumer_secret,
        scope=None,
        entry_path='/github/login',
        callback_path='/github/login/callback',
    ):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope

        config.add_route('github.login', entry_path)
        config.add_route('github.process', callback_path,
                         use_global_views=True,
                         factory=self.process)
        config.add_view(self.login, route_name='github_login')

    def login(self, request):
        """Initiate a github login"""
        scope = request.POST.get('scope', self.scope)
        gh_url = flat_url(
            'https://github.com/login/oauth/authorize',
            scope=scope,
            client_id=self.consumer_key,
            redirect_uri=request.route_url('github.process'))
        return HTTPFound(location=gh_url)

    def process(self, request):
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
            redirect_uri=request.route_url('github.process'),
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
