Twitter - :mod:`velruse.providers.twitter`
==========================================

The Twitter provider combines authentication with OAuth authorization.
It requires a Twitter Application to have been created to use. Twitter
only provides the twitter screen name and id, along with an OAuth
access token.

Twitter Developer Links:

* `Register a New Twitter Application <http://dev.twitter.com/apps/new>`_
* `Twitter OAuth API <http://dev.twitter.com/doc>`_

Settings
--------

velruse.twitter.consumer_key
    Twitter application consumer key
velruse.twitter.consumer_secret
    Twitter application secret
velruse.twitter.authorization
    github application scope

POST Parameters
---------------

Complete Example:

.. code-block:: html

    <form action="/velruse/twitter/login" method="post">
    <input type="submit" value="Login with Twitter" />
    </form>

.. automodule:: velruse.providers.twitter

   .. autoclass:: TwitterAuthenticationComplete
      :show-inheritance:

   .. autofunction:: includeme

   .. autofunction:: add_twitter_login

   .. autofunction:: add_twitter_login_from_settings
