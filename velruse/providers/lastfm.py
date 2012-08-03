"""Last.fm Authentication Views"""
from hashlib import md5
from json import loads

import requests

from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

from velruse.api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from velruse.exceptions import ThirdPartyFailure
from velruse.settings import ProviderSettings
from velruse.utils import flat_url

API_BASE = 'https://ws.audioscrobbler.com/2.0/'


class LastFMAuthenticationComplete(AuthenticationComplete):
    """LastFM auth complete"""


def includeme(config):
    config.add_directive('add_lastfm_login', add_lastfm_login)
    config.add_directive('add_lastfm_login_from_settings',
                         add_lastfm_login_from_settings)


def add_lastfm_login_from_settings(config, prefix='velruse.lastfm.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('login_path')
    p.update('callback_path')
    config.add_lastfm_login(**p.kwargs)


def add_lastfm_login(config,
                     consumer_key,
                     consumer_secret,
                     login_path='/lastfm/login',
                     callback_path='/lastfm/login/callback',
                     name='lastfm'):
    """
    Add a Last.fm login provider to the application.
    """
    provider = LastfmProvider(name, consumer_key, consumer_secret)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class LastfmProvider(object):
    def __init__(self, name, consumer_key, consumer_secret):
        self.name = name
        self.type = 'lastfm'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a LastFM login"""
        fb_url = flat_url('https://www.last.fm/api/auth/',
                          api_key=self.consumer_key)
        return HTTPFound(location=fb_url)

    def callback(self, request):
        """Process the LastFM redirect"""
        if 'error' in request.GET:
            raise ThirdPartyFailure(request.GET.get('error_description',
                                    'No reason provided.'))
        token = request.GET.get('token')
        if not token:
            reason = request.GET.get('error_reason', 'No reason provided.')
            return AuthenticationDenied(reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        # Now establish a session with the token
        params = {
            'method': 'auth.getSession',
            'api_key': self.consumer_key,
            'token': token
        }
        signed_params = sign_call(params, self.consumer_secret)
        session_url = flat_url(API_BASE, format='json', **signed_params)
        r = requests.get(session_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        data = loads(r.content)

        session = data['session']
        cred = {
            'sessionKey': session['key']
        }

        # Fetch the user data
        user_url = flat_url(API_BASE, format='json', method='user.getInfo',
                            user=session['name'], api_key=self.consumer_key)
        r = requests.get(user_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        data = loads(r.content)['user']
        profile = {
            'displayName': data['name'],
            'gender': 'male' if data['gender'] == 'm' else 'female',
            'name': {
                'formatted': data.get('realname'),
            },
            'urls': {
                'type': 'profile',
                'value': data.get('url')
            },
            'photos': [],
            'accounts': [{
                'domain': 'last.fm',
                'username': session['name'],
                'userid': data['id']
            }]
        }
        images = {}
        for img in data.get('image', []):
            images[img['size']] = img['#text']
        if 'medium' in images:
            profile['photos'].append({'type': 'thumbnail',
                                      'value': images['medium']})
        larger = images.get('extralarge', images.get('large'))
        if larger:
            profile['photos'].append({'type': '', 'value': larger})
        return LastFMAuthenticationComplete(profile=profile,
                                            credentials=cred,
                                            provider_name=self.name,
                                            provider_type=self.type)


def sign_call(params, secret):
    pairs = ['%s%s' % (k, params[k]) for k in sorted(params)]
    api_sig = md5(''.join(pairs) + secret).hexdigest()
    signed_params = params.copy()
    signed_params['api_sig'] = api_sig
    return signed_params
