"""Google Authentication Views"""
from json import loads
import uuid

import requests

from pyramid.httpexceptions import HTTPFound

from velruse.api import (
    AuthenticationComplete,
    AuthenticationDenied,
)
from velruse.exceptions import CSRFError
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url


GOOGLE_OAUTH2_DOMAIN = 'accounts.google.com'


class GoogleOAuth2AuthenticationComplete(AuthenticationComplete):
    """Google OAuth 2.0 auth complete"""


class GoogleOAuth2Provider(object):

    profile_scope = 'https://www.googleapis.com/auth/userinfo.profile'
    email_scope = 'https://www.googleapis.com/auth/userinfo.email'

    def __init__(self,
                 name,
                 consumer_key,
                 consumer_secret,
                 scope):
        self.name = name
        self.type = 'google_oauth2'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.protocol = 'https'
        self.domain = GOOGLE_OAUTH2_DOMAIN

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

        self.scope = scope
        if not self.scope:
            self.scope = ' '.join((self.profile_scope, self.email_scope))

    def login(self, request):
        """Initiate a google login"""
        scope = ' '.join(request.POST.getall('scope')) or self.scope
        request.session['state'] = state = uuid.uuid4().hex
        
        approval_prompt = request.POST.get('approval_prompt', 'auto')

        auth_url = flat_url(
            '%s://%s/o/oauth2/auth' % (self.protocol, self.domain),
            scope=scope,
            response_type='code',
            client_id=self.consumer_key,
            redirect_uri=request.route_url(self.callback_route),
            approval_prompt=approval_prompt,
            access_type='offline',
            state=state)
        return HTTPFound(location=auth_url)

    def callback(self, request):
        """Process the google redirect"""
        sess_state = request.session.get('state')
        req_state = request.GET.get('state')
        if not sess_state or sess_state != req_state:
            raise CSRFError(
                'CSRF Validation check failed. Request state {req_state} is not '
                'the same as session state {sess_state}'.format(
                    req_state=req_state,
                    sess_state=sess_state
                )
            )
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error', 'No reason provided.')
            return AuthenticationDenied(reason=reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        # Now retrieve the access token with the code
        r = requests.post('%s://%s/o/oauth2/token' % (self.protocol, self.domain),
                          data={
                              'client_id': self.consumer_key,
                              'client_secret': self.consumer_secret,
                              'redirect_uri': request.route_url(self.callback_route),
                              'code': code,
                              'grant_type': 'authorization_code'
                          })
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        token_data = loads(r.content)
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token')

        # Retrieve profile data if scopes allow
        profile = {}
        user_url = flat_url(
                '%s://www.googleapis.com/oauth2/v1/userinfo' % self.protocol,
                access_token=access_token)
        r = requests.get(user_url)

        if r.status_code == 200:
            data = loads(r.content)
            profile['accounts'] = [{
                'domain': self.domain,
                'username': data['email'],
                'userid': data['id']
            }]
            profile['displayName'] = data['name']
            profile['preferredUsername'] = data['email']
            profile['verifiedEmail'] = data['email']
            profile['emails'] = [{'value': data['email']}]

        cred = {'oauthAccessToken': access_token,
                'oauthRefreshToken': refresh_token}
        return Google2AuthenticationComplete(profile=profile,
                                             credentials=cred,
                                             provider_name=self.name,
                                             provider_type=self.type)
