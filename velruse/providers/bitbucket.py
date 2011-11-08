"""Bitbucket Authentication Views"""
from urlparse import parse_qs

from pyramid.httpexceptions import HTTPFound
import oauth2 as oauth
import requests
import json

from velruse.api import BitbucketAuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure


REQUEST_URL = 'https://bitbucket.org/api/1.0/oauth/request_token/'
ACCESS_URL = 'https://bitbucket.org/api/1.0/oauth/access_token/'
USER_URL = 'https://bitbucket.org/api/1.0/user'
SIGMETHOD = oauth.SignatureMethod_HMAC_SHA1()


def includeme(config):
    config.add_route("bitbucket_login", "/bitbucket/login")
    config.add_route("bitbucket_process", "/bitbucket/process",
                     factory=bitbucket_process)
    config.add_view(bitbucket_login, route_name="bitbucket_login")


def bitbucket_login(request):
    """Initiate a bitbucket login"""
    config = request.registry.settings

    # Create the consumer and client, make the request
    consumer = oauth.Consumer(config['velruse.bitbucket.consumer_key'],
                              config['velruse.bitbucket.consumer_secret'])
    client = oauth.Client(consumer)
    params = {'oauth_callback': request.route_url('bitbucket_process')}

    # We go through some shennanigans here to specify a callback url
    oauth_request = oauth.Request.from_consumer_and_token(consumer,
        http_url=REQUEST_URL, parameters=params)
    oauth_request.sign_request(SIGMETHOD, consumer, None)
    r = requests.get(REQUEST_URL, headers=oauth_request.to_header())

    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    request_token = oauth.Token.from_string(r.content)

    request.session['token'] = r.content

    # Send the user to bitbucket now for authorization
    # there doesnt seem to be separate url for this on BB
    if config.get('velruse.bitbucket.authorize', '').lower() in ['true']: 
        req_url = 'https://bitbucket.org/api/1.0/oauth/authenticate/'
    else:
        req_url = 'https://bitbucket.org/api/1.0/oauth/authenticate/'
    oauth_request = oauth.Request.from_token_and_callback(token=request_token,
        http_url=req_url)
    return HTTPFound(location=oauth_request.to_url())


def bitbucket_process(request):
    """Process the bitbucket redirect"""
    if 'denied' in request.GET:
        return AuthenticationDenied("User denied authentication")

    config = request.registry.settings
    request_token = oauth.Token.from_string(request.session['token'])
    verifier = request.GET.get('oauth_verifier')
    if not verifier:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    request_token.set_verifier(verifier)

    # Create the consumer and client, make the request
    consumer = oauth.Consumer(config['velruse.bitbucket.consumer_key'],
                              config['velruse.bitbucket.consumer_secret'])

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
    # Setup the normalized contact info
    profile = {}
    profile['providerName'] = 'bitbucket'
    profile['displayName'] = user_data['user']['username']
    profile['identifier'] = 'https://api.bitbucket.org/1.0/users/%s/' % user_data['user']['username']
    profile['name'] = {
                       ''
                       'givenName': user_data['user']['first_name'],
                       'familyName': user_data['user']['last_name']
                       }
    cred = {'oauthAccessToken': access_token['oauth_token'][0],
            'oauthAccessTokenSecret': access_token['oauth_token_secret'][0]}
    return BitbucketAuthenticationComplete(profile=profile,
                                           credentials=cred)
