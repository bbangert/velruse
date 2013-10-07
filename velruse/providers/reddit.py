"""Reddit Authentication Views"""
import uuid

from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED

import requests

from ..api import (
    AuthenticationComplete,
    AuthenticationDenied,
    register_provider,
)
from ..exceptions import CSRFError
from ..exceptions import ThirdPartyFailure
from ..settings import ProviderSettings
from ..utils import flat_url


class RedditAuthenticationComplete(AuthenticationComplete):
    """Reddit auth complete"""


def includeme(config):
    config.add_directive('add_reddit_login', add_reddit_login)
    config.add_directive('add_reddit_login_from_settings',
                         add_reddit_login_from_settings)


def add_reddit_login_from_settings(config, prefix='velruse.reddit.'):
    settings = config.registry.settings
    p = ProviderSettings(settings, prefix)
    p.update('consumer_key', required=True)
    p.update('consumer_secret', required=True)
    p.update('user_agent')
    p.update('scope')
    p.update('login_path')
    p.update('callback_path')
    p.update('domain')
    config.add_reddit_login(**p.kwargs)


def add_reddit_login(config,
                     consumer_key,
                     consumer_secret,
                     scope='identity',
                     login_path='/login/reddit',
                     callback_path='/login/reddit/callback',
                     domain='reddit.com',
                     name='reddit',
                     user_agent='velruse'):
    """
    Add a Reddit login provider to the application.
    """
    provider = RedditProvider(name,
                              consumer_key,
                              consumer_secret,
                              scope,
                              domain,
                              user_agent)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)


class RedditProvider(object):
    def __init__(self,
                 name,
                 consumer_key,
                 consumer_secret,
                 scope,
                 domain,
                 user_agent):
        self.name = name
        self.type = 'reddit'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope
        self.protocol = 'https'
        self.domain = domain
        self.user_agent = user_agent

        self.login_route = 'velruse.{name}-login'.format(name=name)
        self.callback_route = 'velruse.{name}-callback'.format(name=name)

    def login(self, request):
        """Initiate a reddit login"""
        scope = request.POST.get('scope', self.scope)
        request.session['velruse.state'] = state = uuid.uuid4().hex
        reddit_url = flat_url(
            '{protocol}://ssl.{domain}/api/v1/authorize'.format(
                protocol=self.protocol,
                domain=self.domain
            ),
            scope=scope,
            client_id=self.consumer_key,
            redirect_uri=request.route_url(self.callback_route),
            response_type='code',
            duration='permanent',
            state=state)
        return HTTPFound(location=reddit_url)

    def callback(self, request):
        """Process the reddit redirect"""
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
            return AuthenticationDenied(reason=reason,
                                        provider_name=self.name,
                                        provider_type=self.type)

        # Now retrieve the access token with the code
        access_url = '{protocol}://ssl.{domain}/api/v1/access_token'.format(
            protocol=self.protocol,
            domain=self.domain
        )
        post_data = dict(redirect_uri=request.route_url(self.callback_route),
                         grant_type='authorization_code',
                         code=code)
        headers = {'User-Agent': self.user_agent}
        r = requests.post(access_url, data=post_data, auth=(self.consumer_key,
                          self.consumer_secret), headers=headers)
        if r.status_code != 200:
            raise ThirdPartyFailure(
                "Status {code}: {content}".format(
                    code=r.status_code,
                    content=r.content
                )
            )

        token_data = r.json()
        access_token = token_data['access_token']
        headers.update({
            'Authorization': 'Bearer {token}'.format(token=access_token)
        })
        api_url = '{protocol}://oauth.{domain}/api/v1/'.format(
            protocol=self.protocol,
            domain=self.domain
        )
        api_method = 'me'
        api_full_url = '{url}{method}'.format(
            url=api_url,
            method=api_method
        )

        # Retrieve profile data
        r = requests.get(api_full_url, headers=headers)
        if r.status_code != 200:
            raise ThirdPartyFailure(
                "Status {code}: {content}".format(
                    code=r.status_code,
                    content=r.content
                )
            )

        profile_data = r.json()
        profile = {}
        profile['accounts'] = [{
            'domain': self.domain,
            'username': profile_data['name'],
            'userid': profile_data['id']
        }]

        profile['preferredUsername'] = profile_data['name']
        profile['displayName'] = profile_data['name']

        cred = {'oauthAccessToken': access_token}
        return RedditAuthenticationComplete(profile=profile,
                                            credentials=cred,
                                            provider_name=self.name,
                                            provider_type=self.type)
