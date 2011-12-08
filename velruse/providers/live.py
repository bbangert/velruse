"""Live Authentication Views"""
import datetime
from json import loads

import requests

from pyramid.httpexceptions import HTTPFound

from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url


class LiveAuthenticationComplete(AuthenticationComplete):
    """Live Connect auth complete"""


def includeme(config):
    config.add_route("live_login", "/live/login")
    config.add_route("live_process", "/live/process",
                     use_global_views=True,
                     factory=live_process)
    config.add_view(live_login, route_name="live_login")


def live_login(request):
    """Initiate a Live login"""
    config = request.registry.settings
    scope = config.get('velruse.live.scope',
                       request.POST.get('scope', 'wl.basic wl.emails wl.signin'))
    fb_url = flat_url('https://oauth.live.com/authorize', scope=scope,
                      client_id=config['velruse.live.client_id'],
                      redirect_uri=request.route_url('live_process'),
                      response_type="code")
    return HTTPFound(location=fb_url)


def live_process(request):
    """Process the Live redirect"""
    if 'error' in request.GET:
        raise ThirdPartyFailure(request.GET.get('error_description',
                                'No reason provided.'))
    config = request.registry.settings
    code = request.GET.get('code')
    if not code:
        reason = request.GET.get('error_reason', 'No reason provided.')
        return AuthenticationDenied(reason)

    # Now retrieve the access token with the code
    access_url = flat_url('https://oauth.live.com/token',
                          client_id=config['velruse.live.client_id'],
                          client_secret=config['velruse.live.client_secret'],
                          redirect_uri=request.route_url('live_process'),
                          grant_type="authorization_code", code=code)
    r = requests.get(access_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    data = loads(r.content)
    access_token = data['access_token']

    # Retrieve profile data
    graph_url = flat_url('https://apis.live.net/v5.0/me',
                         access_token=access_token)
    r = requests.get(graph_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    live_profile = loads(r.content)
    profile = extract_live_data(live_profile)

    cred = {'oauthAccessToken': access_token}
    if 'refresh_token' in data:
        cred['oauthRefreshToken'] = data['refresh_token']
    return LiveAuthenticationComplete(profile=profile,
                                      credentials=cred)


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
        profile['birthday'] = datetime.date(data['birth_year'],
                                            data['birth_month'],
                                            data['birth_day'])
    return profile
