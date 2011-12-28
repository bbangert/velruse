"""Sina Microblogging weibo.com Authentication Views"""
import uuid
from json import loads
import requests
from pyramid.httpexceptions import HTTPFound
from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import CSRFError
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url


class WeiboAuthenticationComplete(AuthenticationComplete):
    """Weibo auth complete"""


def includeme(config):
    config.add_route("weibo_login", "/weibo/login")
    config.add_route("weibo_process", "/weibo/process",
                     use_global_views=True,
                     factory=weibo_process)
    config.add_view(weibo_login, route_name="weibo_login")


def weibo_login(request):
    """Initiate a weibo login"""
    config = request.registry.settings
    request.session['state'] = state = uuid.uuid4().hex
    fb_url = flat_url('https://api.weibo.com/oauth2/authorize',
                      client_id=config['velruse.weibo.app_id'],
                      redirect_uri=request.route_url('weibo_process'),
                      state=state)
    return HTTPFound(location=fb_url)


def weibo_process(request):
    """Process the weibo redirect"""
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
    r = requests.post('https://api.weibo.com/oauth2/access_token', dict(
                          client_id=config['velruse.weibo.app_id'],
                          client_secret=config['velruse.weibo.app_secret'],
                          redirect_uri=request.route_url('weibo_process'),
                          grant_type='authorization_code',
                          code=code)
                    )
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    data = loads(r.content)
    access_token = data['access_token']
    uid = data['uid']

    # Retrieve profile data
    graph_url = flat_url('https://api.weibo.com/2/users/show.json',
                            access_token=access_token,
                            uid=uid)
    r = requests.get(graph_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    data = loads(r.content)

    profile = {
        'accounts': [{'domain':'weibo.com', 'userid':data['id']}],
        'gender': data.get('gender'),
        'displayName': data['screen_name'],
        'preferredUsername': data['name'],
    }

    cred = {'oauthAccessToken': access_token}
    return WeiboAuthenticationComplete(profile=profile, credentials=cred)
