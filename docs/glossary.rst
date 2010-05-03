.. _glossary:

Glossary
========


.. glossary::

    auth provider
        A class implementing the Marco responder pattern that listens to a
        specific set of URL's for interaction and redirects back to the
        designated endpoint when the authentication is finished.
    
    identity provider
        A service/website that authenticates a user and returns user 
        information. Some well known identity providers: Google, AOL,
        Yahoo, Facebook, twitter.
    
    UserStore
        Persistent data storage to hold onto user records after a user
        has authenticated. The user data is stored temporarily until it
        has been retrieved for use.
