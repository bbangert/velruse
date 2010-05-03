.. _architecture:

============
Architecture
============

Velruse is designed as several sets of components that work together, and can
be used individually for the authentication style desired.


Provider Templates
==================

Every authentication provider that is available comes with a basic HTML 
template illustrating the parameters it requires. The template generally 
includes a logo when its a third party :term:`identity provider` to help
a website user find the preferred authentication option.

.. note::
    
    While most websites will redirect to Velruse to handle the authentication
    for a user to login or register, the authentication can be done anytime
    for 'linking' an account to another provider as well.


Auth Providers
==============

Auth Providers implement all the messy details of authentication. Since they
listen to HTTP requests underneath their prefix, they can interact with other
systems that require redirects to authenticate. When the Auth Provider is done
it redirects back to the endpoint that it was provided with.

Implementation Details
----------------------

Each :term:`auth provider` must be a callable. It will be called with a
:class:`webob.Request` instance and must respond with a
:class:`webob.Response` instance.

The Auth Provider is expected to respond to a POST to `/auth`, and then
proceed with the necessary calls and/or redirects necessary to complete
the authentication.

Auth Provider's are usually setup under the :class:`~velruse.wsgiapp.AuthApp`
WSGI app, which is a minimal WSGI application that can dispatch to several
configured Auth Provider's. This WSGI app can also be configured to serve
user details given a token via HTTPS.


UserStore Backends
==================

User data that is retrieved is stored in a backend store. This can be
a file store, in memory, or any other method to store a simple key/value
association. The user data should persist long enough for the web application
to retrieve it.


Implementation Details
----------------------

UserStore backends need to implement the
:class:`~velruse.store.interface.UserStore` interface to store and retrieve
user information that is acquired by the Auth Provider.
