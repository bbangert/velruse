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
  <http://www.facebook.com/#!/developers/>`__
* `Facebook Application Management
  <https://developers.facebook.com/apps>`__


Settings
--------

``consumer_key``
    Facebook App Id
``consumer_secret``
    Facebook secret
``scope``
    Optional comma-separated list of extended permissions. The scope is used
    to request access to additional Facebook properties known as
    `Extended Permissions <http://developers.facebook.com/docs/authentication/permissions>`__.
    It should be a comma-separated list.


POST parameters
---------------

The Facebook provider accepts a scope argument, which is used in the
authenticating request to access additional Facebook properties known
as `Extended Permissions
<http://developers.facebook.com/docs/authentication/permissions>`__.
These should be a comma separated string, for example:

.. code-block:: html

    <input type="hidden" name="scope" value="publish_stream,create_event" />

Complete Example:

.. code-block:: html

    <form action="/velruse/facebook/auth" method="post">
        <input type="hidden" name="scope" value="publish_stream,create_event" />
        <input type="submit" value="Login with Facebook" />
    </form>

Facebook also accepts a `display` argument, which will indicate the UI for
Facebook to use. For more information, see
`OAuth Dialog <https://developers.facebook.com/docs/reference/dialogs/oauth/`__.
For instance, if you would like to use the "popup" interface:

.. code-block:: html

    <input type="hidden" name="display" value="popup" />

Pyramid API
-----------

.. automodule:: velruse.providers.facebook

   .. autoclass:: FacebookAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_facebook_login

   .. autofunction:: add_facebook_login_from_settings
