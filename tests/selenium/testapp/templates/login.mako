<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Auth Page</title>
</head>
<body>

<form id="facebook" action="http://localhost:5000/velruse/facebook/login" method="post">
<input type="hidden" name="scope" value="email,publish_stream,read_stream,create_event,offline_access" />
<input type="submit" value="Login with Facebook" />
</form>

<form id="github" action="http://localhost:5000/velruse/github/login" method="post">
<input type="submit" value="Login with GitHub" />
</form>

<form id="twitter" action="http://localhost:5000/velruse/twitter/login" method="post">
<input type="submit" value="Login with Twitter" />
</form>

<form id="bitbucket" action="http://localhost:5000/velruse/bitbucket/login" method="post">
<input type="submit" value="Login with Bitbucket" />
</form>

<!--
<form id="google" action="http://teaparty.mine.nu:9090/google/auth" method="post">
<input type="hidden" name="use_popup" value="false" />
<input type="hidden" name="oauth_scope" value="https://www.google.com/analytics/feeds/" />
<input type="hidden" name="openid_identifier" value="google.com" />
<input type="submit" value="Login with Google" />
</form>

<form id="yahoo" action="http://teaparty.mine.nu:9090/yahoo/auth" method="post">
<input type="hidden" name="openid_identifier" value="yahoo.com" />
<input type="hidden" name="oauth" value="true" />
<input type="submit" value="Login with Yahoo" />
</form>

<form id="windows_live" action="http://teaparty.mine.nu/live/auth" method="post">
<input type="submit" value="Login with Windows Live" />
</form>
-->

</body>
</html>
