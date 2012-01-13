.. _providers:

=========
Providers
=========

Authentication Providers supply varying levels of information when
authentication has occurred. Some of them can also provide API access
tokens in addition to authenticating a user for sign-on.

Facebook (velruse.providers.facebook)
=====================================

The Facebook provider authenticates using the latest Facebook OAuth 2.0
API with the Social Graph API to obtain additional profile information
for use with user registration.

To use the Facebook authentication, you must register a Facebook application
for use with Velruse.

Facebook Developer Links:

* `Developer Group (View apps, create app)
  <http://www.facebook.com/#!/developers/>`_
* `Facebook Application Management
  <http://www.facebook.com/developers/#!/developers/apps.php>`_
* `Create new Facebook Application
  <http://www.facebook.com/developers/createapp.php>`_

Settings
--------

velruse.facebook.consumer_key
    Facebook App Id
velruse.facebook.consumer_secret
    Facebook secret
velruse.facebook.scope
    Optional comma-separated list of extended permissions.

All of these parameters are necessary. The Facebook Connect URL
registered with Facebook must match the domain that the velruse
application is served from.

POST parameters
---------------

The Facebook provider accepts a scope argument, which is used in the
authenticating request to access additional Facebook properties known
as `Extended Permissions
<http://developers.facebook.com/docs/authentication/permissions>`_.
These should be a comma separated string, for example:

.. code-block:: html

    <input type="hidden" name="scope" value="publish_stream,create_event" />

Complete Example:

.. code-block:: html

    <form action="/velruse/facebook/auth" method="post">
        <input type="hidden" name="scope" value="publish_stream,create_event" />
        <input type="submit" value="Login with Facebook" />
    </form>


OpenID (velruse.providers.openid)
==================================

The OpenID provider does standard OpenID authentication, using both the
`Simple Registration Extension
<http://openid.net/specs/openid-simple-registration-extension-1_0.html>`_
and many of the `Attribute Exchange <http://www.axschema.org/types/>`_
attributes to acquire as much user information to assist in the
authentication process as possible.

OpenID Developer Links:

* `OpenID Authentication 2.0
  <http://openid.net/specs/openid-authentication-2_0.html>`_
* `Attribute Exchange 1.0
  <http://openid.net/specs/openid-attribute-exchange-1_0.html>`_

Settings
--------

velruse.openid.realm
    Domain for your website, e.g. `http://yourdomain.com/`
velruse.openid.store
    A class from which the OpenID store will be instantiated.

.. note::

    The OpenID store is a different store to the Velruse store.
    Please see the :mod:`python-openid` documentation for details.

POST Parameters
---------------

The OpenID provider accepts `openid_identifier` which should designate
the OpenID identifer being claimed to authenticate.

Complete Example:

.. code-block:: html

    <form action="/velruse/openid/login" method="post">
    <input type="text" name="openid_identifier" />
    <input type="submit" value="Login with OpenID" />
    </form>


Google (velruse.providers.google)
==================================

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

The Google provider requires that an OpenID provider configuration be
present in your configuration file in order to provide the ``Realm``
and ``Store`` configuration values.

The following are only required if using the OAuth hybrid:

velruse.google.consumer_key
    The consumer key, e.g. `yourdomain.com`
velruse.google.consumer_secret
    Consumer secret as specified
velruse.google.oauth_scope

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
`Google Auth Scopes <http://code.google.com/apis/gdata/faq.html#AuthScopes>`_
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


Yahoo (velruse.providers.yahoo)
=================================

Like Google, Yahoo offers either plain OpenID for authentication or an
OpenID+OAuth hybrid authentication granting access to Yahoo applications
while authenticating a user for sign-on. Unlike Google, Yahoo requires
the application to register in advance the scope of the API token to
issue. Using the Yahoo OAuth requires registration of a Yahoo application.

Yahoo Developer Links:

* `Yahoo Developer Projects Page (Create new apps here)
  <https://developer.apps.yahoo.com/projects>`_
* `Yahoo OpenID + OAuth Guide
  <http://developer.yahoo.com/oauth/guide/openid-oauth-guide.html>`_

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

velruse.yahoo.consumer_key
    Yahoo consumer key
velruse.yahoo.consumer_secret
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

Twitter (velruse.providers.twitter)
==========================================

The Twitter provider combines authentication with OAuth authorization.
It requires a Twitter Application to have been created to use. Twitter
only provides the twitter screen name and id, along with an OAuth
access token.

Twitter Developer Links:

* `Register a New Twitter Application <http://dev.twitter.com/apps/new>`_
* `Twitter OAuth API <http://dev.twitter.com/doc>`_

Settings
--------

velruse.twitter.consumer_key
    Twitter application consumer key
velruse.twitter.consumer_secret
    Twitter application secret
velruse.twitter.authorization
    github application scope

POST Parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/twitter/login" method="post">
    <input type="submit" value="Login with Twitter" />
    </form>

Github (velruse.providers.github)
==================================

The Github provider combines authentication with OAuth authorization.
It requires a Github Application to have been created to use.

github Links:

* `Register a New Github Application
  <https://github.com/account/applications/new>`_
* `Github OAuth API <http://develop.github.com/p/oauth.html>`_

Settings
--------

velruse.github.consumer_key
    github application consumer key
velruse.github.consumer_secret
    github application secret
velruse.github.scope
    github application scope

POST Parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/github/login" method="post">
    <input type="submit" value="Login with Twitter" />
    </form>


Windows Live (velruse.providers.live)
========================================================

The Windows Live Provider supports the Windows Live OAuth 2.0 API.

.. note::

    The Return URL for velruse must be registered with Live Services
    as **Return URL**.

    Example Return URL::

        http://YOURDOMAIN.COM/velruse/live/process


Windows Live Developer Links:

* `Windows Live <http://msdn.microsoft.com/en-us/windowslive/default.aspx>`_
* `Windows Live OAuth 2.0 SDK
  <http://msdn.microsoft.com/en-us/library/hh243647.aspx>`_

Settings
--------

velruse.live.client_id
    Component Application ID

velruse.live.client_secret
    Component Secret Key

velruse.live.scope
    Delegated auth Offers, e.g. `Contacts.View`
    The `Offers` parameter is optional to invoke Delegated Authentication.

POST Parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/live/auth" method="post">
    <input type="submit" value="Login with Windows Live" />
    </form>
