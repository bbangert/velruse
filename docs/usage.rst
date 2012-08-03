.. _usage:

=====
Usage
=====

Velruse is built around the `Pyramid`_ web framework. Each provider
is implemented as a Pyramid addon via Pyramid's ``include`` mechanism. This
means that it is very easy to integrate Velruse with a Pyramid application
directly. When operating outside of Pyramid, Velruse contains a full
WSGI Pyramid app that can be run via any WSGI server. The app exposes an
HTTP API which speaks language-agnostic JSON. This allows the
Velruse app to run independently of the rest of your web stack.

.. warning::

    In order to get working code examples, many providers require that
    the callback that is configured at the end of the authentication workflow
    must be a fully qualified, externally resolvable domain name.

As a Service
============

Velruse will run as a standalone web application which has an API that
makes it easy to authenticate with various providers, as well as obtain user
credentials and profile information after a user has already been
authenticated. This allows virtually anyone to use Velruse, regardless
of their chosen language or framework.  The standalone app is a standard
Pyramid application, so if you are familiar with the
framework, you will feel right at home.  We are going to assume you have no
experience with Pyramid just to be safe though.

The first thing we need to do is provide the Velruse application
with some information about our account details for each provider we are
supporting. Namely the consumer key and consumer secret of our app. These two
values can be obtained by creating an application on each of the provider's
websites, commonly found in the "developers" section. Once you have obtained
a consumer key and secret from each of the providers you wish to support,
we need to tell Velruse about them.  This can be done by creating
an .ini file that will be used to serve the standalone app.
It could look something like the following:

.. code-block:: ini

    [server:main]
    use = egg:waitress
    host = 0.0.0.0
    port = 80

    [app:velruse]
    use = egg:velruse

    setup = myapp.setup_velruse

    endpoint = http://example.com/logged_in

    store = redis
    store.host = localhost
    store.port = 6379
    store.db = 0
    store.key_prefix = velruse_ustore

    provider.facebook.consumer_key = KMfXjzsA2qVUcnnRn3vpnwWZ2pwPRFZdb
    provider.facebook.consumer_secret = ULZ6PkJbsqw2GxZWCIbOEBZdkrb9XwgXNjRy
    provider.facebook.scope = email

    provider.tw.impl = twitter
    provider.tw.consumer_key = ULZ6PkJbsqw2GxZWCIbOEBZdkrb9XwgXNjRy
    provider.tw.consumer_secret = eoCrFwnpBWXjbim5dyG6EP7HzjhQzFsMAcQOEK

Ok so that's a lot of stuff.  Let's go through each section.  The values
in the '[server:main]' section are saying that we want to serve our app via
the `Waitress`_ web server, to bind to any ip address, and to run on port 80.
Next, we have a number of configuration options for our web app.  The
important ones are as follows:

``setup``
    A Python dotted-name describing the location of a callable. This
    callable must accept a Pyramid ``Configurator`` object and use it
    to initialize a session factory as well as a backend storage mechanism.

``endpoint``
    The url that velruse will redirect to after it finishes authenticating
    with a provider.

``store``
    The type of cache that you would like velruse to use. We've selected
    `Redis`_ but this could be any storage backend supported by the
    `anykeystore`_ library.

``store.*``
    The parameters within the store are dependent on the backend selected.
    See the `anykeystore`_ documentation for more details.

``provider.*``
    The parameters for a specific provider. The format is
    ``provider.<identifier>.<setting>`` where ``identifier`` should be
    the shorthand name of one of the providers. The ``identifier`` can
    be anything, but if it is not the name of a provider then
    ``provider.<identifier>.impl`` must point to something. This allows
    you to configure multiple endpoints using the same provider (e.g.
    maybe one endpoint for login only, and another for authorization later).

Finally, we define all of the provider-specific consumer keys and secrets that
we talked about earlier.  Reference each provider's page for documentation
on the supported settings.

Once we are done configuring the application, we can serve it by running:

.. code-block:: bash

    pserve example.ini

This will start serving Velruse at the specified IP and port in your
INI file. We can then communicate with the app, by sending HTTP requests to
that IP/port.  The API is quite simple, and it only consists of the
following two routes:

``/{provider}/login``
    Authenticates with a provider, and redirects back to the url specified by
    the endpoint setting.

``/auth_info?format=json&token={token}``
    Obtains the profile and credential information for a user with the
    specified token.


.. warning::

   The ``/auth_info`` URL should be considered sensitive and only trusted
   services should be allowed access. If an attacker intercepts a an
   authentication token, they could potentially query ``/auth_info`` and
   learn all of the credentials for the user.


Initiating a Login Attempt
--------------------------

In order to get a user to begin the Velruse authentication workflow we need to
have the user submit a POST request to the provider's login URL. This can be
done by submitting a form placed on some page within your site. An example of
such a form is given below.

.. code-block:: html

    <form action="/velruse/login/facebook" method="post">
        <input type="hidden" name="scope" value="publish_stream,create_event" />
        <input type="submit" value="Login with Facebook" />
    </form>


Handling a Login Attempt
------------------------

After completing the provider's authentication process, Velruse will then
redirect to your :term:`endpoint` using a POST request, with the token
assigned to a user stored in the form data. This token can be used to obtain
authentication details about the user.  An example of how to obtain the token
in the endpoint view of an application is given below.

.. code-block:: python

    # sample callback view in flask
    @app.route('/logged_in', methods=['POST'])
    def login_callback():
        # token is stored in the form data
        token = request.form['token']
        return render_template('result.html', result=token)

As you can see, the token is stored in the form data of the request.  We can
then use the ``/velruse/auth_info`` route to obtain a user's authentication
details.  So if we were passed a token with a value of ``'t0k3n'``, then we
can access everything Velruse knows about that user by visiting
``'/velruse/auth_info?format=json&token=t0k3n'``.  We can further add to our
previous example to make such a call.

.. code-block:: python

    # sample callback view in flask
    @app.route('/logged_in', methods=['POST'])
    def login_callback():
        token = request.form['token']

        # the request must contain 'format' and 'token' params
        payload = {'format': 'json', 'token': token}
        # sending a GET request to /auth_info
        response = requests.get(request.host_url + 'velruse/auth_info', params=payload)
        auth_info = response.json
        return render_template('result.html', result=auth_info)

This example is using the `Requests`_ library. ``auth_info`` contains
information about the user's login attempt. In all cases the response will
contain ``provider_name`` and ``provider_type`` metadata. If the response
was successful then the ``profile`` and ``credentials`` will be available.
In the case of a failure, the ``error`` will be available to explain what
may have gone wrong.

As a Pyramid Plugin
===================

The standalone Velruse application is simply a Pyramid application that
is configured using Velruse's Pyramid plugin. To use Velruse in your own
Pyramid applications you simply have to include the providers you
want in your configuration:

.. code-block:: python

    config.include('velruse.providers.facebook')
    config.add_facebook_login_from_settings(prefix='velruse.facebook.')

Much like the standalone app, we need to provide Velruse with some
information about our account details for each provider we are supporting.
Namely the consumer key and consumer secret of our app. This information can
be obtained by creating an application on each of the provider's websites,
commonly found in the "developers" section.  Once you have obtained
credentials for your application (usually a consumer key and secret)
from each of the providers you wish to support, we need to tell Velruse
about them.  We can easily do this by adding them to our app's INI files.
You can use the following example as a guide:

.. code-block:: ini

    velruse.facebook.consumer_key = 411326239420890
    velruse.facebook.consumer_secret = 81ef2318a1999tttc6d9c43d4e93be0c
    velruse.facebook.scope = email

    velruse.twitter.consumer_key = ULZ6PkJbeqwgGxZaCIbdEBZekrbgXwgXajRl
    velruse.twitter.consumer_secret = eoCrewnpdWXjfim5ayGgEPeHzjcQzFsqAchOEa


Initiating a Login Attempt
--------------------------

After Velruse is included in your app, you can easily generate a login url
for any particular provider.  This is accomplished by calling the
:func:`velruse.login_url` like so:

.. code-block:: python

    login_url(request, 'twitter')

In this case, :func:`velruse.login_url` will generate a url like
``http://www.example.com/login/twitter``. A user can then be directed to that
url when they need to authenticate through the Twitter provider.  This is
commonly done in the form of a link or a button on the login page of your app.

In order to get a user to begin the Velruse authentication workflow we need to
have the user submit a POST request to the provider's login URL. This can be
done by submitting a form placed on some page within your site. An example of
such a form is given below.

.. code-block:: html

    <form action="${login_url(request, 'twitter')}" method="post">
        <input type="submit" value="Login with Twitter" />
    </form>


Handling a Login Attempt
------------------------

By integrating your application directly with Velruse, the workflow for
handling a login attempt is more efficient. Instead of having to talk back
to the standalone application, the credentials are available directly within
your app without requiring any external storage. Once the user has visited the
URL generated by :func:`velruse.login_url`, they will be redirected to the
respective provider. The provider will eventually redirect the user back to
the callback URL. Velruse can then perform validation of the results and
generate the profile. You must then specify Pyramid views that will be invoked
when authentication was completed or denied. The first view we need to add is
called when authentication succeeds, and could potentially look something like
this:

.. code-block:: python

    @view_config(
        context='velruse.AuthenticationComplete',
        renderer='myapp:templates/result.mako',
    )
    def login_complete_view(request):
        context = request.context
        result = {
            'provider_type': context.provider_type,
            'provider_name': context.provider_name,
            'profile': context.profile,
            'credentials': context.credentials,
        }
        return {
            'result': json.dumps(result, indent=4),
        }

The important thing to note here, is that we need to register a view that has
a value of :class:`velruse.AuthenticationComplete` assigned to the context
predicate.  This results in the ``login_complete_view`` being invoked when a
third party redirects to your app and was successful.  This view will most
likely be used to store credentials, create accounts, and redirect the user
to the rest of your application.

If you want to create a view that is only called when a *specific* third
party's authentication succeeds, you can change the view configuration to
specify a more specific context:

.. code-block:: python

    @view_config(
        context='velruse.providers.facebook.FacebookAuthenticationComplete',
        renderer='myapp:templates/result.mako',
    )
    def fb_login_complete_view(request):
        pass

It is possible to create many views. Only the most specific view will be
invoked for the matching provider.

The second view we need to add is called when authentication fails:

.. code-block:: python

    @view_config(
        context='velruse.AuthenticationDenied',
        renderer='myapp:templates/result.mako',
    )
    def login_denied_view(request):
        return {
            'result': 'denied',
        }

We assign a value of :class:`velruse.AuthenticationDenied` to the context
predicate of the view.  The ``login_denied_view`` will be invoked
when a third party redirects to your app and reports a failed authentication.
This view will most likely be used to display an appropriate error message
and redirect the user. After Velruse is configured in your Pyramid
application, login urls are generated for each of the providers that you want
to support, and the previous two views are defined, you can effectively use
Velruse to authenticate with third party providers.

.. _anykeystore: http://pypi.python.org/pypi/anykeystore/
.. _Pyramid: http://docs.pylonsproject.org/en/latest/docs/pyramid.html
.. _Redis: http://redis.io/
.. _RPXNow: http://rpxnow.com/
.. _Waitress: http://docs.pylonsproject.org/projects/waitress/en/latest/
.. _Requests: http://docs.python-requests.org/en/latest/index.html
