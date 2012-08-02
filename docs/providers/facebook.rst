============================================
Facebook - :mod:`velruse.providers.facebook`
============================================

The Facebook provider authenticates using the latest Facebook OAuth 2.0
API with the Social Graph API to obtain additional profile information
for use with user registration.

To use the Facebook authentication, you must register a Facebook application
for use with Velruse.  You can do that by using the following links to learn about
and create said application.  Once you have done so, you will be supplied with a
consumer key and a consumer secret specific to Facebook.

Facebook Developer Links:

* `Developer Group (View apps, create app)
  <http://www.facebook.com/#!/developers/>`_
* `Facebook Application Management
  <https://developers.facebook.com/apps>`_


Settings
--------
Whether you are using Velruse as a standalone app or as a Pyramid plugin, you will
need to add the following settings to an .ini file.  If you are using the standalone
app, you will need to add them to the .ini file that serves the standalone app.
If you are using Velruse as a Pyramid plugin, you will need to add them to your
Pyramid app's .ini file.

``consumer_key``
    Facebook App Id
``consumer_secret``
    Facebook secret
``scope``
    Optional comma-separated list of extended permissions. The scope is used
    to request access to additional Facebook properties known as
    `Extended Permissions <http://developers.facebook.com/docs/authentication/permissions>`_.
    It should be a comma-separated list.


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


Pyramid API
-----------
.. automodule:: velruse.providers.facebook

   .. autoclass:: FacebookAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_facebook_login

   .. autofunction:: add_facebook_login_from_settings
