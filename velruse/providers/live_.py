"""Windows Live ID Delegated Authentication"""
import urlparse

from openid.oidutil import autoSubmitHTML
from routes import Mapper
from webob import Response
import httplib2
import webob.exc as exc

import velruse.utils as utils

class LiveResponder(utils.RouteResponder):
    """Handle Windows Live ID Delegated Authentication"""
    map = Mapper()
    map.connect('login', '/auth', action='login', requirements=dict(method='POST'))
    map.connect('process', '/process', action='process')
    
    def __init__(self, storage, application_id, secret_key, return_url=None, policy_url=None,
                 offers=None):
        # We import here to avoid triggering Crypto imports for users that
        # aren't going to use Windows Live and haven't installed PyCrypto
        from velruse.WindowsLiveLogin import WindowsLiveLogin
        self.application_id = application_id
        self.secret_key = secret_key
        self.return_url = return_url
        self.policy_url = policy_url
        self.offers = offers
        self.storage = storage
        self.WindowsLiveLogin = WindowsLiveLogin
    
    @classmethod
    def parse_config(cls, config):
        """Parse config data from a config file"""
        key_map = {'Application ID': 'application_id', 'Secret Key': 'secret_key',
                   'Policy URL': 'policy_url', 'Return URL': 'return_url', 'Offers': 'offers'}
        live_vals = config['Live']
        params = {}
        for k, v in key_map.items():
            if k not in live_vals:
                continue
            params[v] = live_vals[k]
        params['storage'] = config['UserStore']
        return params
    
    def _create_wll(self):
        return self.WindowsLiveLogin(appid=self.application_id, secret=self.secret_key, 
                                     securityalgorithm='wsignin1.0', returnurl=self.return_url,
                                     policyurl=self.policy_url)
        
    def login(self, req):
        wll = self._create_wll()
        return exc.HTTPFound(location=wll.getLoginUrl())
    
    def process(self, req):
        wll = self._create_wll()
        action = req.POST['action']
        
        finished = False
        if action == 'delauth':
            user = wll.processToken(req.session['user_token'])
            del req.session['user_token']
            consenttoken = wll.processConsent(req.POST)
            finished = True
        else:
            consenttoken = None
            user = wll.processLogin(req.POST)
            if not self.offers:
                finished = True
        
        if not finished:
            req.session['user_token'] = user.getToken()
            req.session.save()
            return exc.HTTPFound(location=wll.getConsentUrl(self.offers))
        
        profile = {}
        profile['providerName'] = 'Live'
        profile['identifier'] = 'http://live.com/%s' % user.getId()
        
        result_data = {'status': 'ok', 'profile': profile}
        
        if consenttoken:
            result_data['credentials'] = {'consentToken': consenttoken.getToken()}
        
        # Generate the token, store the extracted user-data for 5 mins, and send back
        token = utils.generate_token()
        self.storage.store(token, result_data, expires=300)
        form_html = utils.redirect_form(req.session['end_point'], token)
        return Response(body=autoSubmitHTML(form_html))
