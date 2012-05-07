Velruse integration with Pyramid
================================

Velruse can integrate directly into your Pyramid application, providing
only the bare functionality required to handle communication with
third-party authentication providers.

Usage
-----

1. Update example.ini with keys for your configured services.

2. python setup.py develop

3. pserve example.ini

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
