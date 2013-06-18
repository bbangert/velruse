"""Sina Microblogging weibo.com Authentication Views"""
import uuid

import requests

from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED


from ..api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from ..exceptions import CSRFError
from ..exceptions import ThirdPartyFailure
from ..settings import ProviderSettings
from ..utils import flat_url


class WeiboAuthenticationComplete(AuthenticationComplete):
    """Weibo auth complete"""


def includeme(config):
    config.add_directive('add_weibo_login', add_weibo_login)
    config.add_directive('add_weibo_login_from_settings',
                         add_weibo_login_from_settings)


def add_weibo_login_from_settings(config, prefix='velruse.weibo.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    config.add_weibo_login(**p.kwargs)


def add_weibo_login(config,
                    consumer_key,
                    consumer_secret,
                    scope=None,
                    login_path='/login/weibo',
                    callback_path='/login/weibo/callback',
                    name='weibo'):
    """
    Add a Weibo login provider to the application.
    """
    provider = WeiboProvider(name, consumer_key, consumer_secret, scope)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class WeiboProvider(object):
    def __init__(self, name, consumer_key, consumer_secret, scope):
        self.name = name
        self.type = 'weibo'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a weibo login"""
        scope = request.POST.get('scope', self.scope)
        request.session['state'] = state = uuid.uuid4().hex
        url = flat_url('https://api.weibo.com/oauth2/authorize',
                       scope=scope,
                       client_id=self.consumer_key,
                       response_type='code',
                       redirect_uri=request.route_url(self.callback_route),
                       state=state)
        return HTTPFound(url)

    def callback(self, request):
        """Process the weibo redirect"""
        sess_state = request.session.get('state')
        req_state = request.GET.get('state')
        if not sess_state or sess_state != req_state:
            raise CSRFError(
                'CSRF Validation check failed. Request state {req_state} is '
                'not the same as session state {sess_state}'.format(
                    req_state=req_state,
                    sess_state=sess_state
                )
            )
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error_reason', 'No reason provided.')
            return AuthenticationDenied(reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        # Now retrieve the access token with the code
        r = requests.post(
            'https://api.weibo.com/oauth2/access_token',
            dict(
                client_id=self.consumer_key,
                client_secret=self.consumer_secret,
                redirect_uri=request.route_url(self.callback_route),
                grant_type='authorization_code',
                code=code,
            ),
        )
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        token_data = r.json()
        access_token = token_data['access_token']
        user_id = token_data['uid']

        # Retrieve profile data
        graph_url = flat_url('https://api.weibo.com/2/users/show.json',
                             access_token=access_token,
                             uid=user_id)
        r = requests.get(graph_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        data = r.json()

        profile = {
            'accounts': [{'domain': 'weibo.com', 'userid': data['id']}],
            'gender': data.get('gender'),
            'displayName': data['screen_name'],
            'preferredUsername': data['name'],
            'avatar': data['avatar_large'],
            'data': data
        }

        cred = {'oauthAccessToken': access_token}
        return WeiboAuthenticationComplete(profile=profile,
                                           credentials=cred,
                                           provider_name=self.name,
                                           provider_type=self.type)
