default["persona"]["browserid_uid"] = 450
default["persona"]["nginx_uid"] = 452

# Setting these to false bypasses the proxy
# default["proxy"]["host"] = "proxy.example.com"
# default["proxy"]["port"] = 3128
default["proxy"]["host"] = false
default["proxy"]["port"] = false

default["persona"]["cookie_sekret"] = "sgf9z90YqiF10fIreXMHJThJddUIpp9mwSHrSaYpPQkzKj5VudqhU47b0qKpT7Bqy0hsmujc19RwVFK42oZ1p5lZ5GiU1A6yxdd2wD97HzwchsRaDs0kbyEARb6lQg0h"
default["persona"]["root_cert"] = "eyJhbGciOiJSUzI1NiJ9.eyJwdWJsaWMta2V5Ijp7ImFsZ29yaXRobSI6IlJTIiwibiI6IjI1MTAwNDYxNDUyMDgyNzMwMTEyNjk5OTU2NDQyNzcwNTYxMzk2Mjk5NjQ0NDQ2NzAxMDkwMDAyODE2Mjg4MzQ3NjE0MzA4NjczNTkzMDUyNTc4MjExNDQyMDgyNjI3MTQyNzc4NTk1NzU1OTY4MDc0ODY2NDk2MjM1ODg0OTY0NjIyMjc3MjQ0NzYyMTYyMTg3MjgyMzA4Njg4ODQ4NjI1MTcyNzU4MDMyNDgwNTU5NTA2MDQ5OTExODU5NzYwODY2OTIzNjk5MjUyMjc5MTM3NzAwODAzNzk0OTAwNjUwMjExMzI5MzQzMDcxMDU1NDUyNzMxMTk2NzA2MTIyNDEwMjE2MjIxNjY3NDE4MDY5MTUyMjcwODk2MzI0Nzk4MjM2MzU3MTE3ODEzMzU1NjA5Njk1OTQwNzMxNzM3MTEwNzExNDQwNzI3NzAzNzczNjI4MDQwNTkyMDAzMzU3NTc2NDQ0Mjc0NjAwMTY0Njc3MDg2ODIzNzEwOTI0ODgxODQxOTQ5Mzc2ODM0MjYxMTI3NTc4MTcxNzkxMTIyNjUzNDg1MzkyMTM0ODgzMzc1NzIxMzIxNjAwODk3NDgzOTYwODM4NzE4MzIwODU3NDc0ODkzMDcwNjUzODE5NzI2NDQ3MTIzNzM1ODUwMDM2OTMwODg1MzgyMzY2NDc5MTYyNDcxODc2NzExNjI2ODU3ODE5NjQ5ODU3NDg1NzgxNTcxNDc2MDgzMTQ5NDYwNTQxNDk3OTk4MDA5NDE0MjU4OTEwOTUzMjg2MTgxNzkzNTQzMzU4MjIwOTA0ODk0NjQzODk4NDQ4MTUxIiwiZSI6IjY1NTM3In0sInByaW5jaXBhbCI6e30sImlhdCI6MTM0NDI3NjY3MzU1NSwiZXhwIjoxMzc1ODEyNjczNTU1fQ.KLyDoqrMnrDznpvspDiZNmk_SmirU4ipd1_0pjvA75kdl1Ix7z51C53F-LXzFjE43h5NWXm_jgZc6l8xGQ4glhmITKVrysU-osgKHrw9DTQtM0s_x2bNa7CC7PXiDKL1YKQ2IZmXwbDNc5RO-fR2CDrHylwgZKAEdz_LI4YH9dDEUJ7-Jz6R1ioiLINe_r5Zk5t9yTcVk9MJgePPCorDdeRpC8g3y7T0xIvu1RdfyYHBRDwQjT5j71JwFWl0mzVgXtAVquWikj7rlHmsGyZodkMrvKrCwQHo40cPQp8ogGW7NU26TmSLttHErPx4_PMqIFkzh_AHTZWAthIFBhpBxQ"

default["persona"]["site_name"] = "login.example.com"
default["persona"]["public_url"] = "https://login.example.com"
default["persona"]["public_static_url"] = "https://static.login.example.com"
default["persona"]["verifier_url"] = "https://example.com"
default["persona"]["keysigner_url"] = "http://keysign-example-123456.us-west-2.elb.amazonaws.com"
default["persona"]["dbwriter_url"] = "http://dbwrite-example-123456.us-west-2.elb.amazonaws.com"
default["persona"]["proxy_idps"] = { "yahoo.com" => "yahoo.login.example.com" }

default["persona"]["postfix"]["smtp_host"] = false
default["persona"]["postfix"]["smtp_port"] = false
default["persona"]["postfix"]["smtp_user"] = false
default["persona"]["postfix"]["smtp_password"] = false

default["persona"]["rpms"]["librsbac"] = "librsbac-1.4.5-4.el6.x86_64.rpm"
default["persona"]["rpms"]["rsbac"] = "rsbac-1.4.5-4.el6.x86_64.rpm"
default["persona"]["rpms"]["kernel"] = "kernel-2.6.32-131.6.1.el6.rsbac.x86_64.rpm"

default["persona"]["dbwrite_host"] = "dbwrite.example.com"
default["persona"]["keysign_host"] = "keysign.example.com"

default["aws"]["metadata_readers"] = []

default["stack"]["load_balancers"] = { }
default["tier"] = false
default["stack"]["name"] = false
default["stack"]["type"] = false
default["aws_region"] = false
