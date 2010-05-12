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
        self.oauth_key = oauth_key
        self.oauth_secret = oauth_secret
    
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
