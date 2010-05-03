import logging

from openid.consumer import consumer
from openid.extensions import ax
from openid.extensions import sreg
from openid.server import server
from routes import Mapper, URLGenerator
from webob import exc, Response

from ofcode.controllers.auth.utils import error_string
from ofcode.controllers.auth.utils import RouteResponder

log = logging.getLogger(__name__)

# Setup our attribute objects that we'll be requesting
# First the simple registration attributes
simplereg_attributes = dict(
    username = ax.AttrInfo('http://axschema.org/namePerson/friendly', alias='username'),
    email = ax.AttrInfo('http://axschema.org/contact/email', alias='email'),
    full_name = ax.AttrInfo('http://axschema.org/namePerson', alias='full_name'),
    birth_date = ax.AttrInfo('http://axschema.org/birthDate', alias='birth_date'),
    gender = ax.AttrInfo('http://axschema.org/person/gender', alias='gender'),
    postal_code = ax.AttrInfo('http://axschema.org/contact/postalCode/home', alias='postal_code'),
    country = ax.AttrInfo('http://axschema.org/contact/country/home', alias='country'),
    timezone = ax.AttrInfo('http://axschema.org/pref/language', alias='timezone'),
)

# Some common additional attributes
extended_attributes = dict(
    name_prefix = ax.AttrInfo('http://axschema.org/namePerson/prefix', alias='name_prefix'),
    firstname = ax.AttrInfo('http://axschema.org/namePerson/first', alias='firstname'),
    lastname = ax.AttrInfo('http://axschema.org/namePerson/last', alias='lastname'),
    middle_name = ax.AttrInfo('http://axschema.org/namePerson/middle', alias='middle_name'),
    name_suffix = ax.AttrInfo('http://axschema.org/namePerson/suffix', alias='name_suffix'),
)


class OpenIDConsumer(RouteResponder):
    """OpenID Consumer for handling OpenID authentication
    
    This follows the same responder style of Marco apps. It is called
    with a WebOb Request, and responds with a WebOb Response.
    
    """
    map = Mapper()
    map.connect('login', '/login', method='login', requirements=dict(method='POST'))
    map.connect('process', '/process', method='process')
    
    def __init__(self, storage, openid_store, end_point, realm):
        """Create the OpenID Consumer"""
        self.storage = storage
        self.openid_store = openid_store
        self.realm = realm
        self.end_point = end_point
    
    def login(self, req):
        # Load default parameters that all Auth Responders take
        use_popup = req.POST.get('use_popup', '').lower() == 'true'
        end_point = req.POST.get('end_point', self.end_point)

        openid_url = req.POST.get('openid_identifier')
        if not openid_url:
            return self._error_redirect(0, end_point)
        
        openid_session = {}
        oidconsumer = consumer.Consumer(openid_session, self.openid_store)
        
        try:
            if openid_url == 'google.com':
                openid_url = 'https://www.google.com/accounts/o8/id'
            authrequest = oidconsumer.begin(openid_url)
        except consumer.DiscoveryFailure, exc:
            return self._error_redirect(1, end_point)
        
        if authrequest is None:
            return self._error_redirect(1, end_point)
        
        # Form the Simple Reg request
        sreg_request = sreg.SRegRequest(
            required=['fullname', 'email', 'timezone'],
            optional=['language']
        )
        authrequest.addExtension(sreg_request)
        
        # Add on the Attribute Exchange for those that support that
        ax_request = ax.FetchRequest()
        for attrib in simplereg_attributes.values() + extended_attributes.values():
            ax_request.add(attrib)
        
        if openid_url.lower() == 'google.com':
            for attr in ax_request.requested_attributes.values():
                if attr.alias in ['country', 'email', 'firstname', 'lastname', 'language']:
                    attr.required = True
        authrequest.addExtension(ax_request)
            
        
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
            form_html = authrequest.formMarkup(
                realm=self.realm, return_to=return_to, immediate=False,
                form_tag_attrs={'id':'openid_message'})
            self.storage.store(req.session.id, openid_session, expires=300)
            return form_html
    
    def process(self):
        """Handle incoming redirect from OpenID Provider"""
        end_action = session.get('openid_action', 'login')
        
        oidconsumer = consumer.Consumer(self.openid_session, app_globals.openid_store)
        info = oidconsumer.complete(request.params, url('openid_process', qualified=True))
        if info.status == consumer.FAILURE and info.identity_url:
            fmt = "Verification of %s failed: %s"
            failure_flash(fmt % (info.identity_url, info.message))
        elif info.status == consumer.SUCCESS:
            openid_identity = info.identity_url
            if info.endpoint.canonicalID:
                # If it's an i-name, use the canonicalID as its secure even if
                # the old one is compromised
                openid_identity = info.endpoint.canonicalID
            
            # We've now verified a successful OpenID login, time to determine
            # how to dispatch it
            
            # First save their identity in the session, as several pages use 
            # this data
            session['openid_identity'] = openid_identity
            
            # Save off the session
            session.save()
            
            # First, if someone already has this openid, we log them in if
            # they've verified their email, otherwise we inform them to verify
            # their email address first
            users = list(Human.by_openid(self.db)[openid_identity])
            if users:
                user = users[0]
                if user.email_token:
                    failure_flash('You must verify your email before signing in.')
                    redirect(url('account_login'))
                else:
                    user.process_login()
                    success_flash('You have logged into PylonsHQ')
                    if session.get('redirect'):
                        redir_url = session.pop('redirect')
                        session.save()
                        redirect(url(redir_url))
                    redirect(url('home'))
            
            # Second, if this is a registration request, present the rest of
            # registration process
            if session.get('openid_action', '') == 'register':
                sreg_response = sreg.SRegResponse.fromSuccessResponse(info)
                results = {}
                
                # Just in case the user didn't provide sreg details
                if sreg_response:
                    results['displayname'] = sreg_response.get('fullname')
                    results['timezone'] = sreg_response.get('timezone')
                    results['email_address'] = sreg_response.get('email')
                c.defaults = results
                c.openid = openid_identity
                return render('/accounts/register.mako')
            
            # The last option possible, is that the user is associating this
            # OpenID account with an existing account
            c.openid = openid_identity
            return render('/accounts/associate.mako')
        elif info.status == consumer.CANCEL:
            failure_flash('Verification cancelled')
        elif info.status == consumer.SETUP_NEEDED:
            if info.setup_url:
                c.message = '<a href=%s>Setup needed</a>' % info.setup_url
            else:
                # This means auth didn't succeed, but you're welcome to try
                # non-immediate mode.
                failure_flash('Setup needed')
        else:
            failure_flash('Verification failed.')
        session.delete()
        proper_abort(end_action)
