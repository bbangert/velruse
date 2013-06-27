Google Hybrid (OpenID+OAuth) - :mod:`velruse.providers.google_hybrid`
=====================================================================

Google provides both basic OpenID using Attribute Exchange 2.0, as well
as a OpenID+OAuth hybrid that authenticates a user and completes OAuth
authentication to provide API access to Google services.

To use Google authentication, registering an application is *not*
necessary unless you wish to request OAuth tokens to access Google
services.

Google Developer Links:

* `Google Application Management
  <https://www.google.com/accounts/ManageDomains>`__
* `Google OpenID Documentation
  <http://code.google.com/apis/accounts/docs/OpenID.html>`__
* `Google OAuth scope parameters
  <http://code.google.com/apis/gdata/faq.html#AuthScopes>`__


Settings
--------

``realm``
    Required. The realm must be a containing namespace for the callback URL.
``consumer_key``
    OAuth 1.0 key.
``consumer_secret``
    OAuth 1.0 secret.
``scope``
    OAuth 1.0 scope.

.. warning::

    When using the OAuth hybrid, the consumer key domain *must* match the
    OpenID `Realm` domain, otherwise Google will not consider the OAuth to
    be valid. If this domain is *not a valid DNS name*, Google will also
    consider it invalid.


POST Parameters
---------------

The Google provider accepts an oauth_scope argument, which is used in
the authenticating request to access additional Google API's. Each API
has an authentication scope, defined on the
`Google Auth Scopes <http://code.google.com/apis/gdata/faq.html#AuthScopes>`__
page. These should be a *space* separated string, for example to request
access to Google Contacts:

Using the `oauth_scope` parameter requires a registered Google application.

.. code-block:: html

    <input type="hidden" name="oauth_scope" value="http://www.google.com/m8/feeds/" />

Google Provider also accepts a `popup_mode` argument which can be either
`popup` or `x-has-session` as defined in the Google OpenID docs.

The OpenID POST param `openid_identifier` is not required.

Complete Example:

.. code-block:: html

    <form action="/velruse/google/login" method="post">
        <input type="hidden" name="popup_mode" value="popup" />
        <input type="hidden" name="oauth_scope" value="http://www.google.com/m8/feeds/" />
        <input type="submit" value="Login with Google" />
    </form>

Pyramid API
-----------

.. automodule:: velruse.providers.google_hybrid

   .. autoclass:: GoogleAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_google_login
