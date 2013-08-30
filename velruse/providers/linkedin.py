"""LinkedIn Authentication Views"""
import requests
from requests_oauthlib import OAuth1

from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

from ..api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from ..compat import parse_qsl
from ..exceptions import ThirdPartyFailure
from ..settings import ProviderSettings
from ..utils import flat_url


REQUEST_URL = 'https://api.linkedin.com/uas/oauth/requestToken'
AUTH_URL = 'https://api.linkedin.com/uas/oauth/authenticate'
ACCESS_URL = 'https://api.linkedin.com/uas/oauth/accessToken'


class LinkedInAuthenticationComplete(AuthenticationComplete):
    """LinkedIn auth complete"""


def includeme(config):
    config.add_directive('add_linkedin_login', add_linkedin_login)
    config.add_directive('add_linkedin_login_from_settings',
                         add_linkedin_login_from_settings)


def add_linkedin_login_from_settings(config, prefix='velruse.linkedin.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('login_path')
    p.update('callback_path')
    config.add_linkedin_login(**p.kwargs)


def add_linkedin_login(config,
                       consumer_key,
                       consumer_secret,
                       login_path='/login/linkedin',
                       callback_path='/login/linkedin/callback',
                       name='linkedin'):
    """
    Add a Last.fm login provider to the application.
    """
    provider = LinkedInProvider(name, consumer_key, consumer_secret)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class LinkedInProvider(object):
    def __init__(self, name, consumer_key, consumer_secret):
        self.name = name
        self.type = 'linked_in'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a LinkedIn login"""
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
        """Process the LinkedIn redirect"""
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

        profile_url = 'http://api.linkedin.com/v1/people/~'
        profile_url += (':(first-name,last-name,id,date-of-birth,picture-url,'
                        'email-address)')
        profile_url += '?format=json'

        resp = requests.get(profile_url, auth=oauth)
        if resp.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                resp.status_code, resp.content))
        data = resp.json()

        # Setup the normalized contact info
        profile = {}
        profile['displayName'] = data['firstName'] + data['lastName']
        profile['name'] = {
            'givenName': data['firstName'],
            'familyName': data['lastName'],
            'formatted': u'%s %s' % (data['firstName'], data['lastName'])
        }
        if data.get('emailAddress'):
            profile['emails'] = [{'value': data.get('emailAddress')}]
        if data.get('pictureUrl'):
            profile['photos'] = [{'value': data.get('pictureUrl')}]

        profile['accounts'] = [{
            'domain': 'linkedin.com',
            'userid': data['id']
        }]
        return LinkedInAuthenticationComplete(profile=profile,
                                              credentials=creds,
                                              provider_name=self.name,
                                              provider_type=self.type)
