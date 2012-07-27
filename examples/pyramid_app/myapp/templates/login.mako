<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Auth Page</title>
</head>
<body>

<%def name="form(name, title)">
<form id="${name}" method="post" action="/velruse/login/${ name }">
    <input type="submit" value="${title}" />
</form>
</%def>

${form('facebook', 'Login with Facebook')}
${form('github', 'Login with Github')}
${form('twitter', 'Login with Twitter')}
${form('bitbucket', 'Login with Bitbucket')}
${form('google', 'Login with Google')}
${form('yahoo', 'Login with Yahoo')}
${form('live', 'Login with Windows Live')}

</body>
</html>
