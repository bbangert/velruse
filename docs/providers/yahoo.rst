Yahoo - :mod:`velruse.providers.yahoo`
======================================

Like Google, Yahoo offers either plain OpenID for authentication or an
OpenID+OAuth hybrid authentication granting access to Yahoo applications
while authenticating a user for sign-on. Unlike Google, Yahoo requires
the application to register in advance the scope of the API token to
issue. Using the Yahoo OAuth requires registration of a Yahoo application.

Yahoo Developer Links:

* `Yahoo Developer Projects Page (Create new apps here)
  <https://developer.apps.yahoo.com/projects>`__
* `Yahoo OpenID + OAuth Guide
  <http://developer.yahoo.com/oauth/guide/openid-oauth-guide.html>`__


Settings
--------

Like Google, the Yahoo provider requires that an OpenID provider
configuration be present in your configuration file in order to provide
the ``Realm`` and ``Store`` configuration values.

.. warning::

    The ``Realm`` must point to a valid DNS name that is resolvable by
    Yahoo's authentication servers. If this is not the case, Yahoo will
    consider the authentication invalid and display an error message.

The following parameters are only required if using the OAuth hybrid:

``consumer_key``
    Yahoo consumer key
``consumer_secret``
    Yahoo secret


POST Parameters
---------------

Since Yahoo declares the scope of OAuth with the application, you only
need to provide the `oauth` POST parameter if you want OAuth to take
place (which requires a Yahoo application to be created, and configured
in the YAML as shown above).

Complete Example:

.. code-block:: html

    <form action="/velruse/yahoo/login" method="post">
        <input type="hidden" name="oauth" value="true" />
        <input type="submit" value="Login with Yahoo" />
    </form>


Pyramid API
-----------

.. automodule:: velruse.providers.yahoo

   .. autoclass:: YahooAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_yahoo_login
