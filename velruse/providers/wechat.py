"""WeChat Authentication Views"""
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


class WeChatAuthenticationComplete(AuthenticationComplete):
    """WeChat auth complete"""


def includeme(config):
    config.add_directive('add_wechat_login', add_wechat_login)
    config.add_directive('add_wechat_login_from_settings',
                         add_wechat_login_from_settings)


def add_wechat_login_from_settings(config, prefix='velruse.wechat.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    config.add_wechat_login(**p.kwargs)


def add_wechat_login(config,
                     consumer_key,
                     consumer_secret,
                     scope='snsapi_base',
                     login_path='/login/wechat',
                     callback_path='/login/wechat/callback',
                     name='wechat'):
    """
    Add a WeChat login provider to the application.
    """
    provider = WeChatProvider(name, consumer_key, consumer_secret, scope)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class WeChatProvider(object):
    def __init__(self, name, consumer_key, consumer_secret, scope):
        self.name = name
        self.type = 'wechat'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a qq login"""
        scope = request.POST.get('scope', self.scope)
        request.session['velruse.state'] = state = uuid.uuid4().hex
        url = flat_url('https://open.weixin.qq.com/connect/oauth2/authorize',
                       scope=scope,
                       appid=self.consumer_key,
                       response_type='code',
                       redirect_uri=request.route_url(self.callback_route),
                       state=state)
        url += '#wechat_redirect'
        return HTTPFound(location=url)

    def callback(self, request):
        """Process the qq redirect"""
        sess_state = request.session.pop('velruse.state', None)
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
            reason = request.GET.get('error', 'No reason provided.')
            return AuthenticationDenied(reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        # Now retrieve the access token with the code
        access_url = flat_url(
            'https://api.weixin.qq.com/sns/oauth2/access_token',
            appid=self.consumer_key,
            secret=self.consumer_secret,
            grant_type='authorization_code',
            code=code)
        r = requests.get(access_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        token_data = r.json()
        access_token = token_data['access_token']
        openid = token_data['openid']

        # Retrieve profile data
        graph_url = flat_url('https://api.weixin.qq.com/sns/userinfo',
                             access_token=access_token,
                             openid=openid)
        r = requests.get(graph_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        data = r.json()
        profile = {
            'accounts': [{'domain': 'wexin.qq.com', 'userid': openid}],
            'gender': data['sex'],
            'displayName': data['nickname'],
            'preferredUsername': data['nickname'],
            'avatar': data['headimgurl'],
            'data': data
        }
        cred = {'oauthAccessToken': access_token}
        return WeChatAuthenticationComplete(profile=profile,
                                            credentials=cred,
                                            provider_name=self.name,
                                            provider_type=self.type)
