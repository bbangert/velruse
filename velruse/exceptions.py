"""Velruse Exceptions"""
class VelruseException(Exception):
    """Base Velruse Exception"""


class ThirdPartyFailure(VelruseException):
    """Raised when the third party authentication fails to return expected
    data"""


class AuthenticationDenied(VelruseException):
    """Raised when the third party returns properly, but authentication was
    not granted"""


class CSRFError(VelruseException):
    """Raised when CSRF validation fails"""


class AuthenticationComplete(VelruseException):
    """Raised when authentication is complete

    Will have attributes set as appropriate for the authentication method.

    """
