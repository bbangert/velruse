"""Yandex Authentication Views

You may see developer docs at http://api.yandex.com/oauth/
"""
import json
import uuid
import requests

from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

from velruse.api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from velruse.exceptions import CSRFError, ThirdPartyFailure
from velruse.settings import ProviderSettings
from velruse.utils import flat_url



PROVIDER_NAME = 'yandex'
PROVIDER_AUTH_URL = 'https://oauth.yandex.ru/authorize'
PROVIDER_ACCESS_TOKEN_URL = 'https://oauth.yandex.ru/token'
PROVIDER_USER_PROFILE_URL = 'https://login.yandex.ru/info'


class YandexAuthenticationComplete(AuthenticationComplete):
    """Yandex auth complete"""


def includeme(config):
    config.add_directive('add_yandex_login', add_yandex_login)
    config.add_directive('add_yandex_login_from_settings', add_yandex_login_from_settings)


def add_yandex_login_from_settings(config, prefix='velruse.yandex.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('login_path')
    p.update('callback_path')
    config.add_yandex_login(**p.kwargs)


def add_yandex_login(
    config,
    consumer_key,
    consumer_secret,
    login_path='/login/{name}'.format(name=PROVIDER_NAME),
    callback_path='/login/{name}/callback'.format(name=PROVIDER_NAME),
    name=PROVIDER_NAME
):
    """Add a Yandex login provider to the application."""
    provider = YandexProvider(name, consumer_key, consumer_secret)
    config.add_route(provider.login_route, login_path)
    config.add_view(
        provider,
        attr='login',
        route_name=provider.login_route,
        permission=NO_PERMISSION_REQUIRED
    )
    config.add_route(
        provider.callback_route, callback_path,
        use_global_views=True,
        factory=provider.callback
    )
    register_provider(config, name, provider)


class YandexProvider(object):
    
    def __init__(self, name, consumer_key, consumer_secret):
        self.name = name
        self.type = PROVIDER_NAME
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.login_route = 'velruse.{name}-login'.format(name=name)
        # Yandex doesn't support redirect_uri and scope parameters in query string.
        # You must define the Callback URI and the Scope fields manually in 
        # application's settings page at https://oauth.yandex.ru/client/my
        # The following attribute is left intact in order to preserve API consistency.
        self.callback_route = 'velruse.{name}-callback'.format(name=name)


    def login(self, request):
        """Initiate a Yandex login"""
        request.session['state'] = state = uuid.uuid4().hex
        auth_url = flat_url(
            PROVIDER_AUTH_URL,
            client_id=self.consumer_key,
            response_type='code',
            state=state
        )
        return HTTPFound(location=auth_url)


    def callback(self, request):
        """Process the Yandex redirect"""
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
            return AuthenticationDenied(
                reason=reason,
                provider_name=self.name,
                provider_type=self.type
            )
        # Now retrieve the access token with the code
        token_params = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.consumer_key,
            'client_secret': self.consumer_secret,
        }
        r = requests.post(PROVIDER_ACCESS_TOKEN_URL, token_params)
        if r.status_code != 200:
            raise ThirdPartyFailure(
                'Status {status}: {content}'.format(
                    status=r.status_code, content=r.content
                )
            )
        data =json.loads(r.content)
        access_token = data['access_token']
        
        # Retrieve profile data
        profile_url = flat_url(
            PROVIDER_USER_PROFILE_URL,
            format='json',
            oauth_token=access_token
        )
        r = requests.get(profile_url)
        if r.status_code != 200:
            raise ThirdPartyFailure(
                'Status {status}: {content}'.format(
                    status=r.status_code, content=r.content
                )
            )
        profile = json.loads(r.content)
        profile = extract_normalize_yandex_data(profile)
        cred = {'oauthAccessToken': access_token}
        return YandexAuthenticationComplete(
            profile=profile,
            credentials=cred,
            provider_name=self.name,
            provider_type=self.type
        )


def extract_normalize_yandex_data(data):
    """Extract and normalize Yandex data returned by the provider"""
    profile = {
        'accounts': [
            {
                'domain': 'yandex.ru',
                'userid': data['id']
            }
        ],
        'birthday': data.get('birthday'),
        'gender': data.get('sex'),
    }
    
    email = data.get('default_email')
    if email:
        profile['emails'] = [{
            'value': email,
            'primary': True
        }]
    
    display_name = data.get('display_name')
    if display_name:
        profile['preferredUsername'] = display_name
        profile['nickname'] = display_name
    real_name = data.get('real_name')
    profile['displayName'] =  real_name or display_name or 'Yandex user #{id}'.format(id=data['id'])
        
    # Now strip out empty values
    for k, v in profile.items():
        if not v or (isinstance(v, list) and not v[0]):
            del profile[k]

    return profile
