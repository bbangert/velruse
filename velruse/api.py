"""Velruse Authentication API"""
class AuthenticationComplete(object):
    """An AuthenticationComplete context object

    """
    def __init__(self, profile=None, credentials=None):
        """Create an AuthenticationComplete object with user data"""
        self.profile = profile
        self.credentials = credentials


class BitbucketAuthenticationComplete(AuthenticationComplete):
    """Bitbucket auth complete"""


class FacebookAuthenticationComplete(AuthenticationComplete):
    """Facebook auth complete"""


class GithubAuthenticationComplete(AuthenticationComplete):
    """Github auth complete"""


class LinkedInAuthenticationComplete(AuthenticationComplete):
    """LinkedIn auth complete"""


class TwitterAuthenticationComplete(AuthenticationComplete):
    """Twitter auth complete"""


class OpenIDAuthenticationComplete(AuthenticationComplete):
    """OpenID auth complete"""


class GoogleAuthenticationComplete(OpenIDAuthenticationComplete):
    """Google auth complete"""


class YahooAuthenticationComplete(OpenIDAuthenticationComplete):
    """Yahoo auth complete"""
