For the impatient
-----------------

1. Simply run script run-server.sh

2. Navigate to page /login like the example below:

    $ firefox http://localhost:6543/login


Configuration
-------------

1. Please adjust variable *realm* in development.ini.

2. Several providers need to be configured according to your affiliation
   keys with providers like Google OAuth2, Twitter, Facebook, etc.

Several providers work out of the box, like Google Hybrid, Yahoo and most
of OpenID providers.


About this example
------------------

This example evolved to a proper plugin, which is available from PyPI at 
https://pypi.python.org/pypi/kotti_velruse


Dependencies
------------

This example depends on a modified versions of velruse and openid-selector:

* velruse: https://pypi.python.org/pypi/rgomes_velruse

* openid-selector: https://pypi.python.org/pypi/openid-selector

Sources for these changed sources are available at:

* velruse: https://github.com/frgomes/velruse/tree/feature.kotti_auth

* openid-selector: https://github.com/frgomes/velruse
