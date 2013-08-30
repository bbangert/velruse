try:
    STRING_TYPES = (str, unicode)
except NameError: #pragma NO COVER Python >= 3.0
    STRING_TYPES = (str,)

try:
    u = unicode
except NameError: #pragma NO COVER Python >= 3.0
    TEXT = str
    def u(x, encoding='ascii'):
        if isinstance(x, str):
            return x
        if isinstance(x, bytes):
            return x.decode(encoding)
    b = bytes
else: #pragma NO COVER Python < 3.0
    TEXT = unicode
    b = str

try:
    from ConfigParser import ConfigParser
except ImportError: #pragma NO COVER Python >= 3.0
    from configparser import ConfigParser

try:
    from urlparse import parse_qs
except ImportError:
    from urllib.parse import parse_qs

try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
