"""Github Authentication Views"""
from json import loads
from urlparse import parse_qs

import requests
import uuid

from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

from velruse.api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from velruse.exceptions import CSRFError
from velruse.exceptions import ThirdPartyFailure
from velruse.settings import ProviderSettings
from velruse.utils import flat_url


class GithubAuthenticationComplete(AuthenticationComplete):
    """Github auth complete"""


def includeme(config):
    config.add_directive('add_github_login', add_github_login)
    config.add_directive('add_github_login_from_settings',
                         add_github_login_from_settings)


def add_github_login_from_settings(config, prefix='velruse.github.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    p.update('secure')
    p.update('domain')
    config.add_github_login(**p.kwargs)


def add_github_login(config,
                     consumer_key,
                     consumer_secret,
                     scope=None,
                     login_path='/login/github',
                     callback_path='/login/github/callback',
                     secure=True,
                     domain='github.com',
                     name='github'):
    """
    Add a Github login provider to the application.
    """
    provider = GithubProvider(name,
                              consumer_key,
                              consumer_secret,
                              scope,
                              secure,
                              domain)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class GithubProvider(object):
    def __init__(self,
                 name,
                 consumer_key,
                 consumer_secret,
                 scope,
                 secure,
                 domain):
        self.name = name
        self.type = 'github'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope
        self.protocol = 'http' if secure is False else 'https'
        self.domain = domain

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a github login"""
        scope = request.POST.get('scope', self.scope)
        request.session['state'] = state = uuid.uuid4().hex
        gh_url = flat_url(
            '%s://%s/login/oauth/authorize' % (self.protocol, self.domain),
            scope=scope,
            client_id=self.consumer_key,
            redirect_uri=request.route_url(self.callback_route),
            state=state)
        return HTTPFound(location=gh_url)

    def callback(self, request):
        """Process the github redirect"""
        sess_state = request.session.get('state')
        req_state = request.GET.get('state')
        if not sess_state or sess_state != req_state:
            raise CSRFError(
                'CSRF Validation check failed. Request state {req_state} is not '
                'the same as session state {sess_state}'.format(
                    req_state=req_state,
                    sess_state=sess_state
                )
            )
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error', 'No reason provided.')
            return AuthenticationDenied(reason=reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        # Now retrieve the access token with the code
        access_url = flat_url(
            '%s://%s/login/oauth/access_token' % (self.protocol, self.domain),
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
        graph_url = flat_url('%s://api.%s/user' % (self.protocol, self.domain),
                             access_token=access_token)
        graph_headers = dict(Accept='application/vnd.github.v3+json')
        r = requests.get(graph_url, headers=graph_headers)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        data = loads(r.content)

        profile = {}
        profile['accounts'] = [{
            'domain':self.domain,
            'username':data['login'],
            'userid':data['id']
        }]
        
        profile['preferredUsername'] = data['login']
        profile['displayName'] = data.get('name',profile['preferredUsername'])

        # We don't add this to verifiedEmail because ppl can change email
        # addresses without verifying them
        if 'email' in data:
            profile['emails'] = [{'value':data['email']}]

        cred = {'oauthAccessToken': access_token}
        return GithubAuthenticationComplete(profile=profile,
                                            credentials=cred,
                                            provider_name=self.name,
                                            provider_type=self.type)
