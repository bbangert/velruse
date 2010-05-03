.. _architecture:

============
Architecture
============

Velruse is designed as several sets of components that work together, and can
be used individually for the authentication style desired.


Provider Templates
==================

Every authentication provider that is available comes with a basic HTML 
template illustrating the parameters it requires in addition to the basic
required ones.


Auth Providers
==============

Auth Providers implement all the messy details of authentication. Since they
listen to HTTP requests underneath their prefix, they can interact with other
systems that require redirects to authenticate.

Implementation Details
----------------------

Each :term:`auth provider` must be a callable. It will be called with a
:class:`webob.Request` instance and must respond with a
:class:`webob.Response` instance.

The Auth Provider is expected to respond to a POST to `/auth`, and then
proceed with the necessary calls and/or redirects necessary to complete
the authentication. 


UserStore Backends
==================

User data that is retrieved is stored in a backend store. This can be
a file store, in memory, or any other method to store a simple key/value
association.

