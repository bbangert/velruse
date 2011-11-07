"""LinkedIn Authentication Views"""
from urlparse import parse_qs

from simplejson import loads
from pyramid.httpexceptions import HTTPFound
import oauth2 as oauth
import requests

from velruse.api import LinkedInAuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure


REQUEST_URL = 'https://api.linkedin.com/uas/oauth/requestToken'
ACCESS_URL = 'https://api.linkedin.com/uas/oauth/accessToken'


def includeme(config):
    config.add_route("linkedin_login", "/linkedin/login")
    config.add_route("linkedin_process", "/linkedin/process",
                     factory=linkedin_process)
    config.add_view(linkedin_login, route_name="linkedin_login")


def linkedin_login(request):
    """Initiate a LinkedIn login"""
    config = request.registry.settings

    # Create the consumer and client, make the request
    consumer = oauth.Consumer(config['velruse.linkedin.consumer_key'],
                              config['velruse.linkedin.consumer_secret'])
    client = oauth.Client(consumer)
    sigmethod = oauth.SignatureMethod_HMAC_SHA1()
    params = {'oauth_callback': request.route_url('linkedin_process')}

    # We go through some shennanigans here to specify a callback url
    oauth_request = oauth.Request.from_consumer_and_token(consumer,
        http_url=REQUEST_URL, parameters=params)
    oauth_request.sign_request(sigmethod, consumer, None)
    r = requests.get(REQUEST_URL, headers=oauth_request.to_header())

    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    request_token = oauth.Token.from_string(r.content)

    request.session['token'] = r.content

    # Send the user to linkedin now for authorization
    if config.get('velruse.linkedin.authorize', '').lower() in ['true']:
        req_url = 'https://api.linkedin.com/uas/oauth/authorize'
    else:
        req_url = 'https://api.linkedin.com/uas/oauth/authenticate'
    oauth_request = oauth.Request.from_token_and_callback(
        token=request_token, http_url=req_url)
    return HTTPFound(location=oauth_request.to_url())


def linkedin_process(request):
    """Process the LinkedIn redirect"""
    if 'denied' in request.GET:
        return AuthenticationDenied("User denied authentication")

    config = request.registry.settings
    request_token = oauth.Token.from_string(request.session['token'])
    verifier = request.GET.get('oauth_verifier')
    if not verifier:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    request_token.set_verifier(verifier)

    # Create the consumer and client, make the request
    consumer = oauth.Consumer(config['velruse.linkedin.consumer_key'],
                              config['velruse.linkedin.consumer_secret'])

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
    profile_url = 'http://api.linkedin.com/v1/people/~'
    profile_url += ':(first-name,last-name,id,date-of-birth,picture-url)'
    profile_url += '?format=json'
    resp, content = client.request(profile_url)

    if resp['status'] != '200':
        raise ThirdPartyFailure("Status %s: %s" % (resp['status'], content))
    data = loads(content)

    # Setup the normalized contact info
    profile = {}
    profile['providerName'] = 'LinkedIn'
    profile['displayName'] = data['firstName'] + data['lastName']
    profile['name'] = {
        'givenName': data['firstName'],
        'familyName': data['lastName'],
        'formatted': data['firstName'] + data['lastName']
    }
    profile['identifier'] = data['id']

    # Create and raise our AuthenticationComplete exception with the
    # appropriate data to be passed
    complete = LinkedInAuthenticationComplete(
        profile=profile, credentials=cred)
    return complete
