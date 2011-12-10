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


Contents:

.. toctree::
   :maxdepth: 2
   
   overview
   architecture
   providers
   glossary

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
* :ref:`glossary`

Module Listing
--------------

.. toctree::
    :maxdepth: 2
    
    modules/index

.. _Janrain Engage: http://www.janrain.com/products/engage
.. _OpenID: http://openid.com/
.. _Portable Contacts: http://portablecontacts.net/draft-spec.html
.. _CAS: http://www.jasig.org/cas/cas2-architecture
.. _LDAP: http://www.openldap.org/
