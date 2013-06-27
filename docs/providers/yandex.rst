Yandex - :mod:`velruse.providers.yandex`
========================================

The Yandex provider combines authentication with OAuth 2.0 authorization.
It requires a Yandex Application to have been created to use.

Yandex Links (English):

* `Yandex Services OAuth API <http://api.yandex.com/oauth/doc/dg/concepts/authorization-scheme.xml>`__


Yandex Links (Russian):

* `Register a New Yandex Application
  <https://oauth.yandex.ru/client/new>`__
* `Yandex Services OAuth API <http://api.yandex.ru/oauth/doc/dg/concepts/authorization-scheme.xml>`__
* `Yandex Login + OAuth API <http://api.yandex.ru/login/doc/dg/concepts/about.xml>`__


Settings
--------

``consumer_key``
    Yandex Application ID
``consumer_secret``
    Yandex Application password


POST Parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/yandex/login" method="post">
        <input type="submit" value="Login with Yandex" />
    </form>


Pyramid API
-----------

.. automodule:: velruse.providers.yandex

   .. autoclass:: YandexAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_yandex_login

   .. autofunction:: add_yandex_login_from_settings
