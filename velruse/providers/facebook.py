"""Facebook Authentication Views"""
import uuid
from json import loads
from urlparse import parse_qs

import requests

from pyramid.httpexceptions import HTTPFound

from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import CSRFError
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url


class FacebookAuthenticationComplete(AuthenticationComplete):
    """Facebook auth complete"""


def includeme(config):
    settings = config.registry.settings
    app_id = settings['velruse.facebook.app_id']
    app_secret = settings['velruse.facebook.app_secret']
    scope = settings.get('velruse.facebook.scope', None)

    provider = FacebookProvider(app_id, app_secret, scope=scope)

    config.add_route("facebook_login", "/facebook/login")
    config.add_route("facebook_process", "/facebook/process",
                     use_global_views=True,
                     factory=provider.process)
    config.add_view(provider.login, route_name="facebook_login")


class FacebookProvider(object):
    requests = requests # testing

    def __init__(self, app_id, app_secret, scope=None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.scope = scope

    def login(self, request):
        """Initiate a facebook login"""
        scope = self.scope or request.POST.get('scope', '')
        request.session['state'] = state = uuid.uuid4().hex
        fb_url = self.oauth_url(
            redirect_uri=request.route_url('facebook_process'),
            state=state,
            scope=scope)
        return HTTPFound(location=fb_url)

    def process(self, request):
        """Process the facebook redirect"""
        state = request.session.get('state')
        if request.GET.get('state') != state or state is None:
            raise CSRFError("CSRF Validation check failed. Request state "
                            "%s is not the same as session state %s" % (
                                request.GET.get('state'), state))
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error_reason', 'No reason provided.')
            return AuthenticationDenied(reason)

        # Now retrieve the access token with the code
        access_url = self.access_url(
            redirect_uri=request.route_url('facebook_process'),
            code=code)
        r = self.requests.get(access_url)
        if r.status_code != 200:
            raise ThirdPartyFailure(
                "Status %s: %s" % (r.status_code, r.content))
        access_token = parse_qs(r.content)['access_token'][0]

        # Retrieve profile data
        graph_url = self.graph_url(access_token=access_token)
        r = self.requests.get(graph_url)
        if r.status_code != 200:
            raise ThirdPartyFailure(
                "Status %s: %s" % (r.status_code, r.content))
        fb_profile = loads(r.content)
        profile = extract_fb_data(fb_profile)

        cred = {'oauthAccessToken': access_token}
        return FacebookAuthenticationComplete(profile=profile,
                                              credentials=cred)

    def oauth_url(self, redirect_uri, state, scope):
        return flat_url(
            'https://www.facebook.com/dialog/oauth/',
            scope=scope,
            client_id=self.app_id,
            redirect_uri=redirect_uri,
            state=state)

    def access_url(self, redirect_uri, code):
        return flat_url(
            'https://graph.facebook.com/oauth/access_token',
            client_id=self.app_id,
            client_secret=self.app_secret,
            redirect_uri=redirect_uri,
            code=code)

    def graph_url(self, access_token):
        return flat_url(
            'https://graph.facebook.com/me',
            access_token=access_token)


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
        mth, day, yr = bday.split('/')
        profile['birthday'] = '-'.join([yr, mth, day])
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
