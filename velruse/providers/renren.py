"""Renren Authentication Views"""
from json import loads
import requests
from pyramid.httpexceptions import HTTPFound
from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url


class RenrenAuthenticationComplete(AuthenticationComplete):
    """Renren auth complete"""


def includeme(config):
    config.add_route("renren_login", "/renren/login")
    config.add_route("renren_process", "/renren/process",
                     use_global_views=True,
                     factory=renren_process)
    config.add_view(renren_login, route_name="renren_login")
    settings = config.registry.settings
    settings['velruse.providers_infos']['velruse.providers.renren']['login'] =   'renren_login'
    settings['velruse.providers_infos']['velruse.providers.renren']['process'] = 'renren_process'



def renren_login(request):
    """Initiate a renren login"""
    config = request.registry.settings
    scope = config.get('velruse.renren.scope',
                       request.POST.get('scope', ''))
    url = flat_url('https://graph.renren.com/oauth/authorize', scope=scope,
                      client_id=config['velruse.renren.app_id'],
                      response_type='code',
                      redirect_uri=request.route_url('renren_process'))
    return HTTPFound(url)


def renren_process(request):
    """Process the renren redirect"""
    config = request.registry.settings
    code = request.GET.get('code')
    if not code:
        reason = request.GET.get('error', 'No reason provided.')
        return AuthenticationDenied(reason)

    access_url = flat_url('https://graph.renren.com/oauth/token',
                          client_id=config['velruse.renren.app_id'],
                          client_secret=config['velruse.renren.app_secret'],
                          grant_type='authorization_code',
                          redirect_uri=request.route_url('renren_process'),
                          code=code)

    r = requests.get(access_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    data = loads(r.content)
    access_token = data['access_token']
    profile = {
        'accounts': [{'domain': 'renren.com', 'userid': data['user']['id']}],
        'displayName': data['user']['name'],
        'preferredUsername': data['user']['name'],
    }

    cred = {'oauthAccessToken': access_token}

    return RenrenAuthenticationComplete(profile=profile, credentials=cred)
