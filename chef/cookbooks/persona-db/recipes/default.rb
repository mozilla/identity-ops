#
# Cookbook Name:: persona-db
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"

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
