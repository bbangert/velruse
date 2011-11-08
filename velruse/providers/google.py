"""Google Responder

A Google responder that authenticates against Google using OpenID, or optionally
can use OpenId+OAuth hybrid protocol to request access to Google Apps using OAuth2.

"""
try:
     from urlparse import parse_qs
except ImportError:
     from cgi import parse_qs


from openid.extensions import ax
from pyramid.util import DottedNameResolver
import oauth2 as oauth

from velruse.providers.oid_extensions import OAuthRequest
from velruse.providers.oid_extensions import UIRequest
from velruse.providers.openidconsumer import ax_attributes
from velruse.providers.openidconsumer import alternate_ax_attributes
from velruse.providers.openidconsumer import attributes
from velruse.providers.openidconsumer import OpenIDConsumer

GOOGLE_OAUTH = 'https://www.google.com/accounts/OAuthGetAccessToken'

dotted_resolver = DottedNameResolver(None)


def includeme(config):
    settings = config.registry.settings
    store = config.registry.get('velruse.openid_store')
    if not store and 'velruse.openid.store' not in settings:
        raise Exception("Missing 'velruse.openid.store' in config settings.")
    if not store:
        store = dotted_resolver.resolve(settings['velruse.openid.store'])()
        config.registry['velruse.openid_store'] = store
    realm = settings['velruse.openid.realm']
    consumer = GoogleConsumer(storage=store, realm=realm,
                              process_url='google_process',
                              oauth_key=settings.get('velruse.google.consumer_key'),
                              oauth_secret=settings.get('velruse.google.consumer_secret'),
                              request_attributes=settings.get('request_attributes')
                              )
    config.add_route("google_login", "/google/login")
    config.add_route("google_process", "/google/process",
                     use_global_views=True,
                     factory=consumer.process)
    config.add_view(consumer.login, route_name="google_login")


class GoogleConsumer(OpenIDConsumer):
    def __init__(self, oauth_key=None, oauth_secret=None,
                 request_attributes=None, *args, **kwargs):
        """Handle Google Auth
        
        This also handles making an OAuth request during the OpenID
        authentication.
        
        """
        super(GoogleConsumer, self).__init__(*args, **kwargs)
        self.oauth_key = oauth_key
        self.oauth_secret = oauth_secret
        if request_attributes:
            self.request_attributes = request_attributes.split(",")
        else:
            self.request_attributes = ['country', 'email', 'first_name', 'last_name', 'language']
    
    def _lookup_identifier(self, request, identifier):
        """Return the Google OpenID directed endpoint"""
        return "https://www.google.com/accounts/o8/id"
    
    def _update_authrequest(self, request, authrequest):
        """Update the authrequest with Attribute Exchange and optionally OAuth
        
        To optionally request OAuth, the request POST must include an 
        ``oauth_scope`` parameter that indicates what Google Apps should have
        access requested.
        
        """
        settings = request.registry.settings

        ax_request = ax.FetchRequest()
        for attr in self.request_attributes:
            ax_request.add(ax.AttrInfo(attributes[attr], required=True))
        authrequest.addExtension(ax_request)
        
        # Add OAuth request?
        oauth_scope = None
        if 'oauth_scope' in request.POST:
            oauth_scope = request.POST['oauth_scope']
        elif 'velruse.google.oauth_scope' in settings:
            oauth_scope = settings['velruse.google.oauth_scope']
        if oauth_scope:
            oauth_request = OAuthRequest(consumer=self.oauth_key,
                                         scope=oauth_scope)
            authrequest.addExtension(oauth_request)

        if 'popup_mode' in request.POST:
            kw_args = {'mode': request.POST['popup_mode']}
            if 'popup_icon' in request.POST:
                kw_args['icon'] = request.POST['popup_icon']
            ui_request = UIRequest(**kw_args)
            authrequest.addExtension(ui_request)
        return None
    
    def _get_access_token(self, request_token):
        """Retrieve the access token if OAuth hybrid was used"""
        consumer = oauth.Consumer(key=self.oauth_key, secret=self.oauth_secret)
        token = oauth.Token(key=request_token, secret='')
        client = oauth.Client(consumer, token)
        resp, content = client.request(GOOGLE_OAUTH, "POST")
        if resp['status'] != '200':
            return None
        
        access_token = dict(parse_qs(content))
        
        return {'oauthAccessToken': access_token['oauth_token'], 
                'oauthAccessTokenSecret': access_token['oauth_token_secret']}
