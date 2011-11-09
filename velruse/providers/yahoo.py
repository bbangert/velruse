import logging

try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs


from openid.extensions import ax
import oauth2 as oauth

from velruse.providers.oid_extensions import OAuthRequest
from velruse.providers.openidconsumer import OpenIDAuthenticationComplete
from velruse.providers.openidconsumer import OpenIDConsumer

YAHOO_OAUTH = 'https://api.login.yahoo.com/oauth/v2/get_token'
log = logging.getLogger(__name__)


class YahooAuthenticationComplete(OpenIDAuthenticationComplete):
    """Yahoo auth complete"""


def includeme(config):
    settings = config.registry.settings
    store = config.registry.get('velruse.openid_store')
    if not store and 'velruse.openid.store' not in settings:
        raise Exception("Missing 'velruse.openid.store' in config settings.")
    if not store:
        store = config.maybe_dotted(settings['velruse.openid.store'])()
        config.registry['velruse.openid_store'] = store
    realm = settings['velruse.openid.realm']
    consumer = YahooConsumer(
        storage=store,
        realm=realm,
        process_url='yahoo_process',
        oauth_key=settings.get('velruse.yahoo.consumer_key'),
        oauth_secret=settings.get('velruse.yahoo.consumer_secret'),
    )
    config.add_route("yahoo_login", "/yahoo/login")
    config.add_route("yahoo_process", "/yahoo/process",
                     use_global_views=True,
                     factory=consumer.process)
    config.add_view(consumer.login, route_name="yahoo_login")


class YahooConsumer(OpenIDConsumer):
    def __init__(self, oauth_key=None, oauth_secret=None,
                 request_attributes=None, *args, **kwargs):
        """Handle Google Auth

        This also handles making an OAuth request during the OpenID
        authentication.

        """
        super(YahooConsumer, self).__init__(*args, **kwargs)
        self.AuthenticationComplete = YahooAuthenticationComplete
        self.oauth_key = oauth_key
        self.oauth_secret = oauth_secret

    def _lookup_identifier(self, request, identifier):
        """Return the Yahoo OpenID directed endpoint"""
        return 'https://me.yahoo.com/'

    def _update_authrequest(self, request, authrequest):
        # Add on the Attribute Exchange for those that support that
        ax_request = ax.FetchRequest()
        for attrib in ['http://axschema.org/namePerson/friendly',
                       'http://axschema.org/namePerson',
                       'http://axschema.org/person/gender',
                       'http://axschema.org/pref/timezone',
                       'http://axschema.org/media/image/default',
                       'http://axschema.org/contact/email']:
            ax_request.add(ax.AttrInfo(attrib))
        authrequest.addExtension(ax_request)

        # Add OAuth request?
        if 'oauth' in request.params:
            oauth_request = OAuthRequest(consumer=self.oauth_key)
            authrequest.addExtension(oauth_request)
        return None

    def _get_access_token(self, request_token):
        consumer = oauth.Consumer(key=self.oauth_key, secret=self.oauth_secret)
        token = oauth.Token(key=request_token, secret='')
        client = oauth.Client(consumer, token)
        resp, content = client.request(YAHOO_OAUTH, "POST")
        if resp['status'] != '200':
            log.error("OAuth token validation failed. Status: %s, Content: %s",
                resp['status'], content)
            return None

        access_token = dict(parse_qs(content))
        print access_token

        return {'oauthAccessToken': access_token['oauth_token'],
                'oauthAccessTokenSecret': access_token['oauth_token_secret']}
