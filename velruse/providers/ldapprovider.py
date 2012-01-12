"""Ldap Authentication Views"""
from pyramid.response import Response

import ldap

from velruse.api import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.utils import get_came_from, splitlines

"""
named ldapprovider not to conflict with python-ldap module.
"""


class LdapAuthenticationComplete(AuthenticationComplete):
    """Ldap auth complete"""

def includeme(config):
    config.add_route("ldap_login", "/ldap/login")
    config.add_route("ldap_process", "/ldap/process", use_global_views=True, factory=ldap_process)
    config.add_view(ldap_login, route_name="ldap_login")
    settings = config.registry.settings



FORM = """
<html>
    <head>
        <title>LDAP transaction in progress</title>
    </head>
    <body onload="document.forms[0].submit();">
        <form action="%s" method="post" accept-charset="UTF-8"
         enctype="application/x-www-form-urlencoded">
        <input type="hidden" name="end_point" value="%s" />
        <input type="hidden" name="ldap_username" value="%s" />
        <input type="hidden" name="ldap_password" value="%s" />
        <input type="submit" value="Continue"/></form>
        <script>
            var elements = document.forms[0].elements;
            for (var i = 0; i < elements.length; i++) {
                elements[i].style.display = "none";
            }
        </script>
    </body>                         
</html>
"""


def ldap_login(request):
    """Forward infos to process"""
    form = FORM % (
        request.route_url('ldap_process'),
        request.POST.get('end_point', ''),
        request.POST.get('ldap_username', ''),
        request.POST.get('ldap_password', ''),
    )
    return Response(form)

def ldap_process(request):
    """Initiate a ldap login"""
    config = request.registry.settings
    urls = splitlines(config['velruse.providers.ldapprovider.urls'])
    bdn = config['velruse.providers.ldapprovider.basedn']
    verified_login = False
    username = request.POST.get('ldap_username', request.POST.get('username', ''))
    password = request.POST.get('ldap_password', request.POST.get('password', ''))
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    dn = bdn.replace('%LOGIN%', username)
    data = {}
    if urls:
        for url in urls:
            try:
                # We have suceed to connect, break the loop
                con = ldap.initialize(url)
                bind = con.simple_bind_s(dn, password)
                verified_login = True
                items = con.search_s(dn,ldap.SCOPE_SUBTREE)
                if items:
                    for item in items:
                        if item[0] == dn:
                            data = item[1]
                            break
            except Exception, e:
                pass
    if not verified_login:
        reason = "Cannot verify the credentials with any of the ldap servers %s." % url
        return AuthenticationDenied(reason)
    profile = {}
    email, emails = '', data.get('mail', '')
    if emails:
        if isinstance(emails, list):
            email = emails[0]
        else:
            email = emails
    profile['accounts'] = [{
        'domain':'ldap',
        'username': username,
        'userid': username,
    }]
    if email:
        profile['verifiedEmail'] = email
        profile['emails'] = [{'value':email}]
    profile['displayName'] = username
    profile['end_point'] = get_came_from(request)
    cred = {'oauthAccessToken': '', 'oauthAccessTokenSecret': ''} 
    #return LdapAuthenticationComplete(profile=profile, credentials=cred)
    return AuthenticationComplete(profile=profile, credentials=cred) 

