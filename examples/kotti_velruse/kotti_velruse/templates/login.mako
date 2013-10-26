<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
	<title>${project} :: Login</title>
	<!-- Simple OpenID Selector -->
	<link type="text/css" rel="stylesheet" href="css/openid.css" />
	<script type="text/javascript" src="js/jquery-1.2.6.min.js"></script>
	<script type="text/javascript" src="js/openid-jquery.js"></script>
	<script type="text/javascript" src="js/openid-en.js"></script>
	<script type="text/javascript">
		$(document).ready(function() {
			openid.init('openid_identifier');
			openid.setDemoMode(false); //Stops form submission for client javascript-only test purposes
		});
	</script>
	<!-- /Simple OpenID Selector -->
	<style type="text/css">
		/* Basic page formatting */
		body {
			font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		}
	</style>
</head>

<body>
	<h2>Login to ${project}</h2>
	<!-- Simple OpenID Selector -->
	<form action="${login_url}" method="get" id="openid_form">
		<input type="hidden" name="action" value="verify" />
		<fieldset>
			<legend>Sign-in</legend>
			<div id="openid_choice">
				<p>Please click your account provider:</p>
				<div id="openid_btns"></div>
			</div>
			<div id="openid_input_area">
				<input id="openid_identifier" name="openid_identifier" type="text" value="http://" />
				<input id="openid_submit" type="submit" value="Sign-In"/>
			</div>
		</fieldset>
	</form>
	<!-- /Simple OpenID Selector -->
	<p>OpenID allows you to log-on to many different websites using a single identity.<br/>
           Find out <a href="http://openid.net/what/">more about OpenID</a> and
           <a href="http://openid.net/get/">how to get an OpenID enabled account</a>.</p>
</body>
</html>
