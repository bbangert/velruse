Windows Live - :mod:`velruse.providers.live`
============================================

The Windows Live Provider supports the Windows Live OAuth 2.0 API.

.. note::

    The Return URL for velruse must be registered with Live Services
    as **Return URL**.

    Example Return URL::

        http://YOURDOMAIN.COM/velruse/live/process


Windows Live Developer Links:

* `Windows Live <http://msdn.microsoft.com/en-us/windowslive/default.aspx>`__
* `Windows Live OAuth 2.0 SDK
  <http://msdn.microsoft.com/en-us/library/hh243647.aspx>`__


Settings
--------

``client_id``
    Component Application ID

``client_secret``
    Component Secret Key

``scope``
    Delegated auth Offers, e.g. `Contacts.View`
    The `Offers` parameter is optional to invoke Delegated Authentication.


POST Parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/live/auth" method="post">
        <input type="submit" value="Login with Windows Live" />
    </form>


Pyramid API
-----------

.. automodule:: velruse.providers.live

   .. autoclass:: LiveAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_live_login

   .. autofunction:: add_live_login_from_settings
