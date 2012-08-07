Velruse TODO
============

Nice-to-Have
------------

- Create a Velruse WSGI middleware component. This would contain most of the
  current internals of the standalone app, but allow the credentials to be
  passed directly into an application (via the environ) without any
  sub-requests.

- OpenID doesn't seem to work with Google Hosted Apps. This looked like a bug
  within the python-openid package though.

- Improved testing.

  + Support request/response fixtures for each endpoint that can be
    run through to validate behavior.

  + Make selenium tests optional, and preferably have the server run
    in a thread within the test setup to avoid having to spin up a separate
    shell to run the server.

  + Create unit tests for the portable contacts conversion functions
    such as ``velruse.providers.facebook.extract_fb_data()``.

  + Automate testing, possibly via Travis-CI or Jenkins.

- Support storing some state via the login URL.

  + POST /login/facebook with state=foo, we would expect that state=foo
    is then available somehow in the AuthenticationComplete context.

- Add CSRF checking to more providers.

- Add introspection via Pyramid's introspection API ('velruse providers'
  category).

- Add support for /auth endpoints as well as /login endpoints. Some providers
  like Twitter and Last.fm have different workflows for simply logging in
  versus granting access to the user's data on a provider's system.

- Possibly factor out a Provider base class that can handle a lot of common
  operations between providers (sub-requests, state tracking, introspection).
