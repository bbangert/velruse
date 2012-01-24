"""Bitbucket Authentication Views

http://confluence.atlassian.com/display/BITBUCKET/OAuth+on+Bitbucket
"""

import json
from urlparse import parse_qs

import oauth2 as oauth
import requests

from pyramid.httpexceptions import HTTPFound

from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure


REQUEST_URL = 'https://bitbucket.org/api/1.0/oauth/request_token/'
ACCESS_URL = 'https://bitbucket.org/api/1.0/oauth/access_token/'
USER_URL = 'https://bitbucket.org/api/1.0/user'
SIGMETHOD = oauth.SignatureMethod_HMAC_SHA1()

class BitbucketAuthenticationComplete(AuthenticationComplete):
    """Bitbucket auth complete"""
    provider = 'bitbucket'

def includeme(config):
    config.add_directive('add_bitbucket_login', BitbucketProvider().setup)

class BitbucketProvider(object):

    def setup(
        self,
        config,
        consumer_key,
        consumer_secret,
        entry_path='/bitbucket/login',
        callback_path='/bitbucket/login/callback',
    ):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        config.add_route('bitbucket.login', entry_path)
        config.add_route('bitbucket.process', callback_path,
                         use_global_views=True,
                         factory=self.process)
        config.add_view(self.login, route_name='bitbucket.login')

    def login(self, request):
        """Initiate a bitbucket login"""
        # Create the consumer and client, make the request
        consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)
        params = {'oauth_callback': request.route_url('bitbucket_process')}

        # We go through some shennanigans here to specify a callback url
        oauth_request = oauth.Request.from_consumer_and_token(consumer,
            http_url=REQUEST_URL, parameters=params)
        oauth_request.sign_request(SIGMETHOD, consumer, None)
        r = requests.get(REQUEST_URL, headers=oauth_request.to_header())

        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        request_token = oauth.Token.from_string(r.content)

        request.session['token'] = r.content

        req_url = 'https://bitbucket.org/api/1.0/oauth/authenticate/'
        oauth_request = oauth.Request.from_token_and_callback(
            token=request_token, http_url=req_url)
        return HTTPFound(location=oauth_request.to_url())

    def process(self, request):
        """Process the bitbucket redirect"""
        if 'denied' in request.GET:
            return AuthenticationDenied("User denied authentication")

        request_token = oauth.Token.from_string(request.session['token'])
        verifier = request.GET.get('oauth_verifier')
        if not verifier:
            raise ThirdPartyFailure("No oauth_verifier returned")
        request_token.set_verifier(verifier)

        # Create the consumer and client, make the request
        consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)

        client = oauth.Client(consumer, request_token)
        resp, content = client.request(ACCESS_URL, "POST")
        if resp['status'] != '200':
            raise ThirdPartyFailure("Status %s: %s" % (resp['status'], content))
        access_token = dict(parse_qs(content))

        cred = {'oauthAccessToken': access_token['oauth_token'][0],
                'oauthAccessTokenSecret': access_token['oauth_token_secret'][0]}

        # Make a request with the data for more user info
        token = oauth.Token(key=cred['oauthAccessToken'],
                            secret=cred['oauthAccessTokenSecret'])

        client = oauth.Client(consumer, token)
        resp, content = client.request(USER_URL)
        user_data = json.loads(content)
        data = user_data['user']
        # Setup the normalized contact info
        profile = {}
        profile['accounts'] = [{
            'domain':'bitbucket.com',
            'username':data['username']
        }]
        profile['preferredUsername'] = data['username']
        profile['name'] = {
            'formatted': '%s %s' % (data['first_name'], data['last_name']),
            'givenName': data['first_name'],
            'familyName': data['last_name'],
            }
        profile['displayName'] = profile['name']['formatted']
        return BitbucketAuthenticationComplete(profile=profile,
                                               credentials=cred)
