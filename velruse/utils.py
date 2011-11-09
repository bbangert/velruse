"""Utilities for the auth functionality"""
import urllib
import uuid

from velruse.baseconvert import base_encode


def flat_url(url, **kw):
    """Creates a URL with the query param encoded"""
    url += '?' + urllib.urlencode(kw)
    return url


def redirect_form(end_point, token):
    """Generate a redirect form for POSTing"""
    return """
<form action="%s" method="post" accept-charset="UTF-8"
 enctype="application/x-www-form-urlencoded">
<input type="hidden" name="token" value="%s" />
<input type="submit" value="Continue"/></form>
""" % (end_point, token)


def generate_token():
    """Generate a random token"""
    return base_encode(uuid.uuid4().int)


def splitlines(s):
    return filter(None, [x.strip() for x in s.splitlines()])
