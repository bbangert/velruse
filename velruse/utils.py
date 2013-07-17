"""Utilities for the auth functionality"""
from .compat import urlencode

def flat_url(url, **kw):
    """Creates a URL with the query param encoded"""
    return url + '?' + urlencode(kw)
