"""Sina Microblogging weibo.com Authentication Views"""
import uuid
from json import loads

import requests

from pyramid.httpexceptions import HTTPFound

from velruse.api import AuthenticationComplete
from velruse.api import register_provider
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import CSRFError
from velruse.exceptions import ThirdPartyFailure
from velruse.utils import flat_url


class WeiboAuthenticationComplete(AuthenticationComplete):
    """Weibo auth complete"""

def includeme(config):
    config.add_directive('add_weibo_login', add_weibo_login)

def add_weibo_login(config,
                     consumer_key,
                     consumer_secret,
                     login_path='/login/weibo',
                     callback_path='/login/weibo/callback',
                     name='weibo'):
    """
    Add a Weibo login provider to the application.
    """
    provider = WeiboProvider(name, consumer_key, consumer_secret)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider.login, route_name=provider.login_route)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True,
                     factory=provider.callback)

    register_provider(config, name, provider)

class WeiboProvider(object):
    def __init__(self, name, consumer_key, consumer_secret):
        self.name = name
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        self.login_route = 'velruse.%s-login' % name
        self.callback_route = 'velruse.%s-callback' % name

    def login(self, request):
        """Initiate a weibo login"""
        request.session['state'] = state = uuid.uuid4().hex
        fb_url = flat_url('https://api.weibo.com/oauth2/authorize',
                          client_id=self.consumer_key,
                          redirect_uri=request.route_url(self.callback_route),
                          state=state)
        return HTTPFound(location=fb_url)


    def callback(self, request):
        """Process the weibo redirect"""
        if request.GET.get('state') != request.session.get('state'):
            raise CSRFError("CSRF Validation check failed. Request state %s is "
                            "not the same as session state %s" % (
                            request.GET.get('state'), request.session.get('state')
                            ))
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error_reason', 'No reason provided.')
            return AuthenticationDenied(reason)

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
        data = loads(r.content)
        access_token = data['access_token']
        uid = data['uid']

        # Retrieve profile data
        graph_url = flat_url('https://api.weibo.com/2/users/show.json',
                                access_token=access_token,
                                uid=uid)
        r = requests.get(graph_url)
        if r.status_code != 200:
            raise ThirdPartyFailure("Status %s: %s" % (
                r.status_code, r.content))
        data = loads(r.content)

        profile = {
            'accounts': [{'domain':'weibo.com', 'userid':data['id']}],
            'gender': data.get('gender'),
            'displayName': data['screen_name'],
            'preferredUsername': data['name'],
        }

        cred = {'oauthAccessToken': access_token}
        return WeiboAuthenticationComplete(profile=profile, credentials=cred)
