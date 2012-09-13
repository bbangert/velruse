"""Mail.ru Authentication Views

You may see developer docs on http://api.mail.ru/docs/guides/oauth/
"""
import json
import uuid
import requests
import hashlib
import re

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



PROVIDER_NAME = 'mailru'
PROVIDER_DOMAIN = 'mail.ru'
PROVIDER_AUTH_URL = 'https://connect.mail.ru/oauth/authorize'
PROVIDER_ACCESS_TOKEN_URL = 'https://connect.mail.ru/oauth/token'
PROVIDER_USER_PROFILE_URL = 'https://www.appsmail.ru/platform/api'
PROVIDER_USER_PROFILE_API_METHOD = 'users.getInfo'

FIELD_SEX = {
    0: 'male',
    1: 'female'
}
# Mail.ru provides a birthday information in form of 'dd.mm.yyyy' which is a regular
# representation of dates in Russia.
# Therefore, we must convert it into ISO 8601 in order to follow the Portable Contacts'
# birthday format.
FIELD_BIRTHDAY_RE = re.compile('(?P<dd>\d{2})\.(?P<mm>\d{2})\.(?P<yyyy>\d{4})')


class MailRuAuthenticationComplete(AuthenticationComplete):
    """MailRu auth complete"""


def includeme(config):
    config.add_directive('add_mailru_login', add_mailru_login)
    config.add_directive('add_mailru_login_from_settings', add_mailru_login_from_settings)


def add_mailru_login_from_settings(config, prefix='velruse.mailru.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    config.add_mailru_login(**p.kwargs)


def add_mailru_login(
    config,
    consumer_key,
    consumer_secret,
    scope=None,
    login_path='/login/{name}'.format(name=PROVIDER_NAME),
    callback_path='/login/{name}/callback'.format(name=PROVIDER_NAME),
    name=PROVIDER_NAME
):
    """Add a MailRu login provider to the application."""
    provider = MailRuProvider(name, consumer_key, consumer_secret, scope)
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


class MailRuProvider(object):
    
    def __init__(self, name, consumer_key, consumer_secret, scope):
        self.name = name
        self.type = PROVIDER_NAME
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope

        self.login_route = 'velruse.{name}-login'.format(name=name)
        self.callback_route = 'velruse.{name}-callback'.format(name=name)


    def login(self, request):
        """Initiate a MailRu login"""
        request.session['state'] = state = uuid.uuid4().hex
        auth_url = flat_url(
            PROVIDER_AUTH_URL,
            scope=self.scope,
            client_id=self.consumer_key,
            redirect_uri=request.route_url(self.callback_route),
            response_type='code',
            state=state)
        return HTTPFound(location=auth_url)


    def callback(self, request):
        """Process the MailRu redirect"""
        state = request.session.get('state')
        if not state or state != request.GET.get('state'):
            raise CSRFError(
                'CSRF Validation check failed. Request state {req_state} is not '
                'the same as session state {sess_state}'.format(
                    req_state=request.GET.get('state'),
                    sess_state=request.session.get('state')
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
        access_params = dict(
            grant_type='authorization_code',
            code=code,
            client_id=self.consumer_key,
            client_secret=self.consumer_secret,
            redirect_uri=request.route_url(self.callback_route),
        )
        r = requests.post(PROVIDER_ACCESS_TOKEN_URL, access_params)
        if r.status_code != 200:
            raise ThirdPartyFailure(
                'Status {status}: {content}'.format(
                    status=r.status_code, content=r.content
                )
            )
        data =json.loads(r.content)
        access_token = data['access_token']
        
        # Retrieve profile data.
        
        # Mail.ru API requires a special parameter 'sig' which must be composed
        # by the following sequence
        signature = hashlib.md5(
            'app_id={client_id}'
            'method={method}'
            'secure=1'
            'session_key={access_token}'
            '{secret_key}'.format(
                client_id=self.consumer_key,
                method=PROVIDER_USER_PROFILE_API_METHOD,
                access_token=access_token,
                secret_key=self.consumer_secret
            )
        ).hexdigest()
        
        # Read more about the following params on
        # http://api.mail.ru/docs/guides/restapi/#params
        profile_url = flat_url(
            PROVIDER_USER_PROFILE_URL,
            method=PROVIDER_USER_PROFILE_API_METHOD,
            app_id=self.consumer_key,
            sig=signature,
            session_key=access_token,
            secure=1
        )
        r = requests.get(profile_url)
        if r.status_code != 200:
            raise ThirdPartyFailure(
                'Status {status}: {content}'.format(
                    status=r.status_code, content=r.content
                )
            )
        profile = json.loads(r.content)[0]
        profile = extract_normalize_mailru_data(profile)
        cred = {'oauthAccessToken': access_token}
        return MailRuAuthenticationComplete(
            profile=profile,
            credentials=cred,
            provider_name=self.name,
            provider_type=self.type
        )


def extract_normalize_mailru_data(data):
    """Extract and normalize MailRu data returned by the provider"""
    # You may see the input data format on
    # http://api.mail.ru/docs/reference/rest/users-getinfo/#result
    profile = {
        'accounts': [
            {
                'domain': PROVIDER_DOMAIN,
                'userid': data['uid']
            }
        ],
        'name': {},
        'gender': FIELD_SEX.get(data.get('sex')),
        'photos': [],
        'addresses': []
    }
    
    # Names
    nickname = data.get('nick')
    if nickname:
         profile['preferredUsername'] = nickname
    
    first_name = data.get('first_name')
    if first_name:
        profile['name']['givenName'] = first_name
    
    last_name = data.get('last_name')
    if last_name:
        profile['name']['familyName'] = last_name
    
    if first_name and last_name:
        profile['displayName'] = u'{} {}'.format(first_name, last_name).strip()
    elif first_name:
        profile['displayName'] = first_name
    elif last_name:
        profile['displayName'] = first_name
    elif nickname:
        profile['displayName'] = nickname
    else:
        profile['displayName'] = 'Mail.ru user {uid}'.format(uid=data['uid']) 
    
    # Birthday
    match = FIELD_BIRTHDAY_RE.match(data.get('birthday', ''))
    if match:
        profile['birthday'] = '{yyyy}-{mm}-{dd}'.format(**match.groupdict())
    
    # Email
    email = data.get('email')
    if email:
        profile['emails'] = [{
            'value': email,
            'primary': True
        }]
    
    # URLs
    link = data.get('link')
    if link:
        profile['urls'] = [{
            'value': link
        }]
    
    # Photos
    if data.get('has_pic'):
        road_map = [
            [
                # field suffix
                '',
                # type
                'original'
            ],
            ['_big', 'big'],
            ['_small', 'small'],
            ['_190', 'custom_190'],
            ['_180', 'custom_180'],
            ['_128', 'custom_128'],
            ['_50', 'custom_50'],
            ['_40', 'custom_40'],
            ['_32', 'custom_32'],
            ['_22', 'custom_22']
        ]
        for item in road_map:
            photo, image_type = item
            photo = data.get('pic{photo_suffix}'.format(photo_suffix=photo))
            if photo:
                profile['photos'].append({
                    'value': photo,
                    'type': image_type
                })
    
    # Location
    location = data.get('location', {})
    country = location.get('country', {}).get('name')
    region = location.get('region', {}).get('name')
    city = location.get('city', {}).get('name')
    if country or region or city:
        address = {}
        if country:
            address['country'] = country
        if region:
            address['region'] = region
        if city:
            address['locality'] = city
        profile['addresses'].append(address)
    
    # Now strip out empty values
    for k, v in profile.items():
        if not v or (isinstance(v, list) and not v[0]):
            del profile[k]

    return profile
