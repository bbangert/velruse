"""Google Authentication Views"""
from json import loads

import requests

from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

from velruse.api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from velruse.exceptions import ThirdPartyFailure
from velruse.settings import ProviderSettings
from velruse.utils import flat_url


class Google2AuthenticationComplete(AuthenticationComplete):
    """Google OAuth 2.0 auth complete"""


def includeme(config):
    config.add_directive('add_google2_login', add_google2_login)
    config.add_directive('add_google2_login_from_settings',
                         add_google2_login_from_settings)


def add_google2_login_from_settings(config, prefix='velruse.google2.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    config.add_google2_login(**p.kwargs)


def add_google2_login(config,
                     consumer_key,
                     consumer_secret,
                     scope=None,
                     login_path='/login/google2',
                     callback_path='/login/google2/callback',
                     secure=True,
                     domain='accounts.google.com',
                     name='google2'):
    """
    Add a Google OAuth 2.0 login provider to the application.
    """
    provider = Google2Provider(name,
                               consumer_key,
                               consumer_secret,
                               scope,
                               domain)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class Google2Provider(object):

    profile_scope = 'https://www.googleapis.com/auth/userinfo.profile'
    email_scope = 'https://www.googleapis.com/auth/userinfo.email'

    def __init__(self,
                 name,
                 consumer_key,
                 consumer_secret,
                 scope,
                 domain):
        self.name = name
        self.type = 'google2'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.protocol = 'https'
        self.domain = domain

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

        self.scope = scope
        if not self.scope:
            self.scope = ' '.join((self.profile_scope, self.email_scope))

    def login(self, request):
        """Initiate a google login"""
        self.scope = ' '.join(request.POST.getall('scope')) or self.scope
        auth_url = flat_url(
            '%s://%s/o/oauth2/auth' % (self.protocol, self.domain),
            scope=self.scope,
            response_type='code',
            client_id=self.consumer_key,
            redirect_uri=request.route_url(self.callback_route),
            access_type='offline')
        return HTTPFound(location=auth_url)

    def callback(self, request):
        """Process the google redirect"""
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error', 'No reason provided.')
            return AuthenticationDenied(reason=reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        # Now retrieve the access token with the code
        r = requests.post('%s://%s/o/oauth2/token' % (self.protocol, self.domain),
                          data={
                              'client_id': self.consumer_key,
                              'client_secret': self.consumer_secret,
                              'redirect_uri': request.route_url(self.callback_route),
                              'code': code,
                              'grant_type': 'authorization_code'
                          })
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        token_data = loads(r.content)
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token')

        # Retrieve profile data if scopes allow
        profile = {}
        if (self.profile_scope in self.scope and
            self.email_scope in self.scope):
            user_url = flat_url(
                    '%s://www.googleapis.com/oauth2/v1/userinfo' % self.protocol,
                    access_token=access_token)
            r = requests.get(user_url)
            if r.status_code != 200:
                raise ThirdPartyFailure("Status %s: %s" % (
                    r.status_code, r.content))

            data = loads(r.content)
            profile['accounts'] = [{
                'domain': self.domain,
                'username': data['email'],
                'userid': data['id']
            }]
            profile['displayName'] = data['name']
            profile['preferredUsername'] = data['email']
            profile['verifiedEmail'] = data['email']
            profile['emails'] = [{'value': data['email']}]

        cred = {'oauthAccessToken': access_token,
                'oauthRefreshToken': refresh_token}
        return Google2AuthenticationComplete(profile=profile,
                                             credentials=cred,
                                             provider_name=self.name,
                                             provider_type=self.type)
