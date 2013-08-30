from __future__ import absolute_import

from openid.extensions import ax

import requests
from requests_oauthlib import OAuth1

from pyramid.security import NO_PERMISSION_REQUIRED

from ..api import register_provider
from ..compat import parse_qsl

from .oid_extensions import OAuthRequest
from .oid_extensions import UIRequest
from .openid import (
    attributes,
    OpenIDAuthenticationComplete,
    OpenIDConsumer,
)


log = __import__('logging').getLogger(__name__)


GOOGLE_OAUTH = 'https://www.google.com/accounts/OAuthGetAccessToken'


class GoogleAuthenticationComplete(OpenIDAuthenticationComplete):
    """Google auth complete"""

def includeme(config):
    """Activate the ``google_hybrid`` Pyramid plugin via
    ``config.include('velruse.providers.google_hybrid')``. After included,
    a new method will be available to configure new providers.

    ``config.add_google_hybrid_login()``
        See :func:`~velruse.providers.google_hybrid.add_google_login`
        for the supported options.

    """
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
        OpenIDConsumer.__init__(self, name, 'google_hybrid', realm, storage,
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

    def _update_profile_data(self, request, profile, credentials):
        """Update the user data with profile information from Google Contacts

        This only works if the oauth_scope included access to Google Contacts
        i.e. the scope needs::

            http://www-opensocial.googleusercontent.com/api/people

        """
        if self.oauth_key is None:
            return

        # setup oauth for general api calls
        oauth = OAuth1(
            self.oauth_key,
            client_secret=self.oauth_secret,
            resource_owner_key=credentials['oauthAccessToken'],
            resource_owner_secret=credentials['oauthAccessTokenSecret'])

        profile_url = \
            'https://www-opensocial.googleusercontent.com/api/people/@me/@self'
        resp = requests.get(profile_url, auth=oauth)
        if resp.status_code != 200:
            return
        data = resp.json()
        if 'entry' in data:
            profile.update(data['entry'])

            # Strip out the id and add it as the user id
            profile['accounts'][0]['userid'] = profile.pop('id', None)

    def _get_access_token(self, request_token):
        """Retrieve the access token if OAuth hybrid was used"""
        oauth = OAuth1(
            self.oauth_key,
            client_secret=self.oauth_secret,
            resource_owner_key=request_token)

        resp = requests.post(GOOGLE_OAUTH, auth=oauth)
        if resp.status_code != 200:
            log.error(
                'OAuth token validation failed. Status: %d, Content: %s',
                resp.status_code, resp.content)
        else:
            access_token = dict(parse_qsl(resp.text))
            return {
                'oauthAccessToken': access_token['oauth_token'],
                'oauthAccessTokenSecret': access_token['oauth_token_secret'],
            }
