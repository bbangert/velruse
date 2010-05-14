import urlparse

from routes import Mapper
import httplib2
import webob.exc as exc

import velruse.utils as utils


AUTHORIZE_URL = 'https://graph.facebook.com/oauth/authorize'
ACCESS_URL = 'https://graph.facebook.com/oauth/access_token'
PROFILE_URL = 'https://graph.facebook.com/me'

def extract_fb_data(data):
    # Setup the normalized contact info
    nick = None
    
    # Setup the nick and preferred username to the last portion of the
    # FB link URL if its not their ID
    link = data.get('link')
    if link:
        last = link.split('/')[-1]
        if last != data['id']:
            nick = last
    
    profile = {
        'providerName': 'Facebook',
        'identifier': 'https://graph.facebook.com/%s' % data['id'],
        'displayName': data['name'],
        'emails': [data.get('email')],
        'verifiedEmail': data['verified'] and data.get('email'),
        'gender': data.get('gender'),
        'preferredUsername': nick or data['name'],
    }
    tz = data.get('timezone')
    if tz:
        parts = str(tz).split(':')
        if len(parts) > 1:
            h, m = parts
        else:
            h, m = parts[0], '00'
        if len(h) < 3:
            h = '%s0%s' % (h[0], h[1])
        data['utfOffset'] = ':'.join([h, m])
    bday = data.get('birthday')
    if bday:
        mth, day, yr = bday.split('/')
        profile['birthday'] = '-'.join(yr, mth, day)
    
    name = {}
    pcard_map = {'first_name': 'givenName', 'last_name': 'familyName'}
    for key, val in pcard_map.items():
        part = data.get(key)
        if part:
            name[val] = part
    name['formatted'] = data.get('name')
    
    profile['name'] = name
    
    # Now strip out empty values
    for k, v in profile.items():
        if not v or (isinstance(v, list) and not v[0]):
            del profile[k]
    
    return profile


class FacebookResponder(utils.RouteResponder):
    """Handle Twitter OAuth login/authentication"""
    map = Mapper()
    map.connect('login', '/auth', action='login', requirements=dict(method='POST'))
    map.connect('process', '/process', action='process')
    
    def __init__(self, storage, api_key, app_secret, app_id):
        self.api_key = api_key
        self.app_secret = app_secret
        self.app_id = app_id
        self.storage = storage
        self.client = httplib2.Http()
    
    @classmethod
    def parse_config(cls, config):
        """Parse config data from a config file"""
        key_map = {'API Key': 'api_key', 'Application Secret': 'app_secret', 'Application ID': 'app_id'}
        fb_vals = config['Facebook']
        params = {}
        for k, v in key_map.items():
            params[v] = fb_vals[k]
        params['storage'] = config['UserStore']
        return params
    
    def login(self, req):
        req.session['end_point'] = req.POST['end_point']
        req.session.save()
        scope = req.POST.get('scope', '')
        url = req.link(AUTHORIZE_URL, client_id=self.app_id, scope=scope,
                       redirect_uri=req.link('process', qualified=True))
        return exc.HTTPFound(location=url)
    
    def process(self, req):
        end_point = req.session['end_point']
        code = req.GET.get('code')
        if not code:
            self._error_redirect(4, end_point)
        
        access_url = req.link(ACCESS_URL, client_id=self.app_id, client_secret=self.app_secret,
                              code=code, redirect_uri=req.link('process', qualified=True))
        resp, content = self.client.request(access_url)
        if resp['status'] != '200':
            return self._error_redirect(2, end_point)
        
        access_token = urlparse.parse_qs(content)['access_token'][0]
        
        fields = 'id,first_name,last_name,name,link,birthday,email,website,verified,picture,gender,timezone'
        resp, content = self.client.request(
            req.link(PROFILE_URL, access_token=access_token, fields=fields))
        if resp['status'] != '200':
            return self._error_redirect(2, end_point)
        
        fb_profile = utils.json.loads(content)
        
        profile = extract_fb_data(fb_profile)
        result_data = {'status': 'ok', 'profile': profile}
        
        cred = {'oauthAccessToken': access_token}
        result_data['credentials'] = cred
        
        return self._success_redirect(result_data, end_point)
