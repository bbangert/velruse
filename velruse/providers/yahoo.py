from __future__ import absolute_import

import logging
from urlparse import parse_qs

import oauth2 as oauth
from openid.extensions import ax

from pyramid.security import NO_PERMISSION_REQUIRED

from velruse.api import register_provider
from velruse.providers.oid_extensions import OAuthRequest
from velruse.providers.openid import (
    OpenIDAuthenticationComplete,
    OpenIDConsumer,
)


log = logging.getLogger(__name__)

YAHOO_OAUTH = 'https://api.login.yahoo.com/oauth/v2/get_token'


class YahooAuthenticationComplete(OpenIDAuthenticationComplete):
    """Yahoo auth complete"""


def includeme(config):
    config.add_directive('add_yahoo_login', add_yahoo_login)


def add_yahoo_login(config,
                    realm=None,
                    storage=None,
                    consumer_key=None,
                    consumer_secret=None,
                    login_path='/login/yahoo',
                    callback_path='/login/yahoo/callback',
                    name='yahoo'):
    """
    Add a Yahoo login provider to the application.

    OpenID parameters: realm, storage

    OAuth parameters: consumer_key, consumer_secret
    """
    provider = YahooConsumer(name, realm, storage,
                             consumer_key, consumer_secret)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class YahooConsumer(OpenIDConsumer):
    def __init__(self, name, realm=None, storage=None,
                 oauth_key=None, oauth_secret=None):
        """Handle Yahoo Auth

        This also handles making an OAuth request during the OpenID
        authentication.

        """
        OpenIDConsumer.__init__(self, name, 'yahoo', realm, storage,
                                context=YahooAuthenticationComplete)
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
        if 'oauth' in request.POST:
            oauth_request = OAuthRequest(consumer=self.oauth_key)
            authrequest.addExtension(oauth_request)

    def _get_access_token(self, request_token):
        consumer = oauth.Consumer(key=self.oauth_key, secret=self.oauth_secret)
        token = oauth.Token(key=request_token, secret='')
        client = oauth.Client(consumer, token)
        resp, content = client.request(YAHOO_OAUTH, "POST")
        if resp['status'] != '200':
            log.error("OAuth token validation failed. Status: %s, Content: %s",
                resp['status'], content)
            return

        access_token = dict(parse_qs(content))

        return {'oauthAccessToken': access_token['oauth_token'],
                'oauthAccessTokenSecret': access_token['oauth_token_secret']}
