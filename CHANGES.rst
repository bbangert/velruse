1.0.2 (2012-09-13)
==================

- [facebook,github,weibo] Fix bug in CSRF checking where Velruse would pass
  the CSRF check if a session had not been started.

- [google] Added support for Google's OAuth2.0 protocol.

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
