Reddit - :mod:`velruse.providers.reddit`
========================================

The Reddit provider combines authentication with OAuth 2.0 authorization.
It requires a Reddit App to have been created to use.

Reddit Links:

* `Register a New Reddit Application
  <https://ssl.reddit.com/prefs/apps/>`__
* `Reddit OAuth 2.0 API <https://github.com/reddit/reddit/wiki/OAuth2>`__


Settings
--------

``consumer_key``
    reddit application consumer key
``consumer_secret``
    reddit application secret
``scope``
    reddit application scope - defaults to identity


POST Parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/reddit/login" method="post">
        <input type="submit" value="Login with Reddit" />
    </form>


Pyramid API
-----------

.. automodule:: velruse.providers.reddit

   .. autoclass:: RedditAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_reddit_login

   .. autofunction:: add_reddit_login_from_settings
