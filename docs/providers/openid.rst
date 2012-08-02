OpenID - :mod:`velruse.providers.openid`
========================================

The OpenID provider does standard OpenID authentication, using both the
`Simple Registration Extension
<http://openid.net/specs/openid-simple-registration-extension-1_0.html>`_
and many of the `Attribute Exchange <http://www.axschema.org/types/>`_
attributes to acquire as much user information to assist in the
authentication process as possible.

OpenID Developer Links:

* `OpenID Authentication 2.0
  <http://openid.net/specs/openid-authentication-2_0.html>`_
* `Attribute Exchange 1.0
  <http://openid.net/specs/openid-attribute-exchange-1_0.html>`_


Settings
--------
``realm``
    Domain for your website, e.g. `http://yourdomain.com/`
``store``
    A class from which the OpenID store will be instantiated.

.. note::

    The OpenID store is a different store to the Velruse store.
    Please see the :mod:`python-openid` documentation for details.


POST Parameters
---------------
The OpenID provider accepts `openid_identifier` which should designate
the OpenID identifer being claimed to authenticate.

Complete Example:

.. code-block:: html

    <form action="/velruse/openid/login" method="post">
        <input type="text" name="openid_identifier" />
        <input type="submit" value="Login with OpenID" />
    </form>

.. automodule:: velruse.providers.openid

   .. autoclass:: OpenIDAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_openid_login


Pyramid API
-----------
.. automodule:: velruse.providers.oid_extensions

   .. autoclass:: UIRequest
       :members:

   .. autoclass:: OAuthRequest
       :members:

..
    .. autoclass:: AttribAccess

    .. autofunction:: extract_openid_data
    .. autofunction:: setup_openid
    .. autofunction:: includeme
    .. autoclass:: OpenIDAuthenticationComplete
    .. autoclass:: OpenIDConsumer
        :members: __init__, _lookup_identifier, _update_authrequest, _get_access_token, login, _update_profile_data, process
