#
# Cookbook Name:: persona-db
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"
include_recipe "persona-db::monitor"

directory "/data" do
  owner "root"
  group "root"
  mode 0755
end

group "mysql" do
  gid node[:persona][:mysql_uid]
end

user "mysql" do
  comment "MySQL User"
  uid node[:persona][:mysql_uid]
  gid node[:persona][:mysql_uid]
  home "/data/mysql"
  supports :manage_home => true
end

directory "/data/mysql" do
  owner "mysql"
  group "mysql"
  mode 0750
end

# Note that installing Percona-Server-shared-51 first
# is required as it's a dependency for the other
# Percona packages
# Note that Percona-Server-shared-51 will remove
# the mysql-libs package
# Note I'm not adding in Percona-Server-shared-compat
# as it conflicts with Percona-Server-shared-51 and
# to include it will require breaking the yum depenency
# model on the system
for pkg in ["mha4mysql-node",
            "percona-toolkit",
            "Percona-Server-shared-51",
            "Percona-Server-client-51",
            "Percona-Server-server-51",
            "Percona-Server-devel-51"] do
  remote_file "#{Chef::Config[:file_cache_path]}/#{node[:persona][:db][:rpms][pkg]}" do
    source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{node[:persona][:db][:rpms][pkg]}"
  end
  package pkg do
    source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:db][:rpms][pkg]}"
  end
end

service "mysql" do
  action :stop
  not_if { ::File.directory?("/data/mysql/mysql")}
end

execute "mv /var/lib/mysql/mysql /data/mysql/mysql" do
  not_if { ::File.directory?("/data/mysql/mysql")}
end

cookbook_file "/etc/init.d/mysql" do
  # Original Percona init script is at
  # files/default/etc/init.d/mysql.orig
  source "etc/init.d/mysql"
  owner "root"
  group "root"
  mode 0755
  notifies :restart, "service[mysql]", :delayed
end

template "/etc/my.cnf" do
  source "etc/my.cnf.erb"
  owner "root"
  group "root"
  mode 0644
  # :innodb_buffer_pool_size : 75% of total memory
  # :server_id : ip address in integer form ( http://dev.mysql.com/doc/refman/5.1/en/replication-options.html#option_mysqld_server-id )
  variables({
    :innodb_buffer_pool_size => ((node[:memory][:total][0..-3].to_i) * 0.75).to_i.to_s + 
      node[:memory][:total][-2..-1],
    :server_id => node[:ipaddress].split('.').collect(&:to_i).pack('C*').unpack('N').first
  })
  notifies :restart, "service[mysql]", :delayed
end


file "/var/log/mysql-slow.log" do
  owner "mysql"
  group "mysql"
  mode 0644
end

# I'm unsure what this is used for and if we need it
# I assume it relates to mha4mysql-node
directory "/var/masterha" do
  owner "root"
  group "root"
  mode 0750
end

daemontools_service "heartbeat-browserid" do
  directory "/var/services/heartbeat-browserid"
  template "heartbeat-browserid"
  action [:enable, :start]
  log true
end

service "mysql" do
  action [:enable, :start]
end

# TODO : insert mysql.user and mysql.db records for nagiosdaemon browserid-rw browserid-ro
# GRANT ALL PRIVILEGES ON *.* TO 'nagiosdaemon'@'10.%' IDENTIFIED BY PASSWORD '*hashedpasswordgoeshere'
# INSERT INTO `user` VALUES ('10.%','replication','*hashedpasswordgoeshere','N','N','N','N','N','N','N','N','N','N','N','N','N','N','N','N','N','N','N','Y','N','N','N','N','N','N','N','N','','','','',0,0,0,0);
# flush privileges;

#<% if node[:persona][:db][:mysql][:replication_type] != "master" and node[:persona][:db][:mysql]["master-host"] %>
#master-host            = <%= node[:persona][:db][:mysql]["master-host"] %>
#master-user            = <%= node[:persona][:db][:mysql]["master-user"] %>
#master-password        = <%= node[:persona][:db][:mysql]["master-password"] %>
# CHANGE MASTER TO MASTER_HOST = '', MASTER_USER = '', MASTER_PASSWORD = '';

# SQLresponse=`mysql -u root --password=xxxxxx test -e "show slave status \G" |grep -i "Slave_SQL_Running"|gawk '{print $2}'`
# IOresponse=`mysql -u root --password=xxxxx test -e "show slave status \G" |grep -i "Slave_IO_Running"|gawk '{print $2}'`

# https://gist.github.com/grantr/1105416

if node[:persona][:db][:mysql][:replication_type] == "backup" then
  cookbook_file "/usr/local/bin/backup_mysql.sh" do
    source "usr/local/bin/backup_mysql.sh"
    user "root"
    group "root"
    mode 0755
  end
  file "/etc/cron.d/backup_mysql" do
    content "0 3 * * * root /usr/local/bin/backup_mysql.sh > /tmp/backup_mysql.output 2>&1\n"
    owner "root"
    group "root"
    mode 0644
    notifies :run, "execute[touch /etc/cron.d]", :immediately
  end
  execute "touch /etc/cron.d" do
    action :nothing
  end
end
