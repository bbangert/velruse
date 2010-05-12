"""Google Responder

A Google responder that authenticates against Google using OpenID, or optionally
can use OpenId+OAuth hybrid protocol to request access to Google Apps using OAuth2.

"""
import time
import urlparse

from openid.extensions import ax
import oauth2 as oauth

from velruse.providers.oid_extensions import OAuthRequest
from velruse.providers.oid_extensions import UIRequest
from velruse.providers.openidconsumer import ax_attributes
from velruse.providers.openidconsumer import OpenIDResponder

GOOGLE_OAUTH = 'https://www.google.com/accounts/OAuthGetAccessToken'


class GoogleResponder(OpenIDResponder):
    def __init__(self, consumer=None, oauth_key=None, oauth_secret=None, *args,
                 **kwargs):
        """Handle Google Auth
        
        This also handles making an OAuth request during the OpenID
        authentication.
        
        """
        super(GoogleResponder, self).__init__(*args, **kwargs)
        self.consumer = consumer
        self.oauth_secret = oauth_secret
    
    def _lookup_identifier(self, req, identifier):
        """Return the Google OpenID directed endpoint"""
        return "https://www.google.com/accounts/o8/id"
    
    def _update_authrequest(self, req, authrequest):
        """Update the authrequest with Attribute Exchange and optionally OAuth
        
        To optionally request OAuth, the request POST must include an ``oauth_scope``
        parameter that indicates what Google Apps should have access requested.
        
        """
        ax_request = ax.FetchRequest()
        for attr in ['country', 'email', 'first_name', 'last_name', 'language']:
            ax_request.add(ax.AttrInfo(ax_attributes[attr], required=True))
        authrequest.addExtension(ax_request)
        
        # Add OAuth request?
        if 'oauth_scope' in req.POST:
            oauth_request = OAuthRequest(consumer=self.consumer, scope=req.POST['oauth_scope'])
            authrequest.addExtension(oauth_request)
        
        if 'popup_mode' in req.POST:
            kw_args = {'mode': req.POST['popup_mode']}
            if 'popup_icon' in req.POST:
                kw_args['icon'] = req.POST['popup_icon']
            ui_request = UIRequest(**kw_args)
            authrequest.addExtension(ui_request)
        return None
    
    def _get_access_token(self, request_token):
        consumer = oauth.Consumer(key=self.consumer, secret=self.oauth_secret)
        token = oauth.Token(key=request_token, secret=None)
        params = {
            'oauth_version': "1.0",
            'oauth_nonce': oauth.generate_nonce(),
            'oauth_timestamp': int(time.time()),
            'oauth_token': request_token
        }
        req = oauth.Request(method="POST", url=GOOGLE_OAUTH, parameters=params)
        signature_method = oauth.SignatureMethod_HMAC_SHA1()
        req.sign_request(signature_method, consumer, token)
        
        client = oauth.Client(consumer, token)
        resp, content = client.request(GOOGLE_OAUTH, "POST")
        access_token = dict(urlparse.parse_qsl(content))
        
        return {'oauthAccessToken': access_token['oauth_token'], 
                'oauthAccessTokenSecret': access_token['oauth_token_secret']}
