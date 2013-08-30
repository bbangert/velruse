"""Twitter Authentication Views"""
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


REQUEST_URL = 'https://api.twitter.com/oauth/request_token'
AUTH_URL = 'https://api.twitter.com/oauth/authenticate'
ACCESS_URL = 'https://api.twitter.com/oauth/access_token'
DATA_URL = 'https://api.twitter.com/1.1/users/show.json?screen_name=%s'

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
    config.add_view(provider, attr='login',
                    route_name=provider.login_route,
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
        # grab the initial request token
        oauth = OAuth1(
            self.consumer_key,
            client_secret=self.consumer_secret,
            callback_uri=request.route_url(self.callback_route))
        resp = requests.post(REQUEST_URL, auth=oauth)
        if resp.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                resp.status_code, resp.content))
        request_token = dict(parse_qsl(resp.text))

        # store the token for later
        request.session['token'] = request_token

        # redirect the user to authorize the app
        auth_url = flat_url(AUTH_URL, oauth_token=request_token['oauth_token'])
        return HTTPFound(location=auth_url)

    def callback(self, request):
        """Process the Twitter redirect"""
        if 'denied' in request.GET:
            return AuthenticationDenied("User denied authentication",
                                        provider_name=self.name,
                                        provider_type=self.type)
        verifier = request.GET.get('oauth_verifier')
        if not verifier:
            raise ThirdPartyFailure("No oauth_verifier returned")

        request_token = request.session['token']

        # turn our request token into an access token
        oauth = OAuth1(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=request_token['oauth_token'],
            resource_owner_secret=request_token['oauth_token_secret'],
            verifier=verifier)
        resp = requests.post(ACCESS_URL, auth=oauth)
        if resp.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                resp.status_code, resp.content))
        access_token = dict(parse_qsl(resp.text))
        creds = {
            'oauthAccessToken': access_token['oauth_token'],
            'oauthAccessTokenSecret': access_token['oauth_token_secret'],
        }

        username = access_token['screen_name']

        # Setup the normalized contact info
        profile = {}
        profile['accounts'] = [{
            'domain': 'twitter.com',
            'userid': access_token['user_id'],
            'username': username,
        }]
        profile['displayName'] = username
        profile['preferredUsername'] = username

        oauth = OAuth1(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=access_token['oauth_token'],
            resource_owner_secret=access_token['oauth_token_secret'])
        resp = requests.get(DATA_URL % username, auth=oauth)
        if resp.status_code == 200:
            data = resp.json()
            if 'name' in data:
                # replace display name with the full name
                profile['displayName'] = data['name']
                profile['name'] = {'formatted': profile['displayName']}
            if 'url' in data:
                profile['urls'] = [{'value': data['url']}]
            if 'location' in data:
                profile['addresses'] = [{'formatted': data['location']}]
            if 'profile_image_url' in data:
                profile['photos'] = [{'value': data['profile_image_url']}]
            if data.get('utc_offset'):
                offset = float(data['utc_offset']) / 3600
                h = int(offset)
                m = int(abs(offset - h) * 60)
                profile['utcOffset'] = '{h:+03d}:{m:02d}'.format(h=h, m=m)

        return TwitterAuthenticationComplete(profile=profile,
                                             credentials=creds,
                                             provider_name=self.name,
                                             provider_type=self.type)
