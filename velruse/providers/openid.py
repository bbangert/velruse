from __future__ import absolute_import

import datetime
import re
import logging

from openid.consumer import consumer
from openid.extensions import ax
from openid.extensions import sreg

from pyramid.request import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

from velruse.api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from velruse.exceptions import MissingParameter
from velruse.exceptions import ThirdPartyFailure


log = logging.getLogger(__name__)

# Setup our attribute objects that we'll be requesting
ax_attributes = dict(
    nickname='http://axschema.org/namePerson/friendly',
    email='http://axschema.org/contact/email',
    full_name='http://axschema.org/namePerson',
    birthday='http://axschema.org/birthDate',
    gender='http://axschema.org/person/gender',
    postal_code='http://axschema.org/contact/postalCode/home',
    country='http://axschema.org/contact/country/home',
    timezone='http://axschema.org/pref/timezone',
    language='http://axschema.org/pref/language',
    name_prefix='http://axschema.org/namePerson/prefix',
    first_name='http://axschema.org/namePerson/first',
    last_name='http://axschema.org/namePerson/last',
    middle_name='http://axschema.org/namePerson/middle',
    name_suffix='http://axschema.org/namePerson/suffix',
    web='http://axschema.org/contact/web/default',
    thumbnail='http://axschema.org/media/image/default',
)

#Change names later to make things a little bit clearer
alternate_ax_attributes = dict(
    nickname='http://schema.openid.net/namePerson/friendly',
    email='http://schema.openid.net/contact/email',
    full_name='http://schema.openid.net/namePerson',
    birthday='http://schema.openid.net/birthDate',
    gender='http://schema.openid.net/person/gender',
    postal_code='http://schema.openid.net/contact/postalCode/home',
    country='http://schema.openid.net/contact/country/home',
    timezone='http://schema.openid.net/pref/timezone',
    language='http://schema.openid.net/pref/language',
    name_prefix='http://schema.openid.net/namePerson/prefix',
    first_name='http://schema.openid.net/namePerson/first',
    last_name='http://schema.openid.net/namePerson/last',
    middle_name='http://schema.openid.net/namePerson/middle',
    name_suffix='http://schema.openid.net/namePerson/suffix',
    web='http://schema.openid.net/contact/web/default',
)

# Translation dict for AX attrib names to sreg equiv
trans_dict = dict(
    full_name='fullname',
    birthday='dob',
    postal_code='postcode',
)

attributes = ax_attributes


class OpenIDAuthenticationComplete(AuthenticationComplete):
    """OpenID auth complete"""


def includeme(config):
    config.add_directive('add_openid_login', add_openid_login)


def add_openid_login(config,
                     realm=None,
                     storage=None,
                     login_path='/login/openid',
                     callback_path='/login/openid/callback',
                     name='openid'):
    """
    Add a OpenID login provider to the application.

    `storage` should be an object conforming to the
    `openid.store.interface.OpenIDStore` protocol. This will default
    to `openid.store.memstore.MemoryStore`.
    """
    provider = OpenIDConsumer(name, realm=realm, storage=storage)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class OpenIDConsumer(object):
    """OpenID Consumer base class

    Providors using specialized OpenID based authentication subclass this.

    """
    def __init__(self,
                 name,
                 _type=None,
                 realm=None,
                 storage=None,
                 context=AuthenticationComplete):
        self.openid_store = storage
        self.name = name
        self.type = _type
        self.context = context
        self.realm_override = realm

        self.login_route = 'velruse.%s-url' % name
        self.callback_route = 'velruse.%s-callback' % name

    _openid_store = None

    def _get_openid_store(self):
        if self._openid_store is None:
            from openid.store.memstore import MemoryStore
            self._openid_store = MemoryStore()
        return self._openid_store

    def _set_openid_store(self, val):
        self._openid_store = val

    openid_store = property(_get_openid_store, _set_openid_store)

    def _get_realm(self, request):
        if self.realm_override is not None:
            return self.realm_override
        return request.host_url

    def _lookup_identifier(self, request, identifier):
        """Extension point for inherited classes that want to change or set
        a default identifier"""
        return identifier

    def _update_authrequest(self, request, authrequest):
        """Update the authrequest with the default extensions and attributes
        we ask for

        This method doesn't need to return anything, since the extensions
        should be added to the authrequest object itself.

        """
        # Add on the Attribute Exchange for those that support that
        ax_request = ax.FetchRequest()
        for attrib in attributes.values():
            ax_request.add(ax.AttrInfo(attrib))
        authrequest.addExtension(ax_request)

        # Form the Simple Reg request
        sreg_request = sreg.SRegRequest(
            optional=['nickname', 'email', 'fullname', 'dob', 'gender',
                      'postcode', 'country', 'language', 'timezone'],
        )
        authrequest.addExtension(sreg_request)

    def _get_access_token(self, request_token):
        """Called to exchange a request token for the access token

        This method doesn't by default return anything, other OpenID+Oauth
        consumers should override it to do the appropriate lookup for the
        access token, and return the access token.

        """

    def login(self, request):
        log.debug('Handling OpenID login')

        # Load default parameters that all Auth Responders take
        openid_url = request.params.get('openid_identifier')

        # Let inherited consumers alter the openid identifier if desired
        openid_url = self._lookup_identifier(request, openid_url)

        if not openid_url:
            log.error('Velruse: no openid_url')
            raise MissingParameter('No openid_identifier was found')

        openid_session = {}
        oidconsumer = consumer.Consumer(openid_session, self.openid_store)

        try:
            log.debug('About to try OpenID begin')
            authrequest = oidconsumer.begin(openid_url)
        except consumer.DiscoveryFailure:
            log.debug('OpenID begin DiscoveryFailure')
            raise

        if authrequest is None:
            log.debug('OpenID begin returned empty')
            raise ThirdPartyFailure("OpenID begin returned nothing")

        log.debug('Updating authrequest')

        # Update the authrequest
        self._update_authrequest(request, authrequest)

        realm = self._get_realm(request)
        # TODO: add a csrf check to the return_to URL
        return_to = request.route_url(self.callback_route)
        request.session['openid_session'] = openid_session

        # OpenID 2.0 lets Providers request POST instead of redirect, this
        # checks for such a request.
        if authrequest.shouldSendRedirect():
            log.debug('About to initiate OpenID redirect')
            redirect_url = authrequest.redirectURL(
                realm=realm,
                return_to=return_to,
                immediate=False)
            return HTTPFound(location=redirect_url)
        else:
            log.debug('About to initiate OpenID POST')
            html = authrequest.htmlMarkup(
                realm=realm,
                return_to=return_to,
                immediate=False)
            return Response(body=html)

    def _update_profile_data(self, request, user_data, credentials):
        """Update the profile data using an OAuth request to fetch more data"""

    def callback(self, request):
        """Handle incoming redirect from OpenID Provider"""
        log.debug('Handling processing of response from server')

        openid_session = request.session.get('openid_session', None)
        if not openid_session:
            raise ThirdPartyFailure("No OpenID Session has begun.")

        # Delete the temporary token data used for the OpenID auth
        del request.session['openid_session']

        # Setup the consumer and parse the information coming back
        oidconsumer = consumer.Consumer(openid_session, self.openid_store)
        return_to = request.route_url(self.callback_route)
        info = oidconsumer.complete(request.params, return_to)

        if info.status in [consumer.FAILURE, consumer.CANCEL]:
            return AuthenticationDenied("OpenID failure",
                                        provider_name=self.name,
                                        provider_type=self.type)
        elif info.status == consumer.SUCCESS:
            openid_identity = info.identity_url
            if info.endpoint.canonicalID:
                # If it's an i-name, use the canonicalID as its secure even if
                # the old one is compromised
                openid_identity = info.endpoint.canonicalID

            user_data = extract_openid_data(
                identifier=openid_identity,
                sreg_resp=sreg.SRegResponse.fromSuccessResponse(info),
                ax_resp=ax.FetchResponse.fromSuccessResponse(info)
            )
            # Did we get any OAuth info?
            oauth = info.extensionResponse(
                'http://specs.openid.net/extensions/oauth/1.0', False
            )
            cred = {}
            if oauth and 'request_token' in oauth:
                access_token = self._get_access_token(oauth['request_token'])
                if access_token:
                    cred.update(access_token)

                # See if we need to update our profile data with an OAuth call
                self._update_profile_data(request, user_data, cred)

            return self.context(profile=user_data,
                                credentials=cred,
                                provider_name=self.name,
                                provider_type=self.type)
        else:
            raise ThirdPartyFailure("OpenID failed.")


class AttribAccess(object):
    """Uniform attribute accessor for Simple Reg and Attribute Exchange
    values"""
    def __init__(self, sreg_resp, ax_resp):
        self.sreg_resp = sreg_resp or {}
        self.ax_resp = ax_resp or ax.AXKeyValueMessage()

    def get(self, key, ax_only=False):
        """Get a value from either Simple Reg or AX"""
        # First attempt to fetch it from AX
        v = self.ax_resp.getSingle(attributes[key])
        if v:
            return v
        if ax_only:
            return None

        # Translate the key if needed
        if key in trans_dict:
            key = trans_dict[key]

        # Don't attempt to fetch keys that aren't valid sreg fields
        if key not in sreg.data_fields:
            return None

        return self.sreg_resp.get(key)


def extract_openid_data(identifier, sreg_resp, ax_resp):
    """Extract the OpenID Data from Simple Reg and AX data

    This normalizes the data to the appropriate format.

    """
    attribs = AttribAccess(sreg_resp, ax_resp)

    account = {}
    accounts = [account]

    ud = {'accounts': accounts}
    if 'google.com' in identifier:
        account['domain'] = 'google.com'
    elif 'yahoo.com' in identifier:
        account['domain'] = 'yahoo.com'
    elif 'aol.com' in identifier:
        account['domain'] = 'aol.com'
    else:
        account['domain'] = 'openid.net'
    account['username'] = identifier

    # Sort out the display name and preferred username
    if account['domain'] == 'google.com':
        # Extract the first bit as the username since Google doesn't return
        # any usable nickname info
        email = attribs.get('email')
        if email:
            ud['preferredUsername'] = re.match('(^.*?)@', email).groups()[0]
    else:
        ud['preferredUsername'] = attribs.get('nickname')

    # We trust that Google and Yahoo both verify their email addresses
    if account['domain'] in ['google.com', 'yahoo.com']:
        ud['verifiedEmail'] = attribs.get('email', ax_only=True)
    else:
        ud['emails'] = [attribs.get('email')]

    # Parse through the name parts, assign the properly if present
    name = {}
    name_keys = ['name_prefix', 'first_name', 'middle_name', 'last_name',
                 'name_suffix']
    pcard_map = {'first_name': 'givenName', 'middle_name': 'middleName',
                 'last_name': 'familyName',
                 'name_prefix': 'honorificPrefix',
                 'name_suffix': 'honorificSuffix'}
    full_name_vals = []
    for part in name_keys:
        val = attribs.get(part)
        if val:
            full_name_vals.append(val)
            name[pcard_map[part]] = val
    full_name = ' '.join(full_name_vals).strip()
    if not full_name:
        full_name = attribs.get('full_name')

    name['formatted'] = full_name
    ud['name'] = name

    ud['displayName'] = full_name or ud.get('preferredUsername')

    urls = attribs.get('web')
    if urls:
        ud['urls'] = [urls]

    gender = attribs.get('gender')
    if gender:
        ud['gender'] = {'M': 'male', 'F': 'female'}.get(gender)

    birthday = attribs.get('birthday')
    if birthday:
        try:
            ud['birthday'] = datetime.datetime.strptime(
                    birthday, '%Y-%m-%d').date()
        except ValueError:
            pass

    thumbnail = attribs.get('thumbnail')
    if thumbnail:
        ud['photos'] = [{'type': 'thumbnail', 'value': thumbnail}]
        ud['thumbnailUrl'] = thumbnail

    # Now strip out empty values
    for k, v in ud.items():
        if not v or (isinstance(v, list) and not v[0]):
            del ud[k]

    return ud
