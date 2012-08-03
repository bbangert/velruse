"""Twitter Authentication Views"""
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


REQUEST_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_URL = 'https://api.twitter.com/oauth/access_token'


class TwitterAuthenticationComplete(AuthenticationComplete):
    """Twitter auth complete"""


def includeme(config):
    config.add_directive('add_twitter_login', add_twitter_login)
    config.add_directive('add_twitter_login_from_settings',
                         add_twitter_login_from_settings)


def add_twitter_login_from_settings(config, prefix='velruse.twitter.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('login_path')
    p.update('callback_path')
    config.add_twitter_login(**p.kwargs)


def add_twitter_login(config,
                      consumer_key,
                      consumer_secret,
                      login_path='/login/twitter',
                      callback_path='/login/twitter/callback',
                      name='twitter'):
    """
    Add a Twitter login provider to the application.
    """
    provider = TwitterProvider(name, consumer_key, consumer_secret)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class TwitterProvider(object):
    def __init__(self, name, consumer_key, consumer_secret):
        self.name = name
        self.type = 'twitter'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a Twitter login"""
        # Create the consumer and client, make the request
        consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)
        sigmethod = oauth.SignatureMethod_HMAC_SHA1()
        params = {'oauth_callback': request.route_url(self.callback_route)}

        # We go through some shennanigans here to specify a callback url
        oauth_request = oauth.Request.from_consumer_and_token(consumer,
            http_url=REQUEST_URL, parameters=params)
        oauth_request.sign_request(sigmethod, consumer, None)
        r = requests.get(REQUEST_URL, headers=oauth_request.to_header())

        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        request_token = oauth.Token.from_string(r.content)

        request.session['token'] = r.content

        # Send the user to twitter now for authorization
        req_url = 'https://api.twitter.com/oauth/authenticate'
        oauth_request = oauth.Request.from_token_and_callback(
            token=request_token, http_url=req_url)
        return HTTPFound(location=oauth_request.to_url())

    def callback(self, request):
        """Process the Twitter redirect"""
        if 'denied' in request.GET:
            return AuthenticationDenied("User denied authentication",
                                        provider_name=self.name,
                                        provider_type=self.type)

        request_token = oauth.Token.from_string(request.session['token'])
        verifier = request.GET.get('oauth_verifier')
        if not verifier:
            raise ThirdPartyFailure("Oauth verifier not returned")
        request_token.set_verifier(verifier)

        # Create the consumer and client, make the request
        consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)

        client = oauth.Client(consumer, request_token)
        resp, content = client.request(ACCESS_URL, "POST")
        if resp['status'] != '200':
            raise ThirdPartyFailure("Status %s: %s" % (resp['status'], content))
        access_token = dict(parse_qs(content))

        # Setup the normalized contact info
        profile = {}
        profile['accounts'] = [{
            'domain':'twitter.com',
            'userid':access_token['user_id'][0]
        }]
        profile['displayName'] = access_token['screen_name'][0]

        cred = {'oauthAccessToken': access_token['oauth_token'][0],
                'oauthAccessTokenSecret': access_token['oauth_token_secret'][0]}
        return TwitterAuthenticationComplete(profile=profile,
                                             credentials=cred,
                                             provider_name=self.name,
                                             provider_type=self.type)
