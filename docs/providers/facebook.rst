Facebook - :mod:`velruse.providers.facebook`
============================================

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

.. automodule:: velruse.providers.facebook

   .. autoclass:: FacebookAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_facebook_login

   .. autofunction:: add_facebook_login_from_settings
