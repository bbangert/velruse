"""Velruse Exceptions"""
class VelruseException(Exception):
    """Base Velruse Exception"""


class MissingParameter(VelruseException):
	"""Raised when the login process is missing some parameters needed to
	continue"""

class ThirdPartyFailure(VelruseException):
    """Raised when the third party authentication fails to return expected
    data"""


class AuthenticationDenied(VelruseException):
    """Raised when the third party returns properly, but authentication was
    not granted"""


class CSRFError(VelruseException):
    """Raised when CSRF validation fails"""

