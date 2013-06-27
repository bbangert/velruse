Google OAuth2.0 - :mod:`velruse.providers.google_oauth2`
========================================================

Google Developer Links:

* `Google Application Management
  <https://www.google.com/accounts/ManageDomains>`__
* `Configuring OAuth2.0 in Your Application
  <https://developers.google.com/accounts/docs/OAuth2>`__


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
