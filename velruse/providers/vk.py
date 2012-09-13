"""VK.com (ex Vkontakte.ru) Authentication Views

VK is considered to be the #1 social network
(with more than a 100 million active users) in Russia.
You may see the developer docs at http://vk.com/developers.php#devstep2
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



PROVIDER_NAME = 'vk'
PROVIDER_AUTH_URL = 'https://oauth.vk.com/authorize'
PROVIDER_ACCESS_TOKEN_URL = 'https://api.vk.com/oauth/access_token'
PROVIDER_USER_PROFILE_URL = 'https://api.vk.com/method/getProfiles'

FIELD_SEX = {
    1: 'female',
    2: 'male'
}


class VKAuthenticationComplete(AuthenticationComplete):
    """VK auth complete"""


def includeme(config):
    config.add_directive('add_vk_login', add_vk_login)
    config.add_directive('add_vk_login_from_settings', add_vk_login_from_settings)


def add_vk_login_from_settings(config, prefix='velruse.vk.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    config.add_vk_login(**p.kwargs)


def add_vk_login(
    config,
    consumer_key,
    consumer_secret,
    scope=None,
    login_path='/login/{name}'.format(name=PROVIDER_NAME),
    callback_path='/login/{name}/callback'.format(name=PROVIDER_NAME),
    name=PROVIDER_NAME
):
    """Add a VK login provider to the application."""
    provider = VKProvider(name, consumer_key, consumer_secret, scope)
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


class VKProvider(object):
    
    def __init__(self, name, consumer_key, consumer_secret, scope):
        self.name = name
        self.type = PROVIDER_NAME
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope

        self.login_route = 'velruse.{name}-login'.format(name=name)
        self.callback_route = 'velruse.{name}-callback'.format(name=name)


    def login(self, request):
        """Initiate a VK login"""
        request.session['state'] = state = uuid.uuid4().hex
        fb_url = flat_url(
            PROVIDER_AUTH_URL,
            scope=self.scope,
            client_id=self.consumer_key,
            redirect_uri=request.route_url(self.callback_route),
            response_type='code',
            state=state)
        return HTTPFound(location=fb_url)


    def callback(self, request):
        """Process the VK redirect"""
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
            reason = request.GET.get('error_description', 'No reason provided.')
            return AuthenticationDenied(
                reason=reason,
                provider_name=self.name,
                provider_type=self.type
            )
        # Now retrieve the access token with the code
        access_url = flat_url(
            PROVIDER_ACCESS_TOKEN_URL,
            client_id=self.consumer_key,
            client_secret=self.consumer_secret,
            redirect_uri=request.route_url(self.callback_route),
            code=code
        )
        r = requests.get(access_url)
        if r.status_code != 200:
            raise ThirdPartyFailure(
                'Status {status}: {content}'.format(
                    status=r.status_code, content=r.content
                )
            )
        data =json.loads(r.content)
        access_token = data['access_token']
        
        # Retrieve profile data
        graph_url = flat_url(
            PROVIDER_USER_PROFILE_URL,
            access_token=access_token,
            uids=data['user_id'],
            fields=(
                'first_name,last_name,nickname,domain,sex,bdate,city,country,timezone,'
                'photo,photo_medium,photo_big,photo_rec,has_mobile,mobile_phone,home_phone,'
                'rate,contacts,education'
            )
        )
        r = requests.get(graph_url)
        if r.status_code != 200:
            raise ThirdPartyFailure(
                'Status {status}: {content}'.format(
                    status=r.status_code, content=r.content
                )
            )
        vk_profile = json.loads(r.content)['response'][0]
        vk_profile['uid'] = data['user_id']
        profile = extract_normalize_vk_data(vk_profile)
        cred = {'oauthAccessToken': access_token}
        return VKAuthenticationComplete(
            profile=profile,
            credentials=cred,
            provider_name=self.name,
            provider_type=self.type
        )


def extract_normalize_vk_data(data):
    """Extract and normalize VK data returned by the provider"""
    # Names
    profile = {
        'accounts': [
            {
                'domain': 'vk.com',
                'userid': data['uid']
            }
        ],
        'name': {},
        'preferredUsername': data.get('nickname'),
        'photos': [],
        'phoneNumbers': []
    }
    if data['first_name']:
        profile['name']['givenName'] = data['first_name']
    if data['last_name']:
        profile['name']['familyName'] = data['last_name']
    profile['displayName'] = u'{} {}'.format(data['first_name'], data['last_name']).strip()
    
    # Gender
    gender = FIELD_SEX.get(data.get('sex'))
    if gender:
        profile['gender'] = gender
    
    # Photos
    road_map = [
        [
            # field name
            'photo',
            # default value (i.e. no photo)
            'images/question_c.gif',
            # type
            'thumbnail'
        ],
        ['photo_medium', 'images/question_b.gif', 'medium'],
        ['photo_big', 'images/question_a.gif', 'large'],
        ['photo_rec', 'images/question_a.gif', 'square']
    ]
    for item in road_map:
        photo, default, image_type = item
        photo = data.get(photo)
        if photo and photo != default:
            profile['photos'].append({
                'value': photo,
                'type': image_type
            })
    
    # Phones
    road_map = [
        [
            # field name
            'mobile_phone',
            # type
            'mobile'
        ],
        ['home_phone', 'home']
    ]
    for item in road_map:
        phone, phone_type = item
        phone = data.get(phone)
        if phone:
            profile['phoneNumbers'].append({
                'value': phone,
                'type': phone_type
            })
    
    # Now strip out empty values
    for k, v in profile.items():
        if not v or (isinstance(v, list) and not v[0]):
            del profile[k]

    return profile
