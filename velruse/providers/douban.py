"""Douban Authentication Views"""
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

import requests

from ..api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from ..exceptions import ThirdPartyFailure
from ..settings import ProviderSettings
from ..utils import flat_url


class DoubanAuthenticationComplete(AuthenticationComplete):
    """Douban auth complete"""


def includeme(config):
    config.add_directive('add_douban_login', add_douban_login)
    config.add_directive('add_douban_login_from_settings',
                         add_douban_login_from_settings)


def add_douban_login_from_settings(config, prefix='velruse.douban.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    config.add_douban_login(**p.kwargs)


def add_douban_login(config,
                     consumer_key,
                     consumer_secret,
                     scope=None,
                     login_path='/login/douban',
                     callback_path='/login/douban/callback',
                     name='douban'):
    """
    Add a Douban login provider to the application.
    """
    provider = DoubanProvider(name, consumer_key, consumer_secret, scope)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class DoubanProvider(object):
    def __init__(self, name, consumer_key, consumer_secret, scope):
        self.name = name
        self.type = 'douban'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a douban login"""
        scope = request.POST.get('scope', self.scope)
        url = flat_url('https://www.douban.com/service/auth2/auth',
                       scope=scope,
                       client_id=self.consumer_key,
                       response_type='code',
                       redirect_uri=request.route_url(self.callback_route))
        return HTTPFound(url)

    def callback(self, request):
        """Process the douban redirect"""
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error', 'No reason provided.')
            return AuthenticationDenied(reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        r = requests.post(
            'https://www.douban.com/service/auth2/token',
            dict(client_id=self.consumer_key,
            client_secret=self.consumer_secret,
            grant_type='authorization_code',
            redirect_uri=request.route_url(self.callback_route),
            code=code)
        )
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        token_data = r.json()
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token')
        user_id = token_data['douban_user_id']

        # Retrieve profile data if scopes allow
        profile = {
            'accounts': [{'domain': 'douban.com', 'userid': user_id}],
        }
        user_url = flat_url(
            'https://api.douban.com/v2/user/%s' % user_id,
        )
        r = requests.get(user_url)
        if r.status_code == 200:
            data = r.json()
            profile['displayName'] = data['name']
            profile['preferredUsername'] = data['name']
            profile['avatar'] = data['large_avatar']
            profile['data'] = data

        cred = {'oauthAccessToken': access_token,
                'oauthRefreshToken': refresh_token}

        return DoubanAuthenticationComplete(profile=profile,
                                            credentials=cred,
                                            provider_name=self.name,
                                            provider_type=self.type)
