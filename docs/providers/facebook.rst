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
  <http://www.facebook.com/developers/#!/developers/apps.php>`_
* `Create new Facebook Application
  <http://www.facebook.com/developers/createapp.php>`_

Settings
--------

Whether you are using velruse as a standalone app or as a Pyramid plugin, you will
need to add the following settings to an .ini file.  If you are using the standalone
app, you will need to add them to the .ini file that serves the standalone app.
If you are using velruse as a Pyramid plugin, you will need to add them to your
Pyramid app's .ini file.

``velruse.facebook.consumer_key``
    Facebook App Id
``velruse.facebook.consumer_secret``
    Facebook secret
``velruse.facebook.scope``
    Optional comma-separated list of extended permissions.

As a Service
------------

If you are using the velruse standalone app, you will need to create a form in your
application that will send a POST request to velruse. Like so:

.. code-block:: html

    <form action="/velruse/facebook/auth" method="post">
        <input type="hidden" name="scope" value="publish_stream,create_event" />
        <input type="submit" value="Login with Facebook" />
    </form>

It is important to notice this line, as it defines the Facebook scope:

.. code-block:: html

    <input type="hidden" name="scope" value="publish_stream,create_event" />

The scope is used in the authenticating request to access additional Facebook properties known
as `Extended Permissions <http://developers.facebook.com/docs/authentication/permissions>`_.
It should be a comma-separated list.

As a Pyramid Plugin
-------------------

If you are using velruse as a Pyramid plugin, you will need to generate the login url for
the Facebook provider, and add two views to your application.  To generate the login url, you
will use the :func:`velruse.login_url` function like so:

.. code-block:: python

    login_url(request, 'facebook')

This is normally done in a view of your application, or potentially in one of your templates.
This is the url a user will need to visit to begin the authentication process.  After that,
you need to provide a way for your app to handle a successful and failed login.  To do this,
define the following views in your app:

.. code-block:: python

    @view_config(
        context='velruse.FacebookAuthenticationComplete',
        renderer='myapp:templates/result.mako',
    )
    def login_complete_view(request):
        context = request.context
        result = {
            'profile': context.profile,
            'credentials': context.credentials,
        }
        return {
            'result': json.dumps(result, indent=4),
        }


    @view_config(
        context='velruse.AuthenticationDenied',
        renderer='myapp:templates/result.mako',
    )
    def login_denied_view(request):
        return {
            'result': 'denied',
        }

These views will be invoked when authentication through a third party provider completes or
fails.  For Facebook specifically, the profile will look something like this:

.. code-block:: json

    {
        'stuff': 'stuff'
    }

And the credentials will look something like this:

.. code-block:: json

    {
        'stuff': 'stuff'
    }

.. automodule:: velruse.providers.facebook

   .. autoclass:: FacebookAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_facebook_login

   .. autofunction:: add_facebook_login_from_settings
