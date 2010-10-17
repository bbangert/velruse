import urlparse
import logging

from routes import Mapper
import httplib2
import oauth2 as oauth
import webob.exc as exc

import velruse.utils as utils

log = logging.getLogger(__name__)

REQUEST_URL = 'https://twitter.com/oauth/request_token'
ACCESS_URL = 'https://twitter.com/oauth/access_token'
AUTHORIZE_URL = 'https://twitter.com/oauth/authenticate'


class TwitterResponder(utils.RouteResponder):
    """Handle Twitter OAuth login/authentication"""
    map = Mapper()
    map.connect('login', '/auth', action='login', requirements=dict(method='POST'))
    map.connect('process', '/process', action='process')
    
    def __init__(self, storage, consumer_key, consumer_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.storage = storage
        self._consumer = oauth.Consumer(consumer_key, consumer_secret)
        self._sigmethod = oauth.SignatureMethod_HMAC_SHA1()
    
    @classmethod
    def parse_config(cls, config):
        """Parse config data from a config file"""
        key_map = {'Consumer Key': 'consumer_key', 'Consumer Secret': 'consumer_secret'}
        twitter_vals = config['Twitter']
        params = {}
        for k, v in key_map.items():
            params[v] = twitter_vals[k]
        params['storage'] = config['UserStore']
        return params
    
    def login(self, req):
        end_point = req.POST['end_point']
        
        # Create the consumer and client, make the request
        client = oauth.Client(self._consumer)
        params = {'oauth_callback': req.link('process', qualified=True)}
        
        # We go through some shennanigans here to specify a callback url
        request = oauth.Request.from_consumer_and_token(self._consumer,
            http_url=REQUEST_URL, parameters=params)
        request.sign_request(self._sigmethod, self._consumer, None)
        resp, content = httplib2.Http.request(client, REQUEST_URL, method='GET',
            headers=request.to_header())
                    
        if resp['status'] != '200':
            log.debug("Twiter oauth failed: %r %r", resp, content)
            return self._error_redirect(3, end_point)
        
        request_token = oauth.Token.from_string(content)
        req.session['token'] = content
        req.session['end_point'] = end_point
        req.session.save()
        
        # Send the user to twitter to authorize us
        request = oauth.Request.from_token_and_callback(token=request_token, http_url=AUTHORIZE_URL)
        return exc.HTTPFound(location=request.to_url())
    
    def process(self, req):
        end_point = req.session['end_point']
        request_token = oauth.Token.from_string(req.session['token'])
        verifier = req.GET.get('oauth_verifier')
        if not verifier:
            return self._error_redirect(1, end_point)
        request_token.set_verifier(verifier)
        client = oauth.Client(self._consumer, request_token)
        resp, content = client.request(ACCESS_URL, "POST")
        if resp['status'] != '200':
            return self._error_redirect(2, end_point)
        
        access_token = dict(urlparse.parse_qsl(content))
        
        # Setup the normalized contact info
        profile = {}
        profile['providerName'] = 'Twitter'
        profile['displayName'] = access_token['screen_name']
        profile['identifier'] = 'http://twitter.com/?id=%s' % access_token['user_id']
        
        result_data = {'status': 'ok', 'profile': profile}
        
        cred = {'oauthAccessToken': access_token['oauth_token'], 
                'oauthAccessTokenSecret': access_token['oauth_token_secret']}
        result_data['credentials'] = cred
        
        return self._success_redirect(result_data, end_point)
