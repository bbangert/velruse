1.1.1 (2013-08-29)
==================

This release primarily includes various unicode improvements as we approach
py3k support.

Bug Fixes
---------

- [twitter] Fix bug when twitter sends a `null` value for `utc_offset`.

1.1 (2013-06-27)
================

New Features
------------

- Minimal Py3k compatibility.

  - Switch dependency to 'python3-openid' for Py3k.

- [bitbucket] Add an extra query to populate the `emails` and `verifiedEmail`
  keys in the profile.

- [douban] The douban provider now uses their OAuth2 API instead of OAuth1.0.

- [facebook] Support optional `display` parameter for facebook logins.

- [linkedin] Add support for email address.

- [linkedin] Standardize the default login and callback urls to be similar
  to all of the other providers by using the `/login/{provider}` prefix.

- [twitter] Support more portable contacts keys including `preferredUsername`.

- [weibo] Add support for the `scope` parameter.

Backward Incompatibilities
--------------------------

- Standardize birthdays to YYYY-MM-DD format as specified by Portable
  Contacts instead of using Python date objects. This was done to follow
  the spec more closely and keep the standalone app's serialized profile
  the same as the plugin's profile.

- [douban] The douban provider now uses their OAuth2 API instead of OAuth1.0.

- [facebook] Profile keys `gender`, `emails` and `verifiedEmail` will not be
  present in the profile if they are not available.

- [openid, google_hybrid, yahoo] The default OpenID store is now stateless,
  changed from the previous default
  :class:`openid.store.memstore.MemoryStore`. The provider can be updated
  by specifying the `store` opention when creating creating each provider.

Dependencies
------------

- Switch to using oauthlib instead of python-oauth2 for
  OAuth1-based providers.

1.0.3 (2012-10-11)
==================

- [google_hybrid] Modified the type of the
  :class:`~velruse.providers.google_hybrid.GoogleAuthenticationComplete`
  to be ``google_hybrid`` instead of ``google``.

1.0.2 (2012-10-11)
==================

- [facebook,github,weibo] Fix bug in CSRF checking where Velruse would pass
  the CSRF check if a session had not been started.

- [google_hybrid] Renamed the Google OpenID+OAuth1.0 hybrid module to
  ``google_hybrid``. There are bw-compat shims left in
  ``velruse.providers.google``. This will be deprecated in a future release.

- [google_oauth2] Added support for Google's OAuth2.0 protocol.

- [mailru] Added a new provider for mail.ru.

- [vk] Added a new provider for vk.com (Vkontakte).

- [yandex] Added a new provider for yandex.ru.

1.0.1 (2012-08-30)
==================

- [facebook] Modified handling of timezone offsets in user profiles to be more
  robust to different "minute" values.

1.0 (2012-08-14)
================

Version 0.3 is classified as an older release than the previous 0.20
in the semantic versioning scheme. Thus 0.3 was a brownbag and 1.0 will
correct that issue.

This release is also an opportunity to promote Velruse's new API and
provide confidence that it will try to maintain backward compatibility
going forward.

0.3b3 (2012-08-06)
==================

- 0.3b2 was a brownbag

0.3b2 (2012-08-06)
==================

- [github] Add CSRF checks to the provider as they started requiring the
  OAuth state variable to be used.

0.3b1 (2012-08-03)
==================

- Complete rewrite of the Velruse internal API. It is now written as a
  fully supported Pyramid plugin.

- Overhaul of documentation.

  + Individually documented the standalone service application and
    the Pyramid plugin API.

- Removed support for Twitter's authorization API. This will be brought
  back in a future release.

- Added support for several new OAuth2.0 providers.

  + douban
  + github
  + linkedin
  + qq
  + renren (http://renren.com)
  + taobao
  + weibo

0.20a1 (2011-05-25)
===================

- Minor bug fixes.

0.1 (2010-04-30)
================

- Initial release.
