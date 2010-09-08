"""Utilities for the auth functionality"""
import sys
import uuid

try:
    import simplejson as json
except ImportError:
    import json

import webob.exc as exc
from routes import URLGenerator
from openid.oidutil import autoSubmitHTML
from webob import Response

from velruse.baseconvert import base_encode
from velruse.errors import error_dict


def redirect_form(end_point, token):
    """Generate a redirect form for POSTing"""
    return """
<form action="%s" method="post" accept-charset="UTF-8" enctype="application/x-www-form-urlencoded">
<input type="hidden" name="token" value="%s" />
<input type="submit" value="Continue"/></form>
""" % (end_point, token)


def generate_token():
    """Generate a random token"""
    return base_encode(uuid.uuid4().int)


def load_package_obj(package_obj_string):
    """Extract a package name and object name, import the package and return
    the object from that package by name.

    The format is velruse.store.memstore:MemoryStore.
    """
    package_name, obj_name = package_obj_string.split(':')
    __import__(package_name)
    return getattr(sys.modules[package_name], obj_name)


# Copied from Paste
def path_info_pop(environ):
    """
    'Pops' off the next segment of PATH_INFO, pushing it onto
    SCRIPT_NAME, and returning that segment.

    For instance::

        >>> def call_it(script_name, path_info):
        ...     env = {'SCRIPT_NAME': script_name, 'PATH_INFO': path_info}
        ...     result = path_info_pop(env)
        ...     print 'SCRIPT_NAME=%r; PATH_INFO=%r; returns=%r' % (
        ...         env['SCRIPT_NAME'], env['PATH_INFO'], result)
        >>> call_it('/foo', '/bar')
        SCRIPT_NAME='/foo/bar'; PATH_INFO=''; returns='bar'
        >>> call_it('/foo/bar', '')
        SCRIPT_NAME='/foo/bar'; PATH_INFO=''; returns=None
        >>> call_it('/foo/bar', '/')
        SCRIPT_NAME='/foo/bar/'; PATH_INFO=''; returns=''
        >>> call_it('', '/1/2/3')
        SCRIPT_NAME='/1'; PATH_INFO='/2/3'; returns='1'
        >>> call_it('', '//1/2')
        SCRIPT_NAME='//1'; PATH_INFO='/2'; returns='1'

    """
    path = environ.get('PATH_INFO', '')
    if not path:
        return None
    while path.startswith('/'):
        environ['SCRIPT_NAME'] += '/'
        path = path[1:]
    if '/' not in path:
        environ['SCRIPT_NAME'] += path
        environ['PATH_INFO'] = ''
        return path
    else:
        segment, path = path.split('/', 1)
        environ['PATH_INFO'] = '/' + path
        environ['SCRIPT_NAME'] += segment
        return segment    


class RouteResponder(object):
    """RouteResponder for Routes-based dispatching Responder"""
    def __call__(self, req):
        """Handle being called with a request object"""
        results = self.map.routematch(environ=req.environ)
        if not results:
            return exc.HTTPNotFound()
        match = results[0]
        kwargs = match.copy()
        link = URLGenerator(self.map, req.environ)
        req.environ['wsgiorg.routing_args'] = ((), match)
        req.link = link
        self.map.environ = req.environ
        action = kwargs.pop('action')
        return getattr(self, action)(req, **kwargs)
    
    def _error_redirect(self, error_code, end_point):
        """Redirect the user to the endpoint, save the error
        status to the storage under the token"""
        token = generate_token()
        self.storage.store(token, error_dict(error_code), expires=300)
        form_html = redirect_form(end_point, token)
        return Response(body=autoSubmitHTML(form_html))
    
    def _success_redirect(self, user_data, end_point):
        """Redirect the user to the endpoint, save the user_data to a new
        random token in storage"""
        # Generate the token, store the extracted user-data for 5 mins, and send back
        token = generate_token()
        self.storage.store(token, user_data, expires=300)
        form_html = redirect_form(end_point, token)
        return Response(body=autoSubmitHTML(form_html))

    def _get_return_to(self, req):
        if self.protocol:
            return_to = req.link('process', qualified=True, protocol=self.protocol)
        else:
            return_to = req.link('process', qualified=True)
        return return_to


class _Missing(object):
    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'

_missing = _Missing()

class cached_property(object):
    """A decorator that converts a function into a lazy property.  The
    function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value::

        class Foo(object):

            @cached_property
            def foo(self):
                # calculate something important here
                return 42

    The class has to have a `__dict__` in order for this property to
    work.

    """
    # implementation detail: this property is implemented as non-data
    # descriptor.  non-data descriptors are only invoked if there is
    # no entry with the same name in the instance's __dict__.
    # this allows us to completely get rid of the access function call
    # overhead.  If one choses to invoke __get__ by hand the property
    # will still work as expected because the lookup logic is replicated
    # in __get__ for manual invocation.

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value
