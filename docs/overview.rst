.. _overview:

========
Overview
========

Velruse aims to simplify authenticating a user. It provides
:term:`auth provider`'s that handle authenticating to a variety of
identity providers with multiple authentication schemes (LDAP, SAML,
etc.).

Eventually, Velruse will include widgets similar to `RPXNow`_ that
allow one to customize a login/registration widget so that a website
user can select a preferred identity provider to use to sign-in.

In the mean-time, effort is focused on increasing the available
:term:`auth provider`'s for the commonly used authentication schemes
and identity providers (Facebook, Google, OpenID, etc).

Unlike other authentication libraries for use with web applications,
a website using Velruse for authentication **does not have to be
written in any particular language**.


API
===

Velruse implements an API similar to `RPXNow`_ to standardize the way a
web application handles user authentication. The standard flow of using
Velruse looks like this:

.. image:: _static/overview.png
   :alt: Velruse Authentication flow
   :align: center

1. Website sends a POST to the :term:`auth provider`'s URL with an endpoint
   that the user should be redirected back to when authentication is complete
   and includes any additional parameters that the :term:`auth provider`
   requires.
2. When the :term:`auth provider` finishes the authentication, the user is
   redirected back to the endpoint specified with a POST, which includes the
   user's authentication data.


Using in a Pyramid App
======================

.. code-block:: python

    config.include('velruse.providers.google')
    config.add_google_login(realm='http://www.example.com/')

You can get the login url with :func:`velruse.api.login_url` like so:

.. code-block:: python

    login_url(request, 'google')

In this case, the login url handler will be at
http://www.example.com/login/google. Go to that url to login via the Google
provider.

.. warning::

    In order to get working code examples, you will probably need to change the
    realm to something sensible. Maybe "localhost" would work for testing.


Using Separate App as a Service
===============================


.. _RPXNow: http://rpxnow.com/
