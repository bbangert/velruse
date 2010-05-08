import logging
import re

from openid import extension
from openid.consumer import consumer
from openid.extensions import ax
from openid.extensions import sreg
from openid.oidutil import autoSubmitHTML
from routes import Mapper
from webob import Response
import webob.exc as exc

import velruse.utils as utils

log = logging.getLogger(__name__)

__all__ = ['OpenIDResponder']


# Setup our attribute objects that we'll be requesting
ax_attributes = dict(
    nickname = ax.AttrInfo('http://axschema.org/namePerson/friendly', alias='nickname'),
    email = ax.AttrInfo('http://axschema.org/contact/email', alias='email'),
    full_name = ax.AttrInfo('http://axschema.org/namePerson', alias='full_name'),
    birthday = ax.AttrInfo('http://axschema.org/birthDate', alias='birthday'),
    gender = ax.AttrInfo('http://axschema.org/person/gender', alias='gender'),
    postal_code = ax.AttrInfo('http://axschema.org/contact/postalCode/home', alias='postal_code'),
    country = ax.AttrInfo('http://axschema.org/contact/country/home', alias='country'),
    timezone = ax.AttrInfo('http://axschema.org/pref/timezone', alias='timezone'),
    language = ax.AttrInfo('http://axschema.org/pref/language', alias='language'),
    name_prefix = ax.AttrInfo('http://axschema.org/namePerson/prefix', alias='name_prefix'),
    first_name = ax.AttrInfo('http://axschema.org/namePerson/first', alias='first_name'),
    last_name = ax.AttrInfo('http://axschema.org/namePerson/last', alias='last_name'),
    middle_name = ax.AttrInfo('http://axschema.org/namePerson/middle', alias='middle_name'),
    name_suffix = ax.AttrInfo('http://axschema.org/namePerson/suffix', alias='name_suffix'),
    web_page = ax.AttrInfo('http://axschema.org/contact/web/default', alias='web'),
)

# Translation dict for AX attrib names to sreg equiv
trans_dict = dict(
    full_name = 'fullname',
    birthday = 'dob',
    postal_code = 'postcode',
)

class AttribAccess(object):
    def __init__(self, sreg_resp, ax_resp):
        self.sreg_resp = sreg_resp or {}
        self.ax_resp = ax_resp or ax.AXKeyValueMessage()
    
    def get(self, key, ax_only=False):
        # First attempt to fetch it from AX
        v = self.ax_resp.getSingle(ax_attributes[key].type_uri)
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
    
    ud = {'identifier': identifier}
    if 'google.com' in identifier:
        ud['providerName'] = 'Google'
    elif 'yahoo.com' in identifier:
        ud['providerName'] = 'Yahoo'
    else:
        ud['providerName'] = 'OpenID'
    
    # Sort out the display name and preferred username
    if ud['providerName'] == 'Google':
        # Extract the first bit as the username since Google doesn't return
        # any usable nickname info
        email = attribs.get('email')
        first = re.match('(^.*?)@', email).groups()[0]
        ud['preferredUsername'] = first
    else:
        pref_name = attribs.get('nickname')
        if pref_name:
            ud['preferredUsername'] = pref_name
    
    # We trust that Google and Yahoo both verify their email addresses
    if ud['providerName'] in ['Google', 'Yahoo']:
        email = attribs.get('email', ax_only=True)
        if email:
            ud['verifiedEmail'] = email
    
    # Parse through the name parts, assign the properly if present
    name = {}
    name_keys = ['name_prefix', 'first_name', 'middle_name', 'last_name', 'name_suffix']
    pcard_map = {'first_name': 'givenName', 'middle_name': 'middleName', 'last_name': 'familyName',
                 'name_prefix': 'honorificPrefix', 'name_suffix': 'honorificSuffix'}
    full_name_vals = []
    for part in name_keys:
        val = attribs.get(part)
        if val:
            full_name_vals.append(val)
            name[pcard_map[part]] = val
    full_name = ' '.join(full_name_vals).strip()
    if not full_name:
        full_name = attribs.get('full_name')

    if full_name:
        name['formatted'] = full_name
    
    if name:
        ud['name'] = name
    
    display_name = full_name or ud.get('preferredUsername')
    if display_name:
        ud['displayName'] = display_name
    
    web_page = attribs.get('web_page')
    if web_page:
        ud['urls'] = [web_page]
    
    for k in ['gender', 'birthday']:
        val = attribs.get(k)
        if val:
            ud[k] = val
    return ud


class UIRequest(extension.Extension):
    """OpenID UI extension"""
    ns_uri = 'http://specs.openid.net/extensions/ui/1.0'
    ns_alias = 'ui'
    
    def __init__(self, mode=None, icon=None):
        self.mode = mode
        self.icon = icon
    
    def getExtensionArgs(self):
        return {'mode': self.mode, 'icon': self.icon}


class OpenIDResponder(utils.RouteResponder):
    """OpenID Consumer for handling OpenID authentication
    
    This follows the same responder style of Marco apps. It is called
    with a WebOb Request, and responds with a WebOb Response.
    
    """
    map = Mapper()
    map.connect('login', '/auth', action='login', requirements=dict(method='POST'))
    map.connect('process', '/process', action='process')
    
    def __init__(self, storage, openid_store, end_point, realm):
        """Create the OpenID Consumer"""
        self.storage = storage
        self.openid_store = openid_store
        self.realm = realm
        self.end_point = end_point
        self.log_debug = logging.DEBUG >= log.getEffectiveLevel()
    
    def login(self, req):
        log_debug = self.log_debug
        if log_debug:
            log.debug('Handling OpenID login')
        
        # Load default parameters that all Auth Responders take
        use_popup = req.POST.get('use_popup', 'true').lower() == 'true'

        openid_url = req.POST.get('openid_identifier')
        if not openid_url:
            return self._error_redirect(0)
        
        openid_session = {}
        oidconsumer = consumer.Consumer(openid_session, self.openid_store)
        
        try:
            if openid_url == 'google.com':
                openid_url = 'https://www.google.com/accounts/o8/id'
            authrequest = oidconsumer.begin(openid_url)
        except consumer.DiscoveryFailure:
            return self._error_redirect(1)
        
        if authrequest is None:
            return self._error_redirect(1)
        
        # Form the Simple Reg request
        sreg_request = sreg.SRegRequest(
            optional=['nickname', 'email', 'fullname', 'dob', 'gender', 'postcode',
                      'country', 'language', 'timezone'],
        )
        authrequest.addExtension(sreg_request)
        
        # Add on the Attribute Exchange for those that support that
        ax_request = ax.FetchRequest()
        for attrib in ax_attributes.values():
            ax_request.add(attrib)
        
        if 'google.com' in openid_url.lower():
            # We need to require these for Google to actually return them
            for attr in ax_request.requested_attributes.values():
                if attr.alias in ['country', 'email', 'first_name', 'last_name', 'language']:
                    attr.required = True
        authrequest.addExtension(ax_request)
        
        # Do we want a popup?
        if use_popup:
            ui_request = UIRequest(mode='popup', icon='true')
            authrequest.addExtension(ui_request)
        
        return_to = req.link('process', qualified=True)
        
        # Ensure our session is saved for the id to persist
        req.session.save()
        
        # OpenID 2.0 lets Providers request POST instead of redirect, this
        # checks for such a request.
        if authrequest.shouldSendRedirect():
            redirect_url = authrequest.redirectURL(realm=self.realm, 
                                                   return_to=return_to, 
                                                   immediate=False)
            self.storage.store(req.session.id, openid_session, expires=300)
            return exc.HTTPFound(location=redirect_url)
        else:
            html = authrequest.htmlMarkup(realm=self.realm, return_to=return_to, 
                                          immediate=False)
            self.storage.store(req.session.id, openid_session, expires=300)
            return Response(body=html)
    
    def process(self, req):
        """Handle incoming redirect from OpenID Provider"""
        log_debug = self.log_debug
        if log_debug:
            log.debug('Handling processing of response from server')
        
        openid_session = self.storage.retrieve(req.session.id)
        if not openid_session:
            return self._error_redirect(1)
        
        # Setup the consumer and parse the information coming back
        oidconsumer = consumer.Consumer(openid_session, self.openid_store)
        info = oidconsumer.complete(req.params, req.link('process', qualified=True))
        
        if info.status in [consumer.FAILURE, consumer.CANCEL]:
            return self._error_redirect(2)
        elif info.status == consumer.SUCCESS:
            openid_identity = info.identity_url
            if info.endpoint.canonicalID:
                # If it's an i-name, use the canonicalID as its secure even if
                # the old one is compromised
                openid_identity = info.endpoint.canonicalID
            
            user_data = extract_openid_data(identifier=openid_identity, 
                                            sreg_resp=sreg.SRegResponse.fromSuccessResponse(info),
                                            ax_resp=ax.FetchResponse.fromSuccessResponse(info))
            result_data = {'status': 'ok', 'profile': user_data}
            
            # Delete the temporary token data used for the OpenID auth
            self.storage.delete(req.session.id)
            
            # Generate the token, store the extracted user-data for 5 mins, and send back
            token = utils.generate_token()
            self.storage.store(token, result_data, expires=300)
            form_html = utils.redirect_form(self.end_point, token)
            return Response(body=autoSubmitHTML(form_html))
        else:
            return self._error_redirect(1)
