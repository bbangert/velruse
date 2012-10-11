"""Google Responder

A Google responder that authenticates against Google using OpenID, or
optionally can use OpenId+OAuth hybrid protocol to request access to
Google Apps using OAuth2.

"""
from __future__ import absolute_import

import logging
from json import loads
from urlparse import parse_qs

import oauth2 as oauth
from openid.extensions import ax

from pyramid.security import NO_PERMISSION_REQUIRED

from velruse.api import register_provider
from velruse.providers.oid_extensions import OAuthRequest
from velruse.providers.oid_extensions import UIRequest
from velruse.providers.openid import (
    attributes,
    OpenIDAuthenticationComplete,
    OpenIDConsumer,
)


log = logging.getLogger(__name__)

GOOGLE_OAUTH = 'https://www.google.com/accounts/OAuthGetAccessToken'


class GoogleAuthenticationComplete(OpenIDAuthenticationComplete):
    """Google auth complete"""

def includeme(config):
    config.add_directive('add_google_hybrid_login', add_google_login)

def add_google_login(config,
                     attrs=None,
                     realm=None,
                     storage=None,
                     consumer_key=None,
                     consumer_secret=None,
                     scope=None,
                     login_path='/login/google',
                     callback_path='/login/google/callback',
                     name='google'):
    """
    Add a Google login provider to the application using the OpenID+OAuth
    hybrid protocol.  This protocol can be configured for purely
    authentication by specifying only OpenID parameters. If you also wish
    to authorize your application to access the user's information you
    may specify OAuth credentials.

    - OpenID parameters
      + ``attrs``
      + ``realm``
      + ``storage``
    - OAuth parameters
      + ``consumer_key``
      + ``consumer_secret``
      + ``scope``
    """
    provider = GoogleConsumer(
        name,
        attrs,
        realm,
        storage,
        consumer_key,
        consumer_secret,
        scope)


    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)

class GoogleConsumer(OpenIDConsumer):
    openid_attributes = [
        'country', 'email', 'first_name', 'last_name', 'language',
    ]

    def __init__(self, name, attrs=None, realm=None, storage=None,
                 oauth_key=None, oauth_secret=None, oauth_scope=None):
        """Handle Google Auth

        This also handles making an OAuth request during the OpenID
        authentication.

        """
        OpenIDConsumer.__init__(self, name, 'google', realm, storage,
                                context=GoogleAuthenticationComplete)
        self.oauth_key = oauth_key
        self.oauth_secret = oauth_secret
        self.oauth_scope = oauth_scope
        if attrs is not None:
            self.openid_attributes = attrs

    def _lookup_identifier(self, request, identifier):
        """Return the Google OpenID directed endpoint"""
        return "https://www.google.com/accounts/o8/id"

    def _update_authrequest(self, request, authrequest):
        """Update the authrequest with Attribute Exchange and optionally OAuth

        To optionally request OAuth, the request POST must include an
        ``oauth_scope`` parameter that indicates what Google Apps should have
        access requested.

        """
        ax_request = ax.FetchRequest()
        for attr in self.openid_attributes:
            ax_request.add(ax.AttrInfo(attributes[attr], required=True))
        authrequest.addExtension(ax_request)

        # Add OAuth request?
        oauth_scope = self.oauth_scope
        if 'oauth_scope' in request.POST:
            oauth_scope = request.POST['oauth_scope']
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

    def _update_profile_data(self, request, profile, credentials):
        """Update the user data with profile information from Google Contacts

        This only works if the oauth_scope included access to Google Contacts
        i.e. the scope needs::

            http://www-opensocial.googleusercontent.com/api/people

        """
        if self.oauth_key is None:
            return

        # Create the consumer and client, make the request
        consumer = oauth.Consumer(self.oauth_key, self.oauth_secret)

        # Make a request with the data for more user info
        token = oauth.Token(key=credentials['oauthAccessToken'],
                            secret=credentials['oauthAccessTokenSecret'])
        client = oauth.Client(consumer, token)
        profile_url = \
            'https://www-opensocial.googleusercontent.com/api/people/@me/@self'
        resp, content = client.request(profile_url)
        if resp['status'] != '200':
            return
        data = loads(content)
        if 'entry' in data:
            profile.update(data['entry'])

            # Strip out the id and add it as the user id
            profile['accounts'][0]['userid'] = profile.pop('id', None)

    def _get_access_token(self, request_token):
        """Retrieve the access token if OAuth hybrid was used"""
        consumer = oauth.Consumer(key=self.oauth_key, secret=self.oauth_secret)
        token = oauth.Token(key=request_token, secret='')
        client = oauth.Client(consumer, token)
        resp, content = client.request(GOOGLE_OAUTH, "POST")
        if resp['status'] != '200':
            log.error("OAuth token validation failed. Status: %s, Content: %s",
                resp['status'], content)
            return

        access_token = dict(parse_qs(content))

        return {
            'oauthAccessToken': access_token['oauth_token'][0],
            'oauthAccessTokenSecret': access_token['oauth_token_secret'][0]
        }
