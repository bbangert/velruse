Github - :mod:`velruse.providers.github`
========================================

The Github provider combines authentication with OAuth authorization.
It requires a Github Application to have been created to use.

github Links:

* `Register a New Github Application
  <https://github.com/account/applications/new>`_
* `Github OAuth API <http://develop.github.com/p/oauth.html>`_

Settings
--------

velruse.github.consumer_key
    github application consumer key
velruse.github.consumer_secret
    github application secret
velruse.github.scope
    github application scope

POST Parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/github/login" method="post">
    <input type="submit" value="Login with Twitter" />
    </form>

.. automodule:: velruse.providers.github

   .. autoclass:: GithubAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_github_login

   .. autofunction:: add_github_login_from_settings
