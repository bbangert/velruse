from __future__ import absolute_import

from openid.consumer import consumer

from pyramid.security import NO_PERMISSION_REQUIRED

from ..api import (
    register_provider,
    AuthenticationDenied,
)

from ..exceptions import ThirdPartyFailure

from .openid import (
    OpenIDAuthenticationComplete,
    OpenIDConsumer,
)


class SteamAuthenticationComplete(OpenIDAuthenticationComplete):
    """ Steam auth complete """
    def __init__(self, claimed_id, provider_name, provider_type):
        self.claimed_id = claimed_id
        self.provider_name = provider_name
        self.provider_type = provider_type


class SteamAuthenticationDenied(AuthenticationDenied):
    """ Steam auth denied """


def includeme(config):
    config.add_directive('add_steam_login', add_steam_login)


def add_steam_login(config,
                    name='steam',
                    realm=None,
                    storage=None,
                    login_path='/login/steam',
                    callback_path='/login/steam/callback'):
    """ Add a Steam login provider to the application """
    provider = SteamConsumer(name, realm, storage)

    config.add_route(provider.login_route, login_path)
    config.add_view(provider, attr='login', route_name=provider.login_route,
                    permission=NO_PERMISSION_REQUIRED)

    config.add_route(provider.callback_route, callback_path,
                     use_global_views=True, factory=provider.callback)

    register_provider(config, name, provider)


class SteamConsumer(OpenIDConsumer):
    def __init__(self, name, realm=None, storage=None):
        """ Handle Steam auth """
        super(SteamConsumer, self).__init__(name, 'steam', realm, storage,
                                            context=SteamAuthenticationComplete)

    def _lookup_identifier(self, request, identifier):
        """ Return the Steam OpenID directed endpoint """
        return 'http://steamcommunity.com/openid'

    def callback(self, request):
        """ Handle incoming redirect from Steam OpenID """
        openid_session = request.session.pop('velruse.openid_session', None)

        if not openid_session:
            raise ThirdPartyFailure('No OpenID session has begun')

        # Setup the consumer and parse the information coming back
        oidconsumer = consumer.Consumer(openid_session, self.openid_store)
        return_to = request.route_url(self.callback_route)
        info = oidconsumer.complete(request.params, return_to)

        if info.status in [consumer.FAILURE, consumer.CANCEL]:
            return SteamAuthenticationDenied('OpenID failure',
                                             provider_name=self.name,
                                             provider_type=self.type)
        elif info.status == consumer.SUCCESS:
            claimed_id = str(info.identity_url)
            return SteamAuthenticationComplete(claimed_id=claimed_id,
                                               provider_name=self.name,
                                               provider_type=self.type)
        else:
            raise ThirdPartyFailure('OpenID failed')
