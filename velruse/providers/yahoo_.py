import oauth2 as oauth

from velruse.providers.oid_extensions import OAuthRequest
from velruse.providers.openidconsumer import OpenIDResponder

YAHOO_OAUTH = 'https://api.login.yahoo.com/oauth/v2/get_token'


class YahooResponder(OpenIDResponder):
    def __init__(self, consumer=None, oauth_key=None, oauth_secret=None, *args,
                 **kwargs):
        """Handle Yahoo Auth
        
        This also handles making an OAuth request during the OpenID
        authentication.
        
        """
        super(YahooResponder, self).__init__(*args, **kwargs)
        self.consumer = consumer
        self.oauth_secret = oauth_secret

    @classmethod
    def parse_config(cls, config):
        """Parse config data from a config file
        
        We call the super's parse_config first to update it with our additional
        values.
        
        """
        conf = OpenIDResponder.parse_config(config)
        params = {}
        key_map = {'Consumer Key': 'consumer', 'Consumer Secret': 'oauth_secret',
                   'Realm': 'realm', 'Endpoint Regex': 'endpoint_regex'}
        yahoo_vals = config['Yahoo']
        for k, v in key_map.items():
            if k in yahoo_vals:
                params[v] = yahoo_vals[k]
        conf.update(params)
        return conf
    
    def _lookup_identifier(self, req, identifier):
        """Return the Yahoo OpenID directed endpoint"""
        return 'https://yahoo.com/'
    
    def _update_authrequest(self, req, authrequest):
        super(YahooResponder, self)._update_authrequest(self, req, authrequest)
        
        # Add OAuth request?
        if 'oauth' in req.POST:
            oauth_request = OAuthRequest(consumer=self.consumer)
            authrequest.addExtension(oauth_request)
        return None
