"""Bitbucket Authentication Views

http://confluence.atlassian.com/display/BITBUCKET/OAuth+on+Bitbucket
"""
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


REQUEST_URL = 'https://bitbucket.org/api/1.0/oauth/request_token/'
AUTH_URL = 'https://bitbucket.org/api/1.0/oauth/authenticate/'
ACCESS_URL = 'https://bitbucket.org/api/1.0/oauth/access_token/'
USER_URL = 'https://bitbucket.org/api/1.0/user'
EMAIL_URL = 'https://bitbucket.org/api/1.0/users/{username}/emails'


class BitbucketAuthenticationComplete(AuthenticationComplete):
    """Bitbucket auth complete"""


def includeme(config):
    config.add_directive('add_bitbucket_login', add_bitbucket_login)
    config.add_directive('add_bitbucket_login_from_settings',
                         add_bitbucket_login_from_settings)


def add_bitbucket_login_from_settings(config, prefix='velruse.bitbucket.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('login_path')
    p.update('callback_path')
    config.add_bitbucket_login(**p.kwargs)


def add_bitbucket_login(config,
                        consumer_key,
                        consumer_secret,
                        login_path='/bitbucket/login',
                        callback_path='/bitbucket/login/callback',
                        name='bitbucket'):
    """
    Add a Bitbucket login provider to the application.
    """
    provider = BitbucketProvider(name, consumer_key, consumer_secret)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class BitbucketProvider(object):
    def __init__(self, name, consumer_key, consumer_secret):
        self.name = name
        self.type = 'bitbucket'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a bitbucket login"""
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
        """Process the bitbucket redirect"""
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

        data = user_data['user']

        username = data['username']

        # Setup the normalized contact info
        profile = {}
        profile['accounts'] = [{
            'domain': 'bitbucket.com',
            'username': username,
        }]
        profile['preferredUsername'] = username
        name = {}
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        if first_name or last_name:
            name['formatted'] = u'{0} {1}'.format(first_name, last_name).strip()
        if first_name:
            name['givenName'] = first_name
        if last_name:
            name['familyName'] = last_name
        if name:
            profile['name'] = name
        display_name = name.get('formatted')
        if not display_name:
            display_name = data.get('display_name')
        profile['displayName'] = display_name

        # request user emails
        resp = requests.get(EMAIL_URL.format(username=username), auth=oauth)
        if resp.status_code == 200:
            data = resp.json()
            emails = []
            for item in data:
                email = {'value': item['email']}
                if item.get('primary'):
                    email['primary'] = True
                emails.append(email)
                if item.get('active'):
                    profile['verifiedEmail'] = item['email']
            profile['emails'] = emails

        return BitbucketAuthenticationComplete(profile=profile,
                                               credentials=creds,
                                               provider_name=self.name,
                                               provider_type=self.type)
