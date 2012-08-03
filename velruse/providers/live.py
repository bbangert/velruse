"""Live Authentication Views"""
import datetime
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


class LiveAuthenticationComplete(AuthenticationComplete):
    """Live Connect auth complete"""


def includeme(config):
    config.add_directive('add_live_login', add_live_login)
    config.add_directive('add_live_login_from_settings',
                         add_live_login_from_settings)


def add_live_login_from_settings(config, prefix='velruse.live.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    config.add_live_login(**p.kwargs)


def add_live_login(config,
                   consumer_key,
                   consumer_secret,
                   scope=None,
                   login_path='/login/live',
                   callback_path='/login/live/callback',
                   name='live'):
    """
    Add a Live login provider to the application.
    """
    provider = LiveProvider(name, consumer_key, consumer_secret, scope)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class LiveProvider(object):
    def __init__(self, name, consumer_key, consumer_secret, scope):
        self.name = name
        self.type = 'live'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a Live login"""
        scope = request.POST.get('scope', self.scope or
                                 'wl.basic wl.emails wl.signin')
        fb_url = flat_url('https://oauth.live.com/authorize', scope=scope,
                          client_id=self.consumer_key,
                          redirect_uri=request.route_url(self.callback_route),
                          response_type="code")
        return HTTPFound(location=fb_url)

    def callback(self, request):
        """Process the Live redirect"""
        if 'error' in request.GET:
            raise ThirdPartyFailure(request.GET.get('error_description',
                                    'No reason provided.'))
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error_reason', 'No reason provided.')
            return AuthenticationDenied(reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        # Now retrieve the access token with the code
        access_url = flat_url(
            'https://oauth.live.com/token',
            client_id=self.consumer_key,
            client_secret=self.consumer_secret,
            redirect_uri=request.route_url(self.callback_route),
            grant_type="authorization_code",
            code=code)
        r = requests.get(access_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        data = loads(r.content)
        access_token = data['access_token']

        # Retrieve profile data
        graph_url = flat_url('https://apis.live.net/v5.0/me',
                             access_token=access_token)
        r = requests.get(graph_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        live_profile = loads(r.content)
        profile = extract_live_data(live_profile)

        cred = {'oauthAccessToken': access_token}
        if 'refresh_token' in data:
            cred['oauthRefreshToken'] = data['refresh_token']
        return LiveAuthenticationComplete(profile=profile,
                                          credentials=cred,
                                          provider_name=self.name,
                                          provider_type=self.type)


def extract_live_data(data):
    """Extract and normalize Windows Live Connect data"""
    emails = data.get('emails', {})
    profile = {
        'accounts': [{'domain':'live.com', 'userid':data['id']}],
        'gender': data.get('gender'),
        'verifiedEmail': emails.get('preferred'),
        'updated': data.get('updated_time'),
        'name': {
            'formatted': data.get('name'),
            'familyName': data.get('last_name'),
            'givenName': data.get('first_name'),
        },
        'displayName': data.get('name'),
        'emails': [],
        'urls': [],
    }

    if emails.get('personal'):
        profile['emails'].append(
            {'type': 'personal', 'value': emails['personal']})
    if emails.get('business'):
        profile['emails'].append(
            {'type': 'business', 'value': emails['business']})
    if emails.get('preferred'):
        profile['emails'].append(
            {'type': 'preferred', 'value': emails['preferred'],
             'primary': True})
    if emails.get('account'):
        profile['emails'].append(
            {'type': 'account', 'value': emails['account']})
    if 'link' in data:
        profile['urls'].append(
            {'type': 'profile', 'value': data['link']})
    if 'birth_day' in data:
        try:
            profile['birthday'] = datetime.date(
                    int(data['birth_year']),
                    int(data['birth_month']),
                    int(data['birth_day']))
        except ValueError:
            pass
    return profile
