Mail.ru - :mod:`velruse.providers.mailru`
=========================================

The Mail.ru provider combines authentication with OAuth 2.0 authorization.
It requires either a Mail.ru Site or a Mail.ru Application
(the platform makes distinctions between Sites and Applications) 
to have been created to use.

Mail.ru Links (Russian):

* `Register a new Mail.ru Site
  <http://api.mail.ru/sites/my/add>`__
* `Register a new Mail.ru Application
  <http://api.mail.ru/apps/my/add/>`__
* `Mail.ru OAuth Developer Guide <http://api.mail.ru/docs/guides/oauth/>`__
* `Mail.ru API Guide <http://api.mail.ru/docs/>`__


Settings
--------

``consumer_key``
    Mail.ru Site/Application ID
``consumer_secret``
    Mail.ru Secret Key


POST Parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/mailru/login" method="post">
        <input type="submit" value="Login with Mail.ru" />
    </form>


Pyramid API
-----------

.. automodule:: velruse.providers.mailru

   .. autoclass:: MailRuAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_mailru_login

   .. autofunction:: add_mailru_login_from_settings

