"""Douban Authentication Views"""
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

import requests
from requests_oauthlib import OAuth1

from ..api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from ..compat import parse_qsl
from ..exceptions import ThirdPartyFailure
from ..settings import ProviderSettings
from ..utils import flat_url


REQUEST_URL = 'http://www.douban.com/service/auth/request_token'
AUTH_URL = 'http://www.douban.com/service/auth/authorize'
ACCESS_URL = 'http://www.douban.com/service/auth/access_token'
USER_URL = 'http://api.douban.com/people/%40me?alt=json'


class DoubanAuthenticationComplete(AuthenticationComplete):
    """Douban auth complete"""


def includeme(config):
    config.add_directive('add_douban_login', add_douban_login)
    config.add_directive('add_douban_login_from_settings',
                         add_douban_login_from_settings)


def add_douban_login_from_settings(config, prefix='velruse.douban'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('login_path')
    p.update('callback_path')
    config.add_douban_login(**p.kwargs)


def add_douban_login(config,
                     consumer_key,
                     consumer_secret,
                     login_path='/login/douban',
                     callback_path='/login/douban/callback',
                     name='douban'):
    """
    Add a Douban login provider to the application.
    """
    provider = DoubanProvider(name, consumer_key, consumer_secret)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class DoubanProvider(object):
    def __init__(self, name, consumer_key, consumer_secret):
        self.name = name
        self.type = 'douban'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a douban login"""
        # grab the initial request token
        oauth = OAuth1(
            self.consumer_key,
            client_secret=self.consumer_secret,
            callback_uri=request.route_url(self.callback_route))
        resp = requests.post(REQUEST_URL, auth=oauth)
        if resp.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                resp.status_code, resp.content))
        request_token = dict(parse_qsl(resp.content))

        # store the token for later
        request.session['token'] = request_token

        # redirect the user to authorize the app
        auth_url = flat_url(AUTH_URL, oauth_token=request_token['oauth_token'])
        return HTTPFound(location=auth_url)

    def callback(self, request):
        """Process the douban redirect"""
        if 'denied' in request.GET:
            return AuthenticationDenied("User denied authentication",
                                        provider_name=self.name,
                                        provider_type=self.type)

        request_token = request.session['token']

        # turn our request token into an access token
        oauth = OAuth1(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=request_token['oauth_token'],
            resource_owner_secret=request_token['oauth_token_secret'])
        resp = requests.post(ACCESS_URL, auth=oauth)
        if resp.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                resp.status_code, resp.content))
        access_token = dict(parse_qsl(resp.content))
        creds = {
            'oauthAccessToken': access_token['oauth_token'],
            'oauthAccessTokenSecret': access_token['oauth_token_secret'],
        }

        # setup oauth for general api calls
        oauth = OAuth1(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=creds['oauthAccessToken'],
            resource_owner_secret=creds['oauthAccessTokenSecret'])

        # request user profile
        resp = requests.get(USER_URL, auth=oauth)
        if resp.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                resp.status_code, resp.content))

        user_data = resp.json()

        douban_user_id = access_token['douban_user_id']

        # Setup the normalized contact info
        profile = {}
        profile['id'] = douban_user_id
        profile['accounts'] = [{
            'domain': 'douban.com',
            'userid': douban_user_id,
        }]
        profile['displayName'] = user_data['title']['$t']
        profile['preferredUsername'] = user_data['title']['$t']

        return DoubanAuthenticationComplete(profile=profile,
                                            credentials=creds,
                                            provider_name=self.name,
                                            provider_type=self.type)
