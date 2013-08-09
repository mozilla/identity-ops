default["persona"]["monitor"]["mysql"]["root_password"] = "your root password goes here"
default["persona"]["monitor"]["nrd_shared_password"] = "something goes here not sure what yet"
default["persona"]["monitor"]["runtime_dbpasswd"] = "your alpha numeric nagios user password goes here"
default["persona"]["monitor"]["dbpasswd"] = "your alpha numeric opsview user password goes here"

default["persona"]["monitor"]["dynect"]["customer"] = "dynect-customer-name"
default["persona"]["monitor"]["dynect"]["user"] = "dynect-user"
default["persona"]["monitor"]["dynect"]["pass"] = "dynect-password"

normal["aws"]["metadata_readers"] = ["nagios"]
