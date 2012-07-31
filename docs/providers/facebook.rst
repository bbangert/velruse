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

Initiating a Login Attempt
--------------------------

The client will send a POST request to the Velruse login URL. This can
be done by adding a form to your website that the user clicks.

.. code-block:: html

    <form action="/velruse/facebook/login" method="post">
        <input type="hidden" name="scope" value="publish_stream,create_event" />
        <input type="submit" value="Login with Facebook" />
    </form>

If you are using Velruse as a Pyramid plugin, you can generate the login url
for the Facebook provider programmatically via the :func:`velruse.login_url`
function:

.. code-block:: python

    login_url(request, 'facebook')

Handling a Login Attempt From The Standalone App
------------------------------------------------

When running Velruse as a standalone application, it will execute a POST
back to the configured ``endpoint`` URL on your site. The POST
parameter will contain a ``token`` which can be used to request the
user credentials or errors from Velruse.

..
   Possibly provide an example in some other language, or flask
   or django of how to handle the login attempts.
   It might be better to just have a link to some common location
   where we show how to handle velruse login attempts.

Handling a Login Attempt In Your Pyramid App
--------------------------------------------

Integrating the provider directly into your Pyramid application gives you
full control over handling the client's login attempt. There are two
possible paths a login attempt will take. Either it is successful or
denied. These can be handled by adding two separate views to your
Pyramid application.

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

Pyramid API
-----------

.. automodule:: velruse.providers.facebook

   .. autoclass:: FacebookAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_facebook_login

   .. autofunction:: add_facebook_login_from_settings
