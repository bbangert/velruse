Github - :mod:`velruse.providers.github`
========================================

The Github provider combines authentication with OAuth authorization.
It requires a Github Application to have been created to use.

Github Links:

* `Register a New Github Application
  <https://github.com/settings/applications/new>`__
* `Github OAuth API <http://developer.github.com/v3/oauth/>`__


Settings
--------

``consumer_key``
    github application consumer key
``consumer_secret``
    github application secret
``scope``
    github application scope


POST Parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/github/login" method="post">
        <input type="submit" value="Login with Github" />
    </form>


Pyramid API
-----------

.. automodule:: velruse.providers.github

   .. autoclass:: GithubAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_github_login

   .. autofunction:: add_github_login_from_settings
