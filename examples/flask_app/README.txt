Velruse integration with Flask
==============================

Velruse can run as a standalone WSGI application. It exposes an HTTP
interface for communication between Velruse and your application, which
can be written in any framework or language.

This example illustrates how to integrate Velruse with Flask in the
same WSGI pipeline via the DispatcherMiddleware.

Usage
-----

1. Update example.cfg with keys for your configured services.

2. easy_install Flask velruse

3. FLASK_SETTINGS=example.cfg python myapp.py

4. Navigate the browser to http://localhost:5000/login.

5. Select a configured provider and login to their service. You should be
   redirected back to the result page via the login_complete_view. This
   view is invoked for any successful login, and should be used to store
   credentials, create accounts, and redirect the user to the rest of your
   application.

Note
----

Some services require a resolvable domain name and will not work over
localhost. Be sure to consult the documentation.
