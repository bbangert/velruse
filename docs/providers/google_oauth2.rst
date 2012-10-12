Google OAuth2.0
===============

Google provides both basic OpenID using Attribute Exchange 2.0, as well
as a OpenID+OAuth hybrid that authenticates a user and completes OAuth
authentication to provide API access to Google services.

To use Google authentication, registering an application is *not*
necessary unless you wish to request OAuth tokens to access Google
services.

Google Developer Links:

* `Google Application Management
  <https://www.google.com/accounts/ManageDomains>`_
* `Google OpenID Documentation
  <http://code.google.com/apis/accounts/docs/OpenID.html>`_
* `Google OAuth scope parameters
  <http://code.google.com/apis/gdata/faq.html#AuthScopes>`_


Settings
--------

``consumer_key``
    Google application consumer key.

``consumer_secret``
    Google application consumer secret.

``scope``
    Authorization scope.

POST Parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/google/login" method="post">
        <input type="submit" value="Login with Google" />
    </form>

Pyramid API
-----------

.. automodule:: velruse.providers.google_oauth2

   .. autoclass:: GoogleAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_google_login
