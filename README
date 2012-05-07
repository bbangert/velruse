Velruse is a set of authentication routines that provide a unified way
to have a website user authenticate to a variety of different identity
providers and/or a variety of different authentication schemes.

It is similar in some ways to RPXnow with the exception of being
open-source, locally installable, and easily pluggable for custom
identity providers and authentication schemes.

You can run Velruse as a stand-alone service for use with your websites
regardless of the language they're written in. While Velruse itself is
written in Python, since it can interact with your website purely via
HTTP POST's.

Velruse can:

* Normalize identity information from varying provider sources
  (OpenID, Google, Facebook, etc.) to Portable Contacts.
* Simplify complex authentication protocols by providing a simple
  consistent API.
* Provide extension points for other authentication systems, write your
  own auth provider to handle CAS, LDAP, and use it with ease.
* Integrate with most web applications regardless of the language used
  to write the website.

Warning: It's early yet for Velruse, so only those interested in
developing Velruse should be taking a look into this now.

----

Overview

Velruse aims to simplify authenticating a user. It provides auth
providers that handle authenticating to a variety of identity providers
with multiple authentication schemes (LDAP, SAML, etc.).

Eventually, Velruse will include widgets similar to RPXNow that allow
one to customize a login/registration widget so that a website user can
select a preferred identity provider to use to sign-in.

In the mean-time, effort is focused on increasing the available auth
providers for the commonly used authentication schemes and identity
providers (Facebook, Google, OpenID, etc).

Unlike other authentication libraries for use with web applications, a
website using Velruse for authentication does not have to be written in
any particular language.

API

Velruse implements an API similar to RPXNow to standardize the way a
web application handles user authentication.

Velruse Authentication flow

1. Website sends a POST to the auth provider‘s URL with an endpoint that
   the user should be redirected back to when authentication is complete
   and includes any additional parameters that the auth provider requires.
2. When the auth provider finishes the authentication, the user is
   redirected back to the endpoint specified with a POST, which includes
   a unique token.
3. Website then makes a query to the UserStore using the token that was
   provided. The user’s identity information will be returned, or an
   error if the authentication was unsuccessful.

If the website is unable to directly access the UserStore then Step 3 can
be replaced by issuing a HTTP POST in the background to the auth provider
requesting the user’s information with the token.
