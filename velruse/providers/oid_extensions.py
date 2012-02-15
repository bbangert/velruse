"""OpenID Extensions

Additional OpenID extensions for OAuth and UIRequest extensions.

"""
from __future__ import absolute_import

from openid import extension


class UIRequest(extension.Extension):
    """OpenID UI extension"""
    ns_uri = 'http://specs.openid.net/extensions/ui/1.0'
    ns_alias = 'ui'

    def __init__(self, mode=None, icon=False):
        super(UIRequest, self).__init__()
        self._args = {}
        if mode:
            self._args['mode'] = mode
        if icon:
            self._args['icon'] = str(icon).lower()

    def getExtensionArgs(self):
        return self._args


class OAuthRequest(extension.Extension):
    """OAuth extension"""
    ns_uri = 'http://specs.openid.net/extensions/oauth/1.0'
    ns_alias = 'oauth'

    def __init__(self, consumer, scope=None):
        super(OAuthRequest, self).__init__()
        self._args = {'consumer': consumer}
        if scope:
            self._args['scope'] = scope

    def getExtensionArgs(self):
        return self._args
