.. _glossary:

Glossary
========


.. glossary::
    :sorted:

    auth provider
        A class implementing the Marco responder pattern that listens to a
        specific set of URL's for interaction and redirects back to the
        designated endpoint when the authentication is finished.
    
    endpoint
        The end_point is a standard parameter used with velruse authentication
        to indicate where velruse should POST the token to when the user
        has finished.
    
    identity provider
        A service/website that authenticates a user and returns user 
        information. Some well known identity providers: Google, AOL,
        Yahoo, Facebook, twitter.
    
    UserStore
        Persistent data storage to hold onto user records after a user
        has authenticated. The user data is stored temporarily until it
        has been retrieved for use.
    
    responder
        Term used for an object that can be called with a WebOb Request, and
        will return a WebOb Response object. All of the Auth Providers follow
        this call style.
