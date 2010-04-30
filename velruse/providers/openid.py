import logging

from openid import sreg
from openid.consumer import consumer
from openid.server import server
from routes import Mapper, URLGenerator
from webob import exc, Response

from ofcode.controllers.auth.utils import error_string
from ofcode.controllers.auth.utils import RouteResponder

log = logging.getLogger(__name__)


class OpenIDConsumer(RouteResponder):
    """OpenID Consumer for handling OpenID authentication
    
    This follows the same responder style of Marco apps. It is called
    with a WebOb Request, and responds with a WebOb Response.
    
    """
    map = Mapper()
    map.connect('login', '/login', method='login', requirements=dict(method='POST'))
    
    
    def __init__(self, storage, openid_store, end_point):
        """Create the OpenID Consumer"""
        self.storage = storage
        self.openid_store = openid_store
        self.end_point = end_point
    
    def login(self, req):
        openid_url = req.POST.get('openid_identifier')
        end_point = req.POST.get('end_point', self.end_point)
        if not openid_url:
            return self._error_redirect(0, end_point)

        oidconsumer = consumer.Consumer({}, self.openid_store)
        try:
            authrequest = oidconsumer.begin(openid_url)
        except consumer.DiscoveryFailure, exc:
            err_msg = str(exc[0])
            if 'No usable OpenID' in err_msg:
                failure_flash('Invalid OpenID URL')
            else:
                failure_flash('Timeout for OpenID URL')
            proper_abort(end_action)
        
        if authrequest is None:
            failure_flash('No OpenID services found for <code>%s</code>' % openid_url)
            proper_abort(end_action)
        
        if end_action == 'register':
            sreg_request = sreg.SRegRequest(
                required=['fullname', 'email', 'timezone'],
                optional=['language']
            )
            authrequest.addExtension(sreg_request)
            session['openid_action'] = 'register'
        elif 'openid_action' in session:
            del session['openid_action']
        
        trust_root = url('home', qualified=True)
        return_to = url('openid_process', qualified=True)
        
        # OpenID 2.0 lets Providers request POST instead of redirect, this
        # checks for such a request.
        if authrequest.shouldSendRedirect():
            redirect_url = authrequest.redirectURL(realm=trust_root, 
                                                   return_to=return_to, 
                                                   immediate=False)
            self.my_cache.set_value(key=session.id, value=self.openid_session, expiretime=300)
            redirect(url(redirect_url))
        else:
            form_html = authrequest.formMarkup(
                realm=trust_root, return_to=return_to, immediate=False,
                form_tag_attrs={'id':'openid_message'})
            self.my_cache.set_value(key=session.id, value=self.openid_session, expiretime=300)
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
