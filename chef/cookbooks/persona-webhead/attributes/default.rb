default["persona"]["webhead"]["rpms"]["browserid-server"] = "browserid-server-0.2013.02.01-2.el6_112745.x86_64.rpm"
default["persona"]["webhead"]["rpms"]["nodejs"] = "nodejs-0.8.17-1.el6.x86_64.rpm"
default["persona"]["loadtest"] = false

default["persona"]["webhead"]["public_url"] = "https://login.example.com"
default["persona"]["webhead"]["public_static_url"] = "https://static.login.example.com"
default["persona"]["webhead"]["verifier_url"] = "https://example.com"
default["persona"]["webhead"]["keysigner_url"] = "http://keysign-example-123456.us-west-2.elb.amazonaws.com"
default["persona"]["webhead"]["dbwriter_url"] = "http://dbwrite-example-123456.us-west-2.elb.amazonaws.com"
default["persona"]["webhead"]["proxy_idps"] = { "yahoo.com" => "yahoo.login.example.com" }

default["persona"]["webhead"]["kpi_backend_sample_rate"] = 0.2
default["persona"]["webhead"]["database"]["host"] = "dbread-example-123456.us-west-2.elb.amazonaws.com"
default["persona"]["webhead"]["database"]["user"] = "browseridro"
default["persona"]["webhead"]["database"]["password"] = "password-goes-here"
default["persona"]["webhead"]["kpi_backend_db_url"] = "https://kpi.example.com/wsapi/interaction_data"
