"""Douban Authentication Views"""
import json
from urlparse import parse_qs
import oauth2 as oauth
import requests
from pyramid.httpexceptions import HTTPFound
from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure


REQUEST_URL = 'http://www.douban.com/service/auth/request_token'
ACCESS_URL = 'http://www.douban.com/service/auth/access_token'
USER_URL = 'http://api.douban.com/people/%40me?alt=json'
SIGMETHOD = oauth.SignatureMethod_HMAC_SHA1()


class DoubanAuthenticationComplete(AuthenticationComplete):
    """Douban auth complete"""


def includeme(config):
    config.add_route("douban_login", "/douban/login")
    config.add_route("douban_process", "/douban/process",
                     use_global_views=True,
                     factory=douban_process)
    config.add_view(douban_login, route_name="douban_login")


def douban_login(request):
    """Initiate a douban login"""
    config = request.registry.settings
    consumer = oauth.Consumer(config['velruse.douban.consumer_key'],
                              config['velruse.douban.consumer_secret'])

    oauth_request = oauth.Request.from_consumer_and_token(consumer,
        http_url=REQUEST_URL)
    oauth_request.sign_request(SIGMETHOD, consumer, None)
    r = requests.get(REQUEST_URL, headers=oauth_request.to_header())

    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    request_token = oauth.Token.from_string(r.content)

    request.session['token'] = r.content

    # Send the user to douban now for authorization
    req_url = 'http://www.douban.com/service/auth/authorize'
    oauth_request = oauth.Request.from_token_and_callback(token=request_token,
        callback=request.route_url('douban_process'), http_url=req_url)
    return HTTPFound(location=oauth_request.to_url())


def douban_process(request):
    """Process the douban redirect"""
    if 'denied' in request.GET:
        return AuthenticationDenied("User denied authentication")

    config = request.registry.settings
    request_token = oauth.Token.from_string(request.session['token'])

    # Create the consumer and client, make the request
    consumer = oauth.Consumer(config['velruse.douban.consumer_key'],
                              config['velruse.douban.consumer_secret'])
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
    return DoubanAuthenticationComplete(profile=profile, credentials=cred)
