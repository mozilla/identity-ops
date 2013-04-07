default["persona"]["dbread"]["rpms"]["mha4mysql-node"] = "mha4mysql-node-0.52-1.noarch.rpm"
default["persona"]["dbread"]["rpms"]["percona-toolkit"] = "percona-toolkit-2.0.2-1.noarch.rpm"
default["persona"]["dbread"]["rpms"]["Percona-Server-client-51"] = "Percona-Server-client-51-5.1.68-rel14.5.513.rhel6.x86_64.rpm"
default["persona"]["dbread"]["rpms"]["Percona-Server-devel-51"] = "Percona-Server-devel-51-5.1.68-rel14.5.513.rhel6.x86_64.rpm"
default["persona"]["dbread"]["rpms"]["Percona-Server-server-51"] = "Percona-Server-server-51-5.1.68-rel14.5.513.rhel6.x86_64.rpm"
default["persona"]["dbread"]["rpms"]["Percona-Server-shared-51"] = "Percona-Server-shared-51-5.1.68-rel14.5.513.rhel6.x86_64.rpm"

node["persona"]["dbread"]["mysql"]["replication_type"] = "slave"
node["persona"]["dbread"]["mysql"]["master-host"] = "dbmaster.example.com"
node["persona"]["dbread"]["mysql"]["master-user"] = "replicationuser"
node["persona"]["dbread"]["mysql"]["master-password"] = "password-goes-here"

node["persona"]["mysql_uid"] = 451
