"""Taobao Authentication Views"""
from hashlib import md5
from json import loads
import time
import requests
from pyramid.httpexceptions import HTTPFound
from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url


class TaobaoAuthenticationComplete(AuthenticationComplete):
    """Taobao auth complete"""


def includeme(config):
    config.add_route("taobao_login", "/taobao/login")
    config.add_route("taobao_process", "/taobao/process",
                     use_global_views=True,
                     factory=taobao_process)
    config.add_view(taobao_login, route_name="taobao_login")
    settings = config.registry.settings
    settings['velruse.providers_infos']['velruse.providers.taobao']['login'] =   'taobao_login'
    settings['velruse.providers_infos']['velruse.providers.taobao']['process'] = 'taobao_process'


def taobao_login(request):
    """Initiate a taobao login"""
    config = request.registry.settings
    gh_url = flat_url('https://oauth.taobao.com/authorize',
                      client_id=config['velruse.taobao.app_id'],
                      response_type='code',
                      redirect_uri=request.route_url('taobao_process'))
    return HTTPFound(location=gh_url)


def taobao_process(request):
    """Process the taobao redirect"""
    config = request.registry.settings
    code = request.GET.get('code')
    if not code:
        reason = request.GET.get('error', 'No reason provided.')
        return AuthenticationDenied(reason)

    # Now retrieve the access token with the code
    r = requests.post('https://oauth.taobao.com/token',
            dict(grant_type='authorization_code',
                 client_id=config['velruse.taobao.app_id'],
                 client_secret=config['velruse.taobao.app_secret'],
                 redirect_uri=request.route_url('taobao_process'),
                 code=code))
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    data = loads(r.content)
    access_token = data['access_token']

    # Retrieve profile data
    params = {
            'method': 'taobao.user.get',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'format': 'json',
            'app_key': config['velruse.taobao.app_id'],
            'v': '2.0',
            'sign_method': 'md5',
            'fields': 'user_id,nick',
            'session': access_token
            }
    src = config['velruse.taobao.app_secret']\
            + ''.join(["%s%s" % (k, v) for k, v in sorted(params.items())])\
            + config['velruse.taobao.app_secret']
    params['sign'] = md5(src).hexdigest().upper()
    get_user_info_url = flat_url('http://gw.api.taobao.com/router/rest',
                                 **params)
    r = requests.get(get_user_info_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    data = loads(r.content)

    username = data['user_get_response']['user']['nick']
    userid = data['user_get_response']['user']['user_id']

    profile = {
        'accounts': [{'domain':'taobao.com', 'userid':userid}],
        'displayName': username,
        'preferredUsername': username,
    }

    cred = {'oauthAccessToken': access_token}
    return TaobaoAuthenticationComplete(profile=profile, credentials=cred)
