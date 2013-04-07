default["persona"]["db"]["rpms"]["mha4mysql-node"] = "mha4mysql-node-0.52-1.noarch.rpm"
default["persona"]["db"]["rpms"]["percona-toolkit"] = "percona-toolkit-2.0.2-1.noarch.rpm"
default["persona"]["db"]["rpms"]["Percona-Server-client-51"] = "Percona-Server-client-51-5.1.68-rel14.5.513.rhel6.x86_64.rpm"
default["persona"]["db"]["rpms"]["Percona-Server-devel-51"] = "Percona-Server-devel-51-5.1.68-rel14.5.513.rhel6.x86_64.rpm"
default["persona"]["db"]["rpms"]["Percona-Server-server-51"] = "Percona-Server-server-51-5.1.68-rel14.5.513.rhel6.x86_64.rpm"
default["persona"]["db"]["rpms"]["Percona-Server-shared-51"] = "Percona-Server-shared-51-5.1.68-rel14.5.513.rhel6.x86_64.rpm"

default["persona"]["db"]["mysql"]["replication_type"] = "slave"
default["persona"]["db"]["mysql"]["master-host"] = false        # the ip or dns name of the master
default["persona"]["db"]["mysql"]["master-user"] = false        # replication user name
default["persona"]["db"]["mysql"]["master-password"] = false    # replication user password
default["persona"]["db"]["mysql"]["master-port"] = false        # replication port

default["persona"]["mysql_uid"] = 451
