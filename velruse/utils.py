"""Utilities for the auth functionality"""
import urllib


def flat_url(url, **kw):
    """Creates a URL with the query param encoded"""
    url += '?' + urllib.urlencode(kw)
    return url
