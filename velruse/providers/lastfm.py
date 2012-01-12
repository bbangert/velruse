"""Last.fm Authentication Views"""
from hashlib import md5
from urllib import urlencode
from json import loads

import requests

from pyramid.httpexceptions import HTTPFound

from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url, get_came_from 

API_BASE = 'https://ws.audioscrobbler.com/2.0/'


class LastFMAuthenticationComplete(AuthenticationComplete):
    """LastFM auth complete"""


def includeme(config):
    config.add_route("lastfm_login", "/lastfm/login")
    config.add_route("lastfm_process", "/lastfm/process",
                     use_global_views=True,
                     factory=lastfm_process)
    config.add_view(lastfm_login, route_name="lastfm_login")


def sign_call(params, secret):
    pairs = ['%s%s' % (k, params[k]) for k in sorted(params)]
    api_sig = md5(''.join(pairs) + secret).hexdigest()
    signed_params = params.copy()
    signed_params['api_sig'] = api_sig
    return signed_params


def lastfm_login(request):
    """Initiate a LastFM login"""
    config = request.registry.settings
    redirect_uri = request.route_url('lastfm_process')
    came_from = get_came_from(request)
    if came_from:
        qs = urlencode({'end_point':came_from })
        if not '?' in redirect_uri:
            redirect_uri += '?'
        redirect_uri += qs  
    fb_url = flat_url('https://www.last.fm/api/auth/', api_key=config['velruse.lastfm.api_key'], cb=redirect_uri)
    return HTTPFound(location=fb_url)


def lastfm_process(request):
    """Process the LastFM redirect"""
    if 'error' in request.GET:
        raise ThirdPartyFailure(request.GET.get('error_description',
                                'No reason provided.'))
    config = request.registry.settings
    api_key = config['velruse.lastfm.api_key']
    token = request.GET.get('token')
    if not token:
        reason = request.GET.get('error_reason', 'No reason provided.')
        return AuthenticationDenied(reason)

    # Now establish a session with the token
    params = {
        'method': 'auth.getSession',
        'api_key': api_key,
        'token': token
    }
    signed_params = sign_call(params, config['velruse.lastfm.secret'])
    session_url = flat_url(API_BASE, format='json', **signed_params)
    r = requests.get(session_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    data = loads(r.content)

    session = data['session']
    cred = {
        'sessionKey': session['key']
    }

    # Fetch the user data
    user_url = flat_url(API_BASE, format='json', method='user.getInfo',
                        user=session['name'], api_key=api_key)
    r = requests.get(user_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
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
    profile['end_point'] = get_came_from(request)
    return LastFMAuthenticationComplete(profile=profile,
                                        credentials=cred)
