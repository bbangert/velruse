"""Facebook Authentication Views"""
import uuid

from urlparse import parse_qs

from pyramid.httpexceptions import HTTPFound
from simplejson import loads
import requests

from velruse.exceptions import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import CSRFError
from velruse.exceptions import ThirdPartyFailure
from velruse.parsers import extract_fb_data
from velruse.utils import flat_url


def includeme(config):
    config.add_route("facebook_login", "/facebook/login")
    config.add_route("facebook_process", "/facebook/process")
    config.add_view(facebook_login, route_name="facebook_login")
    config.add_view(facebook_process, route_name="facebook_process")


def facebook_login(request):
    """Initiate a facebook login"""
    config = request.registry.settings
    scope = config.get('velruse.facebook.scope',
                       request.POST.get('scope', ''))
    request.session['state'] = state = uuid.uuid4().hex
    fb_url = flat_url('https://www.facebook.com/dialog/oauth/', scope=scope,
                      client_id=config['velruse.facebook.app_id'],
                      redirect_uri=request.route_url('facebook_process'),
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
        raise AuthenticationDenied(reason)

    # Now retrieve the access token with the code
    access_url = flat_url('https://graph.facebook.com/oauth/access_token',
                          client_id=config['velruse.facebook.app_id'],
                          client_secret=config['velruse.facebook.app_secret'],
                          redirect_uri=request.route_url('facebook_process'),
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

    # Create and raise our AuthenticationComplete exception with the
    # appropriate data to be passed
    complete = AuthenticationComplete()
    complete.profile = profile
    complete.credentials = { 'oauthAccessToken': access_token }
    raise complete
