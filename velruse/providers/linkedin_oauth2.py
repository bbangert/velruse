import uuid

from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

import requests

from ..api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from ..exceptions import CSRFError
from ..exceptions import ThirdPartyFailure
from ..settings import ProviderSettings
from ..utils import flat_url

AUTH_URL = "https://www.linkedin.com/uas/oauth2/authorization"
ACCESS_URL = "https://www.linkedin.com/uas/oauth2/accessToken"

class LinkedinAuthenticationComplete(AuthenticationComplete):
    """Google OAuth 2.0 auth complete"""

def includeme(config):
    """Activate the ``linkedin_oauth2`` Pyramid plugin via
    ``config.include('velruse.providers.linkedin_oauth2')``. After included,
    two new methods will be available to configure new providers.

    ``config.add_linkedin_oauth2_login()``
        See :func:`~velruse.providers.linkedin_oauth2.add_linkedin_login`
        for the supported options.

    ``config.add_linkedin_oauth2_login_from_settings()``

    """
    config.add_directive('add_linkedin_oauth2_login', add_linkedin_login)
    config.add_directive('add_linkedin_oauth2_login_from_settings',
                         add_linkedin_login_from_settings)

def add_linkedin_login_from_settings(config, prefix='velruse.linkedin.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    config.add_linkedin_oauth2_login(**p.kwargs)

def add_linkedin_login(config,
                     consumer_key=None,
                     consumer_secret=None,
                     scope='',
                     login_path='/login/linkedin',
                     callback_path='/login/linkedin/callback',
                     name='linkedin_oauth2'):
    """
    Add a Linkedin login provider to the application supporting the new
    OAuth2 protocol.
    """
    provider = LinkedinOAuth2Provider(
        name,
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

class LinkedinOAuth2Provider(object):

    def __init__(self,
                 name,
                 consumer_key,
                 consumer_secret,
                 scope):
        self.name = name
        self.type = 'linkedin_oauth2'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope
        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a Linkedin login"""
        #Overwrites scope from settings if found in login form
        scope = request.POST.get('scope', self.scope) 
        request.session['velruse.state'] = state = uuid.uuid4().hex

        auth_url = flat_url(
            AUTH_URL,
            scope=scope,
            response_type='code',
            client_id=self.consumer_key,
            redirect_uri=request.route_url(self.callback_route),
            state=state)
        return HTTPFound(location=auth_url)

    def callback(self, request):
        """Process the Linkedin redirect"""
        sess_state = request.session.pop('velruse.state', None)
        req_state = request.GET.get('state')
        if not sess_state or sess_state != req_state:
            raise CSRFError(
                'CSRF Validation check failed. Request state {req_state} is '
                'not the same as session state {sess_state}'.format(
                    req_state=req_state,
                    sess_state=sess_state
                )
            )
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error', 'No reason provided.')
            description = request.GET.get('error_description', 'No description provided.')
            return AuthenticationDenied(reason='Error: %s, Error description: %s' % (reason, description),
                                        provider_name=self.name,
                                        provider_type=self.type)

        # Now retrieve the access token with the code
        r = requests.post(
            ACCESS_URL,
            dict(client_id=self.consumer_key,
                 client_secret=self.consumer_secret,
                 redirect_uri=request.route_url(self.callback_route),
                 code=code,
                 grant_type='authorization_code')
        )
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        token_data = r.json()
        access_token = token_data['access_token']
        expires_in = token_data['expires_in']

        # Retrieve profile data if scopes allow
        profile_url = 'https://api.linkedin.com/v1/people/~'
        profile_url += (':(first-name,last-name,id,picture-url,email-address)')
        profile = {}
        user_url = flat_url(
            profile_url,
            format='json',
            oauth2_access_token=access_token)
        r = requests.get(user_url)

        if r.status_code == 200:
            data = r.json()
            profile['displayName'] = u'%s %s' % (data['firstName'], data['lastName'])
            profile['name'] = {
                'givenName': data['firstName'],
                'familyName': data['lastName'],
                'formatted': u'%s %s' % (data['firstName'], data['lastName'])
            }
            if data.get('emailAddress'):
                profile['emails'] = [{'value': data.get('emailAddress')}]
            if data.get('pictureUrl'):
                profile['photos'] = [{'value': data.get('pictureUrl')}]

            profile['accounts'] = [{
                'domain': 'linkedin.com',
                'userid': data['id']
            }]

        cred = {'oauthAccessToken': access_token,
                'oauthExpiresIn': expires_in}
        return LinkedinAuthenticationComplete(profile=profile,
                                              credentials=cred,
                                              provider_name=self.name,
                                              provider_type=self.type)