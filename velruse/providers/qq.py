"""QQ Authentication Views"""
from json import loads
from urlparse import parse_qs
import requests
from pyramid.httpexceptions import HTTPFound
from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url


class QQAuthenticationComplete(AuthenticationComplete):
    """QQ auth complete"""


def includeme(config):
    config.add_route("qq_login", "/qq/login")
    config.add_route("qq_process", "/qq/process",
                     use_global_views=True,
                     factory=qq_process)
    config.add_view(qq_login, route_name="qq_login")
    settings = config.registry.settings
    settings['velruse.providers_infos']['velruse.providers.qq']['login'] =   'qq_login'
    settings['velruse.providers_infos']['velruse.providers.qq']['process'] = 'qq_process'


def qq_login(request):
    """Initiate a qq login"""
    config = request.registry.settings
    scope = config.get('velruse.qq.scope',
                       request.POST.get('scope', ''))
    gh_url = flat_url('https://graph.qq.com/oauth2.0/authorize', scope=scope,
                      client_id=config['velruse.qq.app_id'],
                      response_type='code',
                      redirect_uri=request.route_url('qq_process'))
    return HTTPFound(location=gh_url)


def qq_process(request):
    """Process the qq redirect"""
    config = request.registry.settings
    code = request.GET.get('code')
    if not code:
        reason = request.GET.get('error', 'No reason provided.')
        return AuthenticationDenied(reason)

    # Now retrieve the access token with the code
    access_url = flat_url('https://graph.qq.com/oauth2.0/token',
                          client_id=config['velruse.qq.app_id'],
                          client_secret=config['velruse.qq.app_secret'],
                          grant_type='authorization_code',
                          redirect_uri=request.route_url('qq_process'),
                          code=code)
    r = requests.get(access_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    access_token = parse_qs(r.content)['access_token'][0]

    # Retrieve profile data
    graph_url = flat_url('https://graph.qq.com/oauth2.0/me',
                         access_token=access_token)
    r = requests.get(graph_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    data = loads(r.content[10:-3])
    openid = data.get('openid', '')

    user_info_url = flat_url('https://graph.qq.com/user/get_user_info',
            access_token=access_token,
            oauth_consumer_key=config['velruse.qq.app_id'],
            openid=openid)
    r = requests.get(user_info_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    data = loads(r.content)

    profile = {
        'accounts': [{'domain':'qq.com', 'userid':openid}],
        'displayName': data['nickname'],
        'preferredUsername': data['nickname'],
    }

    cred = {'oauthAccessToken': access_token}
    return QQAuthenticationComplete(profile=profile, credentials=cred)
