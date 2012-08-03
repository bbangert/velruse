"""Taobao Authentication Views"""
from hashlib import md5
from json import loads
import time

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


class TaobaoAuthenticationComplete(AuthenticationComplete):
    """Taobao auth complete"""


def includeme(config):
    config.add_directive('add_taobao_login', add_taobao_login)
    config.add_directive('add_taobao_login_from_settings',
                         add_taobao_login_from_settings)


def add_taobao_login_from_settings(config, prefix='velruse.taobao.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('login_path')
    p.update('callback_path')
    config.add_taobao_login(**p.kwargs)


def add_taobao_login(config,
                     consumer_key,
                     consumer_secret,
                     login_path='/login/taobao',
                     callback_path='/login/taobao/callback',
                     name='taobao'):
    """
    Add a Taobao login provider to the application.
    """
    provider = TaobaoProvider(name, consumer_key, consumer_secret)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class TaobaoProvider(object):
    def __init__(self, name, consumer_key, consumer_secret):
        self.name = name
        self.type = 'taobao'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a taobao login"""
        gh_url = flat_url('https://oauth.taobao.com/authorize',
                          client_id=self.consumer_key,
                          response_type='code',
                          redirect_uri=request.route_url(self.callback_route))
        return HTTPFound(location=gh_url)

    def callback(self, request):
        """Process the taobao redirect"""
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error', 'No reason provided.')
            return AuthenticationDenied(reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        # Now retrieve the access token with the code
        r = requests.post('https://oauth.taobao.com/token',
                dict(grant_type='authorization_code',
                     client_id=self.consumer_key,
                     client_secret=self.consumer_secret,
                     redirect_uri=request.route_url(self.callback_route),
                     code=code))
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        data = loads(r.content)
        access_token = data['access_token']

        # Retrieve profile data
        params = {
                'method': 'taobao.user.get',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                'format': 'json',
                'app_key': self.consumer_key,
                'v': '2.0',
                'sign_method': 'md5',
                'fields': 'user_id,nick',
                'session': access_token
                }
        src = self.consumer_secret\
                + ''.join(["%s%s" % (k, v) for k, v in sorted(params.items())])\
                + self.consumer_secret
        params['sign'] = md5(src).hexdigest().upper()
        get_user_info_url = flat_url('http://gw.api.taobao.com/router/rest',
                                     **params)
        r = requests.get(get_user_info_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
        data = loads(r.content)

        username = data['user_get_response']['user']['nick']
        userid = data['user_get_response']['user']['user_id']

        profile = {
            'accounts': [{'domain':'taobao.com', 'userid':userid}],
            'displayName': username,
            'preferredUsername': username,
        }

        cred = {'oauthAccessToken': access_token}
        return TaobaoAuthenticationComplete(profile=profile,
                                            credentials=cred,
                                            provider_name=self.name,
                                            provider_type=self.type)
