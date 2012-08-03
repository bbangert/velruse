"""Douban Authentication Views"""
import json
from urlparse import parse_qs

import oauth2 as oauth

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


REQUEST_URL = 'http://www.douban.com/service/auth/request_token'
ACCESS_URL = 'http://www.douban.com/service/auth/access_token'
USER_URL = 'http://api.douban.com/people/%40me?alt=json'
SIGMETHOD = oauth.SignatureMethod_HMAC_SHA1()


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
        consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)

        oauth_request = oauth.Request.from_consumer_and_token(consumer,
            http_url=REQUEST_URL)
        oauth_request.sign_request(SIGMETHOD, consumer, None)
        r = requests.get(REQUEST_URL, headers=oauth_request.to_header())

        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        request_token = oauth.Token.from_string(r.content)

        request.session['token'] = r.content

        # Send the user to douban now for authorization
        req_url = 'http://www.douban.com/service/auth/authorize'
        oauth_request = oauth.Request.from_token_and_callback(
            token=request_token,
            callback=request.route_url(self.callback_route),
            http_url=req_url)
        return HTTPFound(location=oauth_request.to_url())

    def callback(self, request):
        """Process the douban redirect"""
        if 'denied' in request.GET:
            return AuthenticationDenied("User denied authentication",
                                        provider_name=self.name,
                                        provider_type=self.type)

        request_token = oauth.Token.from_string(request.session['token'])

        # Create the consumer and client, make the request
        consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)
        client = oauth.Client(consumer, request_token)
        resp, content = client.request(ACCESS_URL)
        if resp['status'] != '200':
            raise ThirdPartyFailure("Status %s: %s" % (resp['status'], content))

        access_token = dict(parse_qs(content))
        cred = {'oauthAccessToken': access_token['oauth_token'][0],
                'oauthAccessTokenSecret': access_token['oauth_token_secret'][0]}

        douban_user_id = access_token['douban_user_id'][0]
        token = oauth.Token(key=cred['oauthAccessToken'],
                            secret=cred['oauthAccessTokenSecret'])

        client = oauth.Client(consumer, token)
        resp, content = client.request(USER_URL)

        user_data = json.loads(content)
        # Setup the normalized contact info
        profile = {
            'accounts': [{'domain':'douban.com', 'userid':douban_user_id}],
            'displayName': user_data['title']['$t'],
            'preferredUsername': user_data['title']['$t'],
        }
        return DoubanAuthenticationComplete(profile=profile,
                                            credentials=cred,
                                            provider_name=self.name,
                                            provider_type=self.type)
