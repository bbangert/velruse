"""Facebook Authentication Views"""
import datetime
import uuid
from json import loads
from urlparse import parse_qs
from urllib import urlencode

import requests

from pyramid.httpexceptions import HTTPFound

from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import CSRFError
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url, get_came_from


class FacebookAuthenticationComplete(AuthenticationComplete):
    """Facebook auth complete"""


def includeme(config):
    config.add_route("facebook_login", "/facebook/login")
    config.add_route("facebook_process", "/facebook/process",
                     use_global_views=True,
                     factory=facebook_process)
    config.add_view(facebook_login, route_name="facebook_login")


def facebook_login(request):
    """Initiate a facebook login"""
    config = request.registry.settings
    scope = config.get('velruse.facebook.scope',
                       request.POST.get('scope', ''))
    request.session['state'] = state = uuid.uuid4().hex
    redirect_uri = request.route_url('facebook_process')
    came_from = get_came_from(request)
    if came_from:
        qs = urlencode({'end_point':came_from })
        if not '?' in redirect_uri:
            redirect_uri += '?'
        redirect_uri += qs   
    fb_url = flat_url('https://www.facebook.com/dialog/oauth/', scope=scope,
                      client_id=config['velruse.facebook.app_id'],
                      redirect_uri=redirect_uri,
                      state=state)
    return HTTPFound(location=fb_url)


def facebook_process(request):
    """Process the facebook redirect"""
    if request.GET.get('state') != request.session.get('state'):
        raise CSRFError("CSRF Validation check failed. Request state %s is "
                        "not the same as session state %s" % (
                        request.GET.get('state'), request.session.get('state')
                        ))
    config = request.registry.settings
    code = request.GET.get('code')
    if not code:
        reason = request.GET.get('error_reason', 'No reason provided.')
        return AuthenticationDenied(reason)

    # Now retrieve the access token with the code
    redirect_uri = request.route_url('facebook_process')
    came_from = get_came_from(request)
    if came_from:
        qs = urlencode({'end_point':came_from })
        if not '?' in redirect_uri:
            redirect_uri += '?'
        redirect_uri += qs    
    access_url = flat_url('https://graph.facebook.com/oauth/access_token',
                          client_id=config['velruse.facebook.app_id'],
                          client_secret=config['velruse.facebook.app_secret'],
                          redirect_uri=redirect_uri,
                          code=code)
    r = requests.get(access_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    access_token = parse_qs(r.content)['access_token'][0]

    # Retrieve profile data
    graph_url = flat_url('https://graph.facebook.com/me',
                         access_token=access_token)
    r = requests.get(graph_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    fb_profile = loads(r.content)
    profile = extract_fb_data(fb_profile)

    cred = {'oauthAccessToken': access_token}
    profile['end_point'] = get_came_from(request)
    return FacebookAuthenticationComplete(profile=profile,
                                          credentials=cred)


def extract_fb_data(data):
    """Extact and normalize facebook data as parsed from the graph JSON"""
    # Setup the normalized contact info
    nick = None

    # Setup the nick and preferred username to the last portion of the
    # FB link URL if its not their ID
    link = data.get('link')
    if link:
        last = link.split('/')[-1]
        if last != data['id']:
            nick = last

    profile = {
        'accounts': [{'domain':'facebook.com', 'userid':data['id']}],
        'displayName': data['name'],
        'verifiedEmail': data.get('email') if data.get('verified') else False,
        'gender': data.get('gender'),
        'preferredUsername': nick or data['name'],
    }
    if data.get('email'):
        profile['emails'] = [{'value':data.get('email')}]

    tz = data.get('timezone')
    if tz:
        parts = str(tz).split(':')
        if len(parts) > 1:
            h, m = parts
        else:
            h, m = parts[0], '00'
        if 1 < len(h) < 3:
            h = '%s0%s' % (h[0], h[1])
        elif len(h) == 1:
            h = h[0]
        data['utfOffset'] = ':'.join([h, m])
    bday = data.get('birthday')
    if bday:
        try:
            mth, day, yr = bday.split('/')
            profile['birthday'] = datetime.date(int(yr), int(mth), int(day))
        except ValueError:
            pass
    name = {}
    pcard_map = {'first_name': 'givenName', 'last_name': 'familyName'}
    for key, val in pcard_map.items():
        part = data.get(key)
        if part:
            name[val] = part
    name['formatted'] = data.get('name')

    profile['name'] = name

    # Now strip out empty values
    for k, v in profile.items():
        if not v or (isinstance(v, list) and not v[0]):
            del profile[k]

    return profile
