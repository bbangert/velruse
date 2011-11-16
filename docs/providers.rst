.. _providers:

=========
Providers
=========

Authentication Providers supply varying levels of information when
authentication has occurred. Some of them can also provide API access
tokens in addition to authenticating a user for sign-on.

Default POST Parameters
=======================

Almost every provider accepts the POST parameter `end_point`, which is
the URL that the token will be POSTed to when authentication is complete.

Facebook
========

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

velruse.facebook.app_id
    Facebook App Id
velruse.facebook.app_secret
    Facebook secret
velruse.facebook.scope
    Optional comma-separated list of extended permissions.

All of these parameters are necessary. The Facebook Connect URL
registered with Facebook must match the domain that the velruse
application is served from.

POST parameters
---------------

In addition to the standard :term:`end_point`, the Facebook provider
accepts a scope argument, which is used in the authenticating request
to access additional Facebook properties known as `Extended Permissions
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
    

OpenID
======

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

    <form action="/velruse/openid/auth" method="post">
    <input type="text" name="openid_identifier" />
    <input type="submit" value="Login with OpenID" />
    </form>


Google
======

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

velruse.google.consumer_key
    The consumer key, e.g. `yourdomain.com`
velruse.google.consumer_secret
    Consumer secret as specified
velruse.google.oauth_scope

YAML Parameters
---------------

The Google Provider requires that an OpenID provider configuration be
present in your configuration file in order to provide the ``Realm``
and ``Endpoint Regex`` configuration values.

The following are only required if using the OAuth hybrid:

OAuth Consumer Key
    The consumer key, e.g. `yourdomain.com`
OAuth Consumer Secret
    Consumer secret as specified

.. warning::

    When using the OAuth hybrid, the consumer key domain *must* match the 
    OpenID `Realm` domain, otherwise Google will not consider the OAuth to
    be valid. If this domain is *not a valid DNS name*, Google will also
    consider it invalid.

If OAuth is not being used, the value of true by itself must be used instead
to enable the Google provider, e.g.:

.. code-block:: yaml
    
    Google: true

POST Parameters
---------------

In addition to the standard :term:`end_point`, the Google provider accepts
a oauth_scope argument, which is used in the authenticating request to
access additional Google API's. Each API has an authentication scope,
defined on the
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
    
    <form action="/velruse/google/auth" method="post">
    <input type="hidden" name="popup_mode" value="popup" />
    <input type="hidden" name="oauth_scope" value="http://www.google.com/m8/feeds/" />
    <input type="submit" value="Login with Google" />
    </form>


Yahoo
=====

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

YAML Parameters
---------------

Like Google, the Yahoo Provider requires that an OpenID provider
configuration be present in your configuration file in order to provide
the ``Realm`` and ``Endpoint Regex`` configuration values.

.. warning::

    Both the ``Realm`` and ``Endpoint Regex`` must point to valid DNS
    names that are resolvable by Yahoo's authentication servers. If this
    is not the case, Yahoo will consider the authentication invalid and
    display an error message.

The following parameters are only required if using the OAuth hybrid:

Consumer Key
    Yahoo consumer key
Consumer Secret
    Yahoo secret

If OAuth is not being used, the value of true by itself must be used instead
to enable the Google provider, e.g.:

.. code-block:: yaml

    Yahoo: true

POST Parameters
---------------

Since Yahoo declares the scope of OAuth with the application, you only
need to provide the `oauth` POST parameter if you want OAuth to take
place (which requires a Yahoo application to be created, and configured
in the YAML as shown above).

Complete Example:

.. code-block:: html
    
    <form action="/velruse/yahoo/auth" method="post">
    <input type="hidden" name="oauth" value="true" />
    <input type="submit" value="Login with Yahoo" />
    </form>

Twitter
=======

The Twitter provider combines authentication with OAuth authorization.
It requires a Twitter Application to have been created to use. Twitter
only provides the twitter screen name and id, along with an OAuth
access token.

Twitter Developer Links:

* `Register a New Twitter Application <http://dev.twitter.com/apps/new>`_
* `Twitter OAuth API <http://dev.twitter.com/doc>`_

YAML Parameters
---------------

Consumer Key
    Twitter application consumer key
Consumer Secret
    Twitter application secret

POST Parameters
---------------

Only the default `end_point` parameter is used.

Complete Example:

.. code-block:: html
    
    <form action="/velruse/twitter/auth" method="post">
    <input type="submit" value="Login with Twitter" />
    </form>


Windows Live
============

The Windows Live Provider handles Windows Live Web Authentication and
Delegated Authentication. Both of these methods of authentication require
a Live Services Component to be registered
`per the 'Registering Your Application' documentation
<http://msdn.microsoft.com/en-us/library/cc287659(v=MSDN.10).aspx>`_.

Delegated authentication will only be performed if the `Offers` YAML
parameter is set.

Login Authentication provides a single unique identifier, while
Delegated Authentication provides the single unique identifier and a
consent token to use to access Live services.

.. note::

    The Windows Live API requires the Python package
    `PyCrypto <http://www.dlitz.net/software/pycrypto/>`_ to be
    installed before using.

.. note::

    The Return URL for velruse must be registered with Live Services
    as **Return URL**.

    Example Return URL::

        http://YOURDOMAIN.COM/velruse/live/process


Windows Live Developer Links:

* `Getting Your Application ID
  <http://msdn.microsoft.com/en-us/library/cc287659(v=MSDN.10).aspx>`_
* `Services Available for Delegated Authentication
  <http://dev.live.com/blogs/liveid/archive/2008/02/25/211.aspx>`_
* `Live Services Management Page
  <http://go.microsoft.com/fwlink/?LinkID=144070>`_

YAML Parameters
---------------

Application ID
    Component Application ID
Secret Key
    Component Secret Key
Policy URL
    Site's Privacy Policy URL, overrides the url specified during registration
    of your application with Live Services.
Return URL
    Site's Return URL, overrides the url specified during registration of 
    your application with Live Services. This is not *YOUR* applicaton's end
    point!  This should only be overriden if your registration url is not
    the velruse url.  For example http://YOURDOMAIN.COM/velruse/live/process.
Offers
    Delegated auth Offers, e.g. `Contacts.View`

The `Offers` parameter is optional to invoke Delegated Authentication.

POST Parameters
---------------

Only the default `end_point` parameter is used.

Complete Example:

.. code-block:: html
    
    <form action="/velruse/live/auth" method="post">
    <input type="submit" value="Login with Windows Live" />
    </form>
