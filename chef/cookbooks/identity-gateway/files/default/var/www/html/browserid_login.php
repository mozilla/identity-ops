<html>
<head>
  <script src="https://login.persona.org/include.js" type="text/javascript">
</script>

  <title>Authentication</title>
</head>

<body style="margin-top:60px">
  <center>
    To access this resource :<br />
    <a href="#" onclick="doLogin()"><img src="/persona_sign_in_blue.png" /></a>
  </center>

  <form method="get" action="/mod_browserid_submit" id="loginform" name="loginform">
    <input type="hidden" name="assertion" id="assertion" />
    <input type="hidden" name="returnto" id="returnto" 
      value="<?php if (isset($_SERVER["REDIRECT_URL"])) echo $_SERVER["REDIRECT_URL"]; else echo "/"; ?>">
  </form>

  <script type="text/javascript">
//<![CDATA[
  function doLogin()
  {
      navigator.id.getVerifiedEmail(function(assertion) {
              document.getElementById("assertion").value = assertion;
              document.getElementById("loginform").submit();
      });
  }
  //]]>
  </script>
</body>
</html>