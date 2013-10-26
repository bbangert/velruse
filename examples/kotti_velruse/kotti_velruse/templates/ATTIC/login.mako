<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Auth Page</title>
</head>
<body>

<%def name="form(name, title, **kw)">
% if name in providers:
<form id="${name}" action="${login_url(request, name)}" method="post">
    % for k, v in kw.items():
    <input type="hidden" name="${k}" value="${v}" />
    % endfor
    <input type="submit" value="${title}" />
</form>
% else:
<form id="${name}" method="post">
    <input type="submit" value="${title}" disabled="disabled" />
</form>
% endif
</%def>




${form('google', 'Login with Google',                 openid_identifier='google.com', use_popup='false')}
${form('google_hybrid', 'Login with Google (Hybrid)', openid_identifier='google.com', use_popup='false')}
${form('google_oauth2', 'Login with Google (OAuth2)', openid_identifier='google.com', use_popup='false')}
${form('yahoo', 'Login with Yahoo',                   openid_identifier='yahoo.com',  oauth='true')}
${form('live', 'Login with Windows Live')}
${form('facebook', 'Login with Facebook', scope='email,publish_stream,read_stream,create_event,offline_access')}
${form('twitter', 'Login with Twitter')}
${form('github', 'Login with Github')}
${form('bitbucket', 'Login with Bitbucket')}

${form('openid', 'Login with XKBM.NET',  openid_identifier='openid.fake.net:6060/id/rgomes', use_popup='false')}
${form('openid', 'Login with Launchpad', openid_identifier='launchpad.net/~frgomes',   use_popup='false')}

</body>
</html>
