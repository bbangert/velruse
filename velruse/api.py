"""Velruse Authentication API"""


class AuthenticationComplete(object):
    """An AuthenticationComplete context object

    """
    def __init__(self, profile=None, credentials=None):
        """Create an AuthenticationComplete object with user data"""
        self.profile = profile
        self.credentials = credentials
