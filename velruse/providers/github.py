"""Github Authentication Views"""
from json import loads
from urlparse import parse_qs

import requests

from pyramid.httpexceptions import HTTPFound

from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url


class GithubAuthenticationComplete(AuthenticationComplete):
    """Github auth complete"""


def includeme(config):
    config.add_route("github_login", "/github/login")
    config.add_route("github_process", "/github/process",
                     use_global_views=True,
                     factory=github_process)
    config.add_view(github_login, route_name="github_login")


def github_login(request):
    """Initiate a github login"""
    config = request.registry.settings
    scope = config.get('velruse.github.scope',
                       request.POST.get('scope', ''))
    gh_url = flat_url('https://github.com/login/oauth/authorize', scope=scope,
                      client_id=config['velruse.github.app_id'],
                      redirect_uri=request.route_url('github_process'))
    return HTTPFound(location=gh_url)


def github_process(request):
    """Process the github redirect"""
    config = request.registry.settings
    code = request.GET.get('code')
    if not code:
        reason = request.GET.get('error', 'No reason provided.')
        return AuthenticationDenied(reason)

    # Now retrieve the access token with the code
    access_url = flat_url('https://github.com/login/oauth/access_token',
                          client_id=config['velruse.github.app_id'],
                          client_secret=config['velruse.github.app_secret'],
                          redirect_uri=request.route_url('github_process'),
                          code=code)
    r = requests.get(access_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    access_token = parse_qs(r.content)['access_token'][0]

    # Retrieve profile data
    graph_url = flat_url('https://github.com/api/v2/json/user/show',
                         access_token=access_token)
    r = requests.get(graph_url)
    if r.status_code != 200:
        raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
    data = loads(r.content)['user']

    profile = {}
    profile['accounts'] = [{
        'domain':'github.com',
        'username':data['login'],
        'userid':data['id']
    }]
    profile['displayName'] = data['name']
    profile['preferredUsername'] = data['login']

    # We don't add this to verifiedEmail because ppl can change email addresses
    # without verifying them
    if 'email' in data:
        profile['emails'] = [{'value':data['email']}]

    cred = {'oauthAccessToken': access_token}
    return GithubAuthenticationComplete(profile=profile,
                                        credentials=cred)
