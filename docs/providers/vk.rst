============================================
VK - :mod:`velruse.providers.vk`
============================================

The VK (ex Vkontakte) provider authenticates using the OAuth 2.0
API with the VK API to obtain additional profile information
for use with user registration.

To use the VK authentication, you must register a VK application
for use with Velruse. You can do that by using the following links to learn about
and create said application.  Once you have done so, you will be supplied with a
consumer key and a consumer secret specific to VK.

VK Developer Links:

* `Developer Page (View apps, create app)
  <http://vk.com/developers.php>`__



Settings
--------

``consumer_key``
    VK Application ID
``consumer_secret``
    VK Secure key
``scope``
    Comma-separated list of permissions. The scope is used
    to request access to VK properties known as
    `Application Access Rights <http://vk.com/developers.php?oid=-17680044&p=Application_Access_Rights>`__.
    It should be either a comma-separated or space-separated list.


POST parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/vk/auth" method="post">
        <input type="submit" value="Login with VK" />
    </form>


Pyramid API
-----------

.. automodule:: velruse.providers.vk

   .. autoclass:: VKAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_vk_login

   .. autofunction:: add_vk_login_from_settings
