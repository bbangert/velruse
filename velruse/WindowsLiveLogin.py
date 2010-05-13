#######################################################################
# FILE:        WindowsLiveLogin.py
#                                                                      
# DESCRIPTION: Sample implementation of Web Authentication and 
#              Delegated Authentication protocol in Python. Also 
#              includes trusted sign-in and application verification 
#              sample implementations.
#
# VERSION:     1.1
#
# Copyright (c) 2008 Microsoft Corporation.  All Rights Reserved.
#######################################################################

from Crypto.Cipher import AES
from Crypto.Hash import SHA256 
from Crypto.Hash import HMAC 
import xml.dom.minidom
import warnings
import logging
import urllib
import base64
import time
import cgi
import sys
import re

class WLLError(Exception):

    """All fatal errors in this class will throw this exception."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class ConsentToken :
    
    """Holds the Consent Token object corresponding to consent granted. """
    
    def __init__(self, wll, delegationToken, refreshToken, sessionKey, expiry,
                   offers, locationID, context, decodedToken, token ):
        """Initialize the ConsentToken module with the WindowsLiveLogin, 
        delegation token, refresh token, session key, expiry, offers, 
        location ID, context, decoded token, and raw token.
        """
        self.__wll = wll
        self.setDelegationToken(delegationToken)
        self.setRefreshToken(refreshToken)
        self.setSessionKey(sessionKey)
        self.setExpiry(expiry)
        self.setOffers(offers)
        self.setLocationID(locationID)
        self.setContext(context)
        self.setDecodedToken(decodedToken)
        self.setToken(token)
        
    def setDelegationToken(self, delegationToken):
        """Sets the Delegation token."""
        if not delegationToken:
            raise WLLError("Error: ConsentToken: Null delegation token.")
        self.__delegationToken = delegationToken
        
    def getDelegationToken(self):
        """Gets the Delegation token."""
        return self.__delegationToken
        
    def setRefreshToken(self, refreshToken):
        """Sets the refresh token."""
        self.__refreshToken = refreshToken
        
    def getRefreshToken(self):
        """Gets the refresh token."""
        return self.__refreshToken
        
    def setSessionKey(self, sessionKey):
        """Sets the session key."""
        if not sessionKey:
            raise WLLError("Error: ConsentToken: Null session key.")
        self.__sessionKey = self.__wll.u64(sessionKey)
        
    def getSessionKey(self):
        """Gets the session key."""
        return self.__sessionKey
        
    def setExpiry(self, expiry):
        """Sets the expiry time of delegation token."""
        if not expiry:
            raise WLLError("Error: ConsentToken: Null expiry time.")

        try:
            expirytime = int(expiry)
            if expirytime <= 0:
                raise WLLError("Error: setExpiry: Invalid expiry time (<=0): %s" % expiry)
            self.__expiry = expirytime
        except BaseException, e: 
            raise WLLError("Error: setExpiry: Invalid expiry time %s : %s" % (expiry, e))
        
    def getExpiry(self):
        """Gets the expiry time of delegation token."""
        return self.__expiry
        
    def setOffers(self, offers):
        """Sets the offers/actions for which user granted consent."""
        if not offers:
            raise WLLError("Error: ConsentToken: Null offers.")
        offers = urllib.unquote(offers)
        
        offer_s = ""
        offers_a = {}
        counter = 0
        pairs = offers.split(';')
        for pair in pairs:
            if pair.find(":") >= 0:
                k, v = pair.split(':')
                if offer_s:
                    offer_s = offer_s + ','
                offer_s = offer_s + k
                offers_a[counter] = k
                counter = counter + 1

        self.__offers = offers_a
        self.__offers_string = offer_s
            
    def getOffers(self):
        """Gets the list of offers/actions for which the user granted consent."""
        return self.__offers
        
    def getOffersString(self):
        """Gets the string representation of all the offers/actions for which 
        the user granted consent."""
        return self.__offers_string
        
    def setLocationID(self, locationID):
        """Sets the location ID."""
        if not locationID:
            raise WLLError("Error: ConsentToken: Null location ID.")
        self.__locationID = locationID
        
    def getLocationID(self):
        """Gets the location ID."""
        return self.__locationID

    def getContext(self):
        """Returns the application context that was originally passed
        to the sign-in request, if any."""
        return self.__context

    def setContext(self, context):
        """Sets the application context."""
        self.__context = context

    def setDecodedToken(self, decodedToken):
        """Sets the decoded token."""
        self.__decodedToken = decodedToken
        
    def decodedToken(self):
        """Gets the decoded token."""
        return self.__decodedToken
        
    def setToken(self, token):
        """Sets the raw token."""
        self.__token = token
        
    def getToken(self):
        """Gets the raw token."""
        return self.__token
        
    def isValid(self):
        """Indicates whether the delegation token is set and has not expired."""
        if not self.__delegationToken:
            return False
        now = time.time()
        expiry = self.getExpiry()
        return (now - 300) < expiry
        
    def refresh (self):
        """Refreshes the current token and replace it. If operation succeeds 
        true (1) is returned to signify success."""
        ct = self.__wll.refreshConsentToken(self)
        if not ct:
            return False
        self.copy(ct)
        return True
        
    def copy(self, ct):
        """Makes a copy of the ConsentToken object."""
        self.__wll = ct.__wll
        self.__delegationToken = ct.__delegationToken
        self.__refreshToken = ct.__refreshToken
        self.__sessionKey = ct.__sessionKey
        self.__expiry = ct.__expiry
        self.__offers = ct.__offers
        self.__offers_string = ct.__offers_string
        self.__locationID = ct.__locationID
        self.__decodedToken = ct.__decodedToken
        self.__token = ct.__token
           
        
class User:

    """Holds the user information after a successful sign-in."""

    def __init__(self, timestamp, userid, flags, context, token):
        """Initialize the User with time stamp, userid, flags, 
        context and token."""
        self.setTimestamp(timestamp)
        self.setId(userid)
        self.setFlags(flags)
        self.setContext(context)
        self.setToken(token)

    def getTimestamp(self):
        """Returns the Unix timestamp as obtained from the SSO token."""
        return self.__timestamp

    def setTimestamp(self, timestamp):
        """Sets the Unix timestamp."""
        if not timestamp:
            raise WLLError("Error: User: Null timestamp in token.")

        try:
            timestamp = int(timestamp)
            if timestamp <= 0:
                raise WLLError("Error: User: Invalid timestamp: %s" % timestamp)
            self.__timestamp = timestamp
        except:
            raise WLLError("Error: User: Invalid timestamp: %s" % timestamp)

    def getId(self):
        """Returns the the pairwise unique ID for the user."""
        return self.__id

    def setId(self, userid):
        """Sets the the pairwise unique ID for the user."""
        if not userid:
            raise WLLError("Error: User: Null id in token.")            

        m = re.match(r'^\w+$', userid)
        if not m:
            raise WLLError("Error: User: Invalid id: %s" % userid)            

        self.__id = userid

    def usePersistentCookie(self):
        """Indicates whether the application is expected to store the
        user token in a session or persistent cookie."""
        return self.__usePersistentCookie

    def setFlags(self, flags):
        """Sets the usePersistentCookie flag for the user."""
        self.__usePersistentCookie = False
        if flags:
            try:
                flags = int(flags)
                self.__usePersistentCookie = ((flags %2) == 1)
            except:
                raise WLLError("Error: User: Invalid flags: %s" % flags)            

    def getContext(self):
        """Returns the application context that was originally passed
        to the sign-in request, if any."""
        return self.__context

    def setContext(self, context):
        """Sets the the Application context."""
        self.__context = context

    def getToken(self):
        """Returns the encrypted Web Authentication token containing the UID.

        This can be cached in a cookie and the UID can be retrieved by
        calling the ProcessToken method.
        """
        return self.__token

    def setToken(self, token):
        """Sets the raw User token."""
        self.__token = token

class WindowsLiveLogin:

    ###################################################################
    # Implementation of the basic methods needed to perform 
    # Web Authentication and Delegated Authentication.
    ###################################################################

    def setDebug(self, logenabled):
        """Stub implementation for logging errors.

        If you want to enable debugging output, set the DEBUG flag to True
        or False to disable.
        """
        if logenabled:
            self.__log = True
        else:
            self.__log = False
        
    def debug(self, error):
        """Stub implementation for logging errors.
        
        By default, this function does nothing if the debug file has
        not been set with setDebug. Otherwise, the standard Python
        logger is used to output the SDK error message.
        """
        if self.__log:
            warnings.warn(error)
        return
    
    def fatal(self, error):
        """Stub implementation for handling a fatal error."""
        self.debug(error)
        raise WLLError(error)

    def __init__(self, appid=None, secret=None, securityalgorithm=None, force_delauth_nonprovisioned=False, policyurl=None, returnurl=None):
        """# Initialize the WindowsLiveLogin module with the application ID,
        secret key, and security algorithm.  

        We recommend that you employ strong measures to protect the
        secret key. The secret key should never be exposed to the Web
        or other users.

        Be aware that if you do not supply these settings at
        initialization time, you may need to set the corresponding
        properties manually.

        For Delegated Authentication, you may optionally specify the
        privacy policy URL and return URL. If you do not specify these
        values here, the default values that you specified when you
        registered your application will be used.  

        The 'force_delauth_nonprovisioned' flag also indicates whether
        your application is registered for Delegated Authentication 
        (that is, whether it uses an application ID and secret key). We 
        recommend that your Delegated Authentication application always 
        be registered for enhanced security and functionality.
        """
        self.__log = None
        self.__appid = None
        self.__cryptkey = None
        self.__signkey = None
        self.__securityalgorithm = None
        self.__baseurl = None
        self.__secureurl = None
        self.__force_delauth_nonprovisioned = force_delauth_nonprovisioned
        self.__policyurl = None
        self.__returnurl = None
        self.__oldsecretexpiry = None
        self.__oldsignkey = None
        self.__oldcryptkey = None
        self.__consenturl = None

        if appid:
            self.setAppId(appid)
        if secret:
            self.setSecret(secret)
        if securityalgorithm:
            self.setSecurityAlgorithm(securityalgorithm)
        if policyurl:
            self.setPolicyUrl(policyurl)
        if returnurl:
            self.setReturnUrl(returnurl)
            

    @staticmethod
    def initFromXml(settingsFile):
        """Initialize the WindowsLiveLogin module from a settings file. 

        'settingsFile' specifies the location of the XML settings file
        that contains the application ID, secret key, and security
        algorithm. The file is of the following format:

        <windowslivelogin>
          <appid>APPID</appid>
          <secret>SECRET</secret>
          <securityalgorithm>wsignin1.0</securityalgorithm>
        </windowslivelogin>

        In a Delegated Authentication scenario, you may also specify
        'returnurl' and 'policyurl' in the settings file, as shown in the
        Delegated Authentication samples.

        We recommend that you store the WindowsLiveLogin settings file
        in an area on your server that cannot be accessed through the 
        Internet. This file contains important confidential information.
        """
        o = WindowsLiveLogin()
        settings = o.parseSettings(settingsFile)
        
        o.force_delauth_nonprovisioned = False
        if 'force_delauth_nonprovisioned' in settings:
            o.__force_delauth_nonprovisioned  = (settings['force_delauth_nonprovisioned'].lower() == 'true')

        if 'appid' in settings:
            o.setAppId(settings['appid'])
        if 'secret' in settings:
            o.setSecret(settings['secret'])
        if 'securityalgorithm' in settings:
            o.setSecurityAlgorithm(settings['securityalgorithm'])
        if 'baseurl' in settings:
            o.setBaseUrl(settings['baseurl'])
        if 'secureurl' in settings:
            o.setSecureUrl(settings['secureurl'])
        if 'debug' in settings:
            o.setDebug(settings['debug'])
        if 'oldsecret' in settings:
            o.setOldSecret(settings['oldsecret'])
        if 'oldsecretexpiry' in settings:
            o.setOldSecretExpiry(settings['oldsecretexpiry'])
        if 'policyurl' in settings:
            o.setPolicyUrl(settings['policyurl'])
        if 'returnurl' in settings:
            o.setReturnUrl(settings['returnurl'])
        if 'consenturl' in settings:
            o.setConsentBaseUrl(settings['consenturl'])
        return o
    
    def setAppId(self, appid):
        """Sets the application ID. Use this method if you did not specify
        an application ID at initialization."""
        if not appid:
            if self.__force_delauth_nonprovisioned:
                return 
            self.fatal("Error: setAppId: Null application ID.")

        if not re.match(r'^\w+$', appid):
            self.fatal("Error: setAppId: Application ID must be alpha-numeric: %s" %
                       appid)
        
        self.__appid = appid

    def getAppId(self):
        """Returns the application ID."""
        if not self.__appid:
            self.fatal("Error: getAppId: Application ID was not set.  Aborting.")
        return self.__appid

    def setSecret(self, secret):
        """Sets your secret key. Use this method if you did not specify
        a secret key at initialization."""
        if not secret or (len(secret) < 16):
            if self.__force_delauth_nonprovisioned:
                return 
            self.fatal("Error: setSecret: Secret must be non-null.") 
        if len(secret) < 16:
            self.fatal("Error: setSecret: Secret must at least 16 characters.") 
        self.__signkey = self.derive(secret, "SIGNATURE")
        self.__cryptkey = self.derive(secret, "ENCRYPTION")

    def setOldSecret(self, oldsecret):
        """Sets your old secret key.

        Use this property to set your old secret key if you are in the
        process of transitioning to a new secret key. You may need this 
        property because the Windows Live ID servers can take up to 
        24 hours to propagate a new secret key after you have updated 
        your application settings.

        If an old secret key is specified here and has not expired
        (as determined by the oldsecretexpiry setting), it will be used
        as a fallback if token decryption fails with the new secret 
        key.
        """
        if not oldsecret:
            return
        if len(oldsecret) < 16:
            self.fatal("Error: setOldSecret: Secret must at least 16 characters.") 
        self.__oldsignkey = self.derive(oldsecret, "SIGNATURE")
        self.__oldcryptkey = self.derive(oldsecret, "ENCRYPTION")
       
    def setOldSecretExpiry(self, timestamp):
        """Sets the expiry time for your old secret key.

        After this time has passed, the old secret key will no longer be
        used even if token decryption fails with the new secret key.

        The old secret expiry time is represented as the number of seconds
        elapsed since January 1, 1970. 
        """
        if not timestamp:
            return
        try:
            timestamp = int(timestamp)
            if timestamp <= 0:
                raise WLLError("Error: setOldSecretExpiry: Invalid timestamp: %s" % timestamp)
            self.__oldsecretexpiry = timestamp
        except:
            raise WLLError("Error: setOldSecretExpiry: Invalid timestamp: %s" % timestamp)
                        
    def getOldSecretExpiry(self):
        """Gets the old secret key expiry time."""
        return self.__oldsecretexpiry

    def setSecurityAlgorithm(self, securityalgorithm):
        """Sets the version of the security algorithm being used."""
        self.__securityalgorithm = securityalgorithm

    def getSecurityAlgorithm(self):
        """Gets the version of the security algorithm being used."""
        if not self.__securityalgorithm:
            return "wsignin1.0"
        return self.__securityalgorithm

    def setPolicyUrl(self, policyurl):
        """Sets the privacy policy URL if you did not
        provide one at initialization time."""
        if not policyurl:
            if self.__force_delauth_nonprovisioned:
                return 
            self.fatal("Error: setAppId: Null application ID.")

        self.__policyurl = policyurl

    def getPolicyUrl(self):
        """Gets the privacy policy URL for your site."""
        if not self.__policyurl:
            self.debug("Warning: In the initial release of Del Auth, a Policy URL must be configured in the SDK for both provisioned and non-provisioned scenarios.")
            if self.__force_delauth_nonprovisioned:
                self.fatal("Error: getPolicyUrl: Policy URL must be set in a Del Auth non-provisioned scenario. Aborting.") 
        return self.__policyurl

    def setReturnUrl(self, returnurl):
        """Sets the return URL--the URL on your site to which the consent 
        service redirects users (along with the action, consent token, 
        and application context) after they have successfully provided 
        consent information for Delegated Authentication. This value will 
        override the return URL specified during registration.
        """
        if not returnurl:
            if self.__force_delauth_nonprovisioned:
                return 
            self.fatal("Error: setReturnUrl: Null return URL given.")
        self.__returnurl = returnurl

    def getReturnUrl(self):
        """Returns the return URL of your site."""
        if not self.__returnurl:
            if self.__force_delauth_nonprovisioned:
                self.fatal("Error: getReturnUrl: Return URL must be set in a Del Auth non-provisioned scenario. Aborting.") 
        return self.__returnurl


    def setBaseUrl(self, baseurl):
        """Sets the base URL to use for the Windows Live Login server. 
        You should not have to change this property. Furthermore, we recommend 
        that you use the Sign In control instead of the URL methods
        provided here.
        """
        self.__baseurl = baseurl

    def getBaseUrl(self):
        """Gets the base URL to use for the Windows Live Login server. 
        You should not have to use this property. Furthermore, we recommend 
        that you use the Sign In control instead of the URL methods 
        provided here.
        """
        if not self.__baseurl:
            return "http://login.live.com/"
        return self.__baseurl

    def setSecureUrl(self, secureurl):
        """Sets the secure (HTTPS) URL to use for the Windows Live Login 
        server. You should not have to change this property.
        """
        self.__secureurl = secureurl

    def getSecureUrl(self):
        """Gets the Secure (HTTPS) URL to use for the Windows Live 
        Login server.

        You should not have to use this. 
        """
        if not self.__secureurl:
            return "https://login.live.com/"
        return self.__secureurl

    def setConsentBaseUrl(self, consenturl):
        """Sets the Consent Base URL to use for the Windows Live Consent 
        server. You should not have to use or change this property directly.
        """
        self.__consenturl = consenturl

    def getConsentBaseUrl(self):
        """Gets the URL to use for the Windows Live Consent server. You
        should not have to use or change this directly.
        """
        if not self.__consenturl:
            return "https://consent.live.com/"
        return self.__consenturl


    def processLogin(self, fs):
        """Processes the sign-in response from the Windows Live Login server.

        'query' contains the preprocessed POST table, such as that
        returned by WebOb's Response object.

        This method returns a User object on successful sign-in; otherwise 
        it returns nil.
        """
        if not fs:
            self.debug("Error: processLogin: Query was null.")
            return

        if not 'action' in fs:
            self.debug("Warning: processLogin: No action in query.")
            return

        action = fs['action']
        if action != 'login':
            self.debug("Warning: processLogin: fs action ignored: %s." % action)
            return

        token = None
        context = None
        if 'stoken' in fs:
            token = fs["stoken"]
        if 'appctx' in fs:
            context = fs["appctx"]
            context = urllib.unquote(context)
        
        return self.processToken(token, context)

    def getLoginUrl(self, context=None, market=None):
        """Returns the sign-in URL to use for the Windows Live Login server. 
        We recommend that you use the Sign In control instead.
         
        If you specify it, 'context' will be returned as-is in the sign-in
        response for site-specific use.
        """
        url = self.getBaseUrl()
        url += "wlogin.srf?appid=" + self.getAppId()
        url += "&alg=" + self.getSecurityAlgorithm()
        if context:    
            url += "&appctx=" + urllib.quote(context)
        if market:    
            url += "&mkt=" + urllib.quote(market)
        return url

    def getLogoutUrl(self, market=None):
        """Returns the sign-out URL to use for the Windows Live Login server. 
        We recommend that you use the Sign In control instead.
        """
        url = self.getBaseUrl()
        url + "logout.srf?appid=" + self.getAppId()
        if market:    
            url += "&mkt=" + urllib.quote(market)
        return url
 
    def processToken(self, token, context=None):
        """Decodes and validates a Web Authentication token. Returns a User 
        object on success. If a context is passed in, it will be returned 
        as the context field in the User object.
        """
        if not token:
            self.debug('Error: processToken: Invalid token specified.')
            return
        
        decodedToken = self.decodeAndValidateToken (token)
        if not decodedToken:
            self.debug("Error: processToken: Failed to decode/validate token: " + token)
            return

        decodedToken = self.parse(decodedToken)
        if not decodedToken:
            self.debug("Error: processToken: Failed to parse token after decoding: " + token)
            return

        if not 'appid' in decodedToken:
            self.debug("Error: processToken: token does not contain application ID.")
            return
        sappid = decodedToken['appid']
        appid = self.getAppId()
        if sappid != appid:
            self.debug("Error: processToken: Application ID in token (%s) did not match application ID in configuration (%s)." %
                       (sappid, appid))
            return

        timestamp = None
        if 'ts' in decodedToken:
            timestamp = decodedToken['ts']
        userid = None
        if 'uid' in decodedToken:
            userid = decodedToken['uid']
        flags = None
        if 'flags' in decodedToken:
            flags = decodedToken['flags']

        try:
            return User(timestamp, userid, flags, context, token)
        except BaseException, e: 
            self.debug("Error: processToken: Contents of token considered invalid: %s" % e)
            return

    def getClearCookieResponse(self):
        """Returns an appropriate content type and body response that the 
        application handler can return to signify a successful sign-out 
        from the application.
         
        When a user signs out of Windows Live or a Windows Live
        application, a best-effort attempt is made at signing the user out
        from all other Windows Live applications the user might be signed
        in to. This is done by calling the handler page for each
        application with 'action' set to 'clearcookie' in the query
        string. The application handler is then responsible for clearing
        any cookies or data associated with the sign-in. After successfully
        signing the user out, the handler should return a GIF (any GIF)
        image as response to the 'action=clearcookie' query.
        """
        type = "image/gif"
        content = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAEALAAAAAABAAEAAAIBTAA7"
        content = base64.decodestring(content)
        return type, content

    def getConsentUrl(self, offers, context=None, ru=None, market=None):
        """Returns the consent URL to use for Delegated Authentication for
        the given comma-delimited list of offers.

        If you specify it, 'context' will be returned as-is in the consent
        response for site-specific use.

        The registered/configured return URL can also be overridden by 
        specifying 'ru' here.

        You can change the language in which the consent page is displayed
        by specifying a culture ID (For example, 'fr-fr' or 'en-us') in the
        'market' parameter.
        """
        if not offers:
            self.fatal("Error: getConsentUrl: Invalid offers list.")
            
        url = self.getConsentBaseUrl() + "Delegation.aspx?ps=" + urllib.quote(offers)
        if context:
            url += "&appctx=" + urllib.quote(context)
        if not ru:
            ru = self.getReturnUrl()
        if ru:
            url += "&ru=" + urllib.quote(ru)
        pu = self.getPolicyUrl()
        if pu:
            url += "&pl=" + urllib.quote(pu)
        if market:
            url += "&mkt=" + urllib.quote(market)
        if not self.__force_delauth_nonprovisioned:
            url += "&app=" + self.getAppVerifier() 
        return url        

    def getRefreshConsentTokenUrl(self, offers, refreshtoken, ru=None):
        """Returns the URL to use to download a new consent token, given the 
        offers and refresh token.
        The registered/configured return URL can also be overridden by 
        specifying 'ru' here.
        """
        if not offers:
            self.fatal("Error: getConsentUrl: Invalid offers list.")
        if not refreshtoken:
            self.fatal("Error: getConsentUrl: Invalid refresh token.")
            
        url = self.getConsentBaseUrl() + "RefreshToken.aspx?ps=" + urllib.quote(offers)
        url += "&reft=" + urllib.quote(refreshtoken)
        if not ru:
            ru = self.getReturnUrl()
        if ru:
            url += "&ru=" + urllib.quote(ru)
        pu = self.getPolicyUrl()
        if not self.__force_delauth_nonprovisioned:
            url += "&app=" + self.getAppVerifier() 
        return url        

    def getManageConsentUrl(self, market=None):
        """Returns the URL for the consent-management user interface.
        You can change the language in which the consent page is displayed
        by specifying a culture ID (For example, 'fr-fr' or 'en-us') in the
        'market' parameter.
        """
        url = self.getConsentBaseUrl() + "ManageConsent.aspx"
        if market:
            url += "?mkt=" + urllib.quote(market)
        return url        

    def processConsent(self, query):
        """Processes the POST response from the Delegated Authentication 
        service after a user has granted consent. The processConsent
        function extracts the consent token string and returns the result 
        of invoking the processConsentToken method. 
        """
        if not query:
            self.debug("Error: processConsent: Query was null.")
            return

        if not 'action' in query:
            self.debug("Warning: processConsent: No action in query.")
            return

        action = query['action']
        if action != 'delauth':
            self.debug("Warning: processConsent: query action ignored: %s." % action)
            return
        
        responsecode = query['ResponseCode']
        if not (responsecode == 'RequestApproved'):
            self.debug('Warning: processConsent: Consent was not successfully granted: $responsecode')
            return
            
        token = None
        context = None

        if 'ConsentToken' in query:
            token = query["ConsentToken"]
        if 'appctx' in query:
            context = query["appctx"]
            context = urllib.unquote(context)
        
        return self.processConsentToken(token, context)
        
    def processConsentToken(self, token, context=None):
        """Processes the consent token string that is returned in the POST 
        response by the Delegated Authentication service after a 
        user has granted consent.
        """
        if not token:
            self.debug("Error: processConsentToken: Null token.")
            return
            
        decodedtoken = token
        parsedtoken = self.parse(urllib.unquote(decodedtoken))
        if not parsedtoken:
          self.debug("Error: processConsentToken: Failed to parse token: " + token)
          return

        if 'eact' in parsedtoken:
            eact = parsedtoken['eact']
            if eact:
                decodedtoken = self.decodeAndValidateToken(eact)
                if not decodedtoken:
                    self.debug('Error: processConsentToken: Failed to decode/validate token: ' + token)
                    return
                
                parsedtoken = self.parse(decodedtoken)
                if not parsedtoken:
                    self.debug('Error: processConsentToken: Failed to parse token after decoding: ' + token)
                    return
                    
                decodedtoken = urllib.quote(decodedtoken)

        consenttoken = None
        if 'delt' not in parsedtoken:
            parsedtoken['delt'] = None
        if 'reft' not in parsedtoken:
            parsedtoken['reft'] = None
        if 'skey' not in parsedtoken:
            parsedtoken['skey'] = None
        if 'exp' not in parsedtoken:
            parsedtoken['exp'] = None
        if 'offer' not in parsedtoken:
            parsedtoken['offer'] = None
        if 'lid' not in parsedtoken:
            parsedtoken['lid'] = None
        try:
            consenttoken = ConsentToken(self, 
                                              parsedtoken['delt'],
                                              parsedtoken['reft'],
                                              parsedtoken['skey'],
                                              parsedtoken['exp'],
                                              parsedtoken['offer'],
                                              parsedtoken['lid'],
                                              context, decodedtoken, token)
        except BaseException, e:
            self.debug("Error: processConsentToken: Contents of token considered invalid %s." % e)
        return consenttoken

    def refreshConsentToken(self, token, ru=None):
        """Attempts to obtain a new, refreshed token and return it. The 
        original token is not modified.
        """
        if not token:
            self.debug("Error: refreshConsentToken: Null consent token.")
            return
        self.refreshConsentToken2(token.getOffersString(), token.getRefreshToken(), ru);
        
    def refreshConsentToken2(self, offers_string, refreshtoken, ru=None):
        """Helper function to obtain a new, refreshed token and return it.
        The original token is not modified.
        """
        try:
            url = self.getRefreshConsentTokenUrl(offers_string, refreshtoken, ru)
            body = self.fetch(url)
            if not body:
                self.debug("Error: refreshConsentToken2: Failed to obtain a new token.")
                return
                
            m = re.match(r'\{"ConsentToken":"(.*)"\}', body)
            if m:
                return self.processConsentToken(m.group(1))

            self.debug("Error: getAppSecurityToken: Failed to extract consent token: " +
                       body)
        except BaseException, e:
            self.debug("Error: refreshConsentToken2: Failed to refresh consent token: %s" % e)
        return

    def decodeAndValidateToken(self, token, cryptkey=None, signkey=None, internal_allow_recursion=True):
        """Decodes and validates the token."""
        if not cryptkey:
            cryptkey = self.__cryptkey
        if not signkey:
            signkey = self.__signkey
            
        haveoldsecret = False
        oldsecretexpiry = self.getOldSecretExpiry()
        oldcryptkey = self.__oldcryptkey;
        oldsignkey = self.__oldsignkey;

        if oldsecretexpiry and (oldsecretexpiry - time.time() > 0):
            if (oldcryptkey and oldsignkey):
                haveoldsecret = True;
        
        haveoldsecret = (haveoldsecret and internal_allow_recursion);
        
        stoken = self.decodeToken(token, cryptkey)
        if (stoken):
            stoken = self.validateToken(stoken, signkey)

        if (not stoken) and haveoldsecret:
            self.debug("Warning: Failed to validate token with current secret, attempting with old secret.");
            stoken = self.decodeAndValidateToken(token, oldcryptkey, oldsignkey, False)
        return stoken;

    def decodeToken(self, token, cryptkey=None):
        """Decodes the given token string; returns undef on failure.

        First, the string is URL-unescaped and base64 decoded.
        Second, the IV is extracted from the first 16 bytes of the string.
        Finally, the string is decrypted using the encryption key.
        """
        if not cryptkey:
            cryptkey = self.__cryptkey
        if not cryptkey:
            self.fatal("Error: decodeToken: Secret key was not set. Aborting.")
        token  = self.u64(token)
        if not token or (len(token) <= 16) or ((len(token) % 16) != 0):
            self.debug("Error: decodeToken: Attempted to decode invalid token.")
            return

        iv = token[0:16]
        crypted = token[16:]
        try:
            aes128cbc = AES.new(cryptkey, AES.MODE_CBC, iv)
            if not aes128cbc:
                raise WLLError("aes128cbc")
            return aes128cbc.decrypt(crypted)
        except:
            self.debug("Error: decodeToken: Could not construct cipher object to decode token.")
        return
        
    def signToken(self, token, signkey=None):
        """Creates a signature for the given string by using the
        signature key."""
        if not signkey:
            signkey = self.__signkey
        if not signkey:
            self.fatal("Error: signToken: Secret key was not set. Aborting.")
        try:
            hmac = HMAC.new(signkey, token, SHA256)
            if not hmac:
                raise WLLError("hmac")
            return hmac.digest()
        except:
            self.debug("Error: signToken: Unable to construct hash object to sign token.")
        return

    def validateToken(self, token, signkey=None):
        """Extracts the signature from the token and validates it."""
        if not signkey:
            signkey = self.__signkey
        if not token:
            self.debug("Error: validateToken: Null token specified.")
            return
        
        split = token.split("&sig=")    
        if len(split) != 2:
            self.debug("Error: validateToken: Invalid token: " + token)
            return
        body, sig = split
        sig = self.u64(sig)
        if sig != self.signToken(body, signkey):
            self.debug("Error: validateToken: Signature is not valid.")
            return
        return token


    ###################################################################
    # Implementation of the methods needed to perform Windows Live
    # application verification as well as trusted sign-in.
    ###################################################################
        
    def getAppVerifier(self, ip=None):
        """Generates an application verifier token. An IP address can 
        optionally be included in the token.
        """
        token = "appid=%s&ts=%s" % (self.getAppId(), self.getTimestamp())
        if ip:
            token += "&ip=" + ip
        token += "&sig=" + self.e64(self.signToken(token))
        return urllib.quote(token)
        
    def getAppLoginUrl(self, siteid=None, ip=None, js=None):
        """Returns the URL that is required to retrieve the application 
        security token.

        By default, the application security token is generated for 
        the Windows Live site; a specific Site ID can optionally be 
        specified in 'siteid'. The IP address can also optionally be 
        included in 'ip'.

        If 'js' is nil, a JavaScript Output Notation (JSON) response is 
        returned in the following format: 

        {"token":"<value>"}

        Otherwise, a JavaScript response is returned. It is assumed that
        WLIDResultCallback is a custom function implemented to handle the
        token value:

        WLIDResultCallback("<tokenvalue>");
        """
        url = self.getSecureUrl()
        url += "wapplogin.srf?app=" + self.getAppVerifier(ip)
        url += "&alg=" + self.getSecurityAlgorithm()
        if siteid:
            url += "&id=" + siteid
        if js:
            url += "&js=1"
        return url

    def getAppSecurityToken(self, siteid=None, ip=None):
        """Retrieves the application security token for application
        verification from the application sign-in URL.  

        By default, the application security token will be generated for
        the Windows Live site; a specific Site ID can optionally be
        specified in 'siteid'. The IP address can also optionally be
        included in 'ip'.

        Implementation note: The application security token is downloaded
        from the application sign-in URL in JSON format:

        {"token":"<value>"}

        Therefore we must extract <value> from the string and return it as
        seen here.
        """
        url  = self.getAppLoginUrl(siteid, ip)    
        body = self.fetch(url)
        if not body:
            self.debug("Error: getAppSecurityToken: Unable to fetch application security token.")
            return
            
        m = re.match(r'\{"token":"(.*)"\}', body)
        if m:
            return m.group(1)

        self.debug("Error: getAppSecurityToken: Failed to extract token: " +
                   body)
        return

    def getAppRetCode(self):
        """Returns a string that can be passed to the getTrustedParams
        function as the 'retcode' parameter. If this is specified as the
        'retcode', the application will be used as return URL after it
        finishes trusted sign-in.
        """
        return "appid=" + self.getAppId()

    def getTrustedParams(self, user, retcode=None):
        """Returns a table of key-value pairs that must be posted to the
        sign-in URL for trusted sign-in. Use HTTP POST to do this. Be aware
        that the values in the table are neither URL nor HTML escaped and
        may have to be escaped if you are inserting them in code such as
        an HTML form.

        The user to be trusted on the local site is passed in as string 
        'user'.

        Optionally, 'retcode' specifies the resource to which successful
        sign-in is redirected, such as Windows Live Mail, and is typically
        a string in the format 'id=2000'. If you pass in the value from
        getAppRetCode instead, sign-in will be redirected to the 
        application. Otherwise, an HTTP 200 response is returned.
        """
        token  = self.getTrustedToken(user)
        if not token:
            return
        token  = '<wst:RequestSecurityTokenResponse xmlns:wst="http://schemas.xmlsoap.org/ws/2005/02/trust"><wst:RequestedSecurityToken><wsse:BinarySecurityToken xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">%s</wsse:BinarySecurityToken></wst:RequestedSecurityToken><wsp:AppliesTo xmlns:wsp="http://schemas.xmlsoap.org/ws/2004/09/policy"><wsa:EndpointReference xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"><wsa:Address>uri:WindowsLiveID</wsa:Address></wsa:EndpointReference></wsp:AppliesTo></wst:RequestSecurityTokenResponse>' % token
        params = {}
        params['wa'] = self.getSecurityAlgorithm()
        params['wresult'] = token
        if retcode:
            params['wctx'] = retcode
        return params

    def getTrustedToken(self, user):
        """Returns the trusted sign-in token in the format that is needed by a
        control doing trusted sign-in.

        The user to be trusted on the local site is passed in as string
        'user'.
        """
        if not user:
            self.debug('Error: getTrustedToken: Null user specified.')
            return
        token  = "appid=%s&uid=%s&ts=%s" %\
                 (self.getAppId(), urllib.quote(user), self.getTimestamp())
        token += "&sig=" + self.e64(self.signToken(token))
        return urllib.quote(token)

    def getTrustedLoginUrl(self):
        """Returns the trusted sign-in URL to use for Windows Live
        Login server."""
        return self.getSecureUrl() + "wlogin.srf"

    def getTrustedLogoutUrl(self):
        """Returns the trusted sign-out URL to use for Windows Live
        Login server."""
        return self.getSecureUrl() + "logout.srf?appid=" + self.getAppId()


    ###################################################################
    # Helper methods.
    ###################################################################
    
    def parseSettings(self, settingsFile):
        """Function to parse the settings file."""
        settings = {}
        try:
            dom = xml.dom.minidom.parse(settingsFile)
        
            topnode = dom.getElementsByTagName("windowslivelogin")
            if len(topnode) < 1:
                self.fatal("Error: parseSettings: Failed to parse settings file: " +
                           settingsFile)

            for e in topnode[0].childNodes:
                if e.nodeType == e.ELEMENT_NODE:
                    settings[e.localName] = e.firstChild.nodeValue
       
        except BaseException, e:
            self.fatal("Error: parseSettings: Error while reading %s: %s" %
                       (settingsFile, e))
        return settings
            
    def derive(self, secret, prefix):
        """Derives the key, given the secret key and prefix as described in the
        Web Authentication SDK documentation."""
        if not secret:
            self.debug("Error: derive: Null secret specified.")
            return
        if not prefix:
            self.debug("Error: derive: Null prefix specified.")
            return
            
        key = prefix + secret
        key = SHA256.new(key).digest()

        if (not key) or (len(key) < 16):
            self.debug("Error: derive: Failed to generate valid hash.")
            return
            
        return key[0:16]

    def parse(self, inpuut):
        """Parses query string and returns a hash.

        If a hash ref is passed in from CGI->Var, it is dereferenced and
        returned."""
        if not inpuut:
            self.debug("Error: parse: Null input.")
            return

        inpuut = inpuut.split('&')
        pairs = {}
        for pair in inpuut:
            if pair.find("=") >= 0:
                k, v = pair.split('=')
                pairs[k] = v
        return pairs

    def getTimestamp(self):
        """Generates a time stamp suitable for the application verifier 
        token."""
        return "%i" % time.time()

    def e64(self, s):
        """Base64-encodes and URL-escapes a string."""
        if not s:
            return
        try:
            return urllib.quote(base64.encodestring(s))
        except:
            return

    def u64(self, s):
        """URL-unescapes and Base64-decodes a string."""
        if not s:
            return
        try:
            return base64.decodestring(urllib.unquote(s))
        except:
            return

    def fetch(self, url):
        """Fetches the contents given a URL."""
        try:
            f = urllib.urlopen(url)
            return f.read()
        except BaseException, e:
            self.debug("Error: fetch: %s" % e)
        return
        


