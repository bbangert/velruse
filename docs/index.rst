Velruse Documentation
=====================

Velruse is a set of authentication routines that provide a unified way to have
a website user authenticate to a variety of different identity providers
*and/or* a variety of different authentication schemes.

It is similar in some ways to `Janrain Engage`_ with the exception of being
open-source, locally installable, and easily pluggable for custom identity
providers and authentication schemes.

You can run Velruse as a stand-alone service for use with your websites
regardless of the language they're written in. While Velruse itself is written
in Python, since it can interact with your website purely via HTTP POST's.

Velruse can:

* **Normalize identity information** from varying provider sources (OpenID,
  Google, Facebook, etc.) to `Portable Contacts`_.

* **Simplify complex authentication protocols** by providing a simple
  consistent API

* **Provide extension points for other authentication systems**, write your
  own auth provider to handle `CAS`_, `LDAP`_, and use it with ease

* **Integrate with most web applications** regardless of the language used
  to write the website

Velruse aims to simplify authenticating a user. It provides
:term:`auth provider`'s that handle authenticating to a variety of
identity providers with multiple authentication schemes (LDAP, SAML,
etc.). Eventually, Velruse will include widgets similar to `RPXNow`_
that allow one to customize a login/registration widget so that a website
user can select a preferred identity provider to use to sign-in. In the
mean-time, effort is focused on increasing the available
:term:`auth provider`'s for the commonly used authentication schemes
and identity providers (Facebook, Google, OpenID, etc). Unlike other
authentication libraries for use with web applications,
a website using Velruse for authentication **does not have to be
written in any particular language**.


Contents:

.. toctree::
   :maxdepth: 2

   architecture
   usage
   providers
   api
   changes

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
* :ref:`glossary`

.. toctree::
   :hidden:

   glossary

.. _Janrain Engage: http://www.janrain.com/products/engage
.. _OpenID: http://openid.com/
.. _Portable Contacts: http://portablecontacts.net/draft-spec.html
.. _CAS: http://www.jasig.org/cas/cas2-architecture
.. _LDAP: http://www.openldap.org/
.. _RPXNow: http://rpxnow.com/
