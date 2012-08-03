"""Renren Authentication Views"""
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


class RenrenAuthenticationComplete(AuthenticationComplete):
    """Renren auth complete"""


def includeme(config):
    config.add_directive('add_renren_login', add_renren_login)
    config.add_directive('add_renren_login_from_settings',
                         add_renren_login_from_settings)


def add_renren_login_from_settings(config, prefix='velruse.renren.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    config.add_renren_login(**p.kwargs)


def add_renren_login(config,
                     consumer_key,
                     consumer_secret,
                     scope=None,
                     login_path='/login/renren',
                     callback_path='/login/renren/callback',
                     name='renren'):
    """
    Add a Renren login provider to the application.
    """
    provider = RenrenProvider(name, consumer_key, consumer_secret, scope)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class RenrenProvider(object):
    def __init__(self, name, consumer_key, consumer_secret, scope):
        self.name = name
        self.type = 'renren'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a renren login"""
        scope = request.POST.get('scope', self.scope)
        url = flat_url('https://graph.renren.com/oauth/authorize',
                       scope=scope,
                       client_id=self.consumer_key,
                       response_type='code',
                       redirect_uri=request.route_url(self.callback_route))
        return HTTPFound(url)

    def callback(self, request):
        """Process the renren redirect"""
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error', 'No reason provided.')
            return AuthenticationDenied(reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        access_url = flat_url(
            'https://graph.renren.com/oauth/token',
            client_id=self.consumer_key,
            client_secret=self.consumer_secret,
            grant_type='authorization_code',
            redirect_uri=request.route_url(self.callback_route),
            code=code)

        r = requests.get(access_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        data = loads(r.content)
        access_token = data['access_token']
        profile = {
            'accounts': [
                {'domain': 'renren.com', 'userid': data['user']['id']},
            ],
            'displayName': data['user']['name'],
            'preferredUsername': data['user']['name'],
        }

        cred = {'oauthAccessToken': access_token}

        return RenrenAuthenticationComplete(profile=profile,
                                            credentials=cred,
                                            provider_name=self.name,
                                            provider_type=self.type)
