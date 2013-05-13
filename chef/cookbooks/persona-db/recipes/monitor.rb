#
# Cookbook Name:: persona-db
# Recipe:: monitor
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

for file in ["usr/local/nagios/libexec/check_mysql_innodb",
             "usr/local/nagios/libexec/check_mysql_percona_heartbeat"]
  cookbook_file "/#{file}" do
    source file
    owner "root"
    group "root"
    mode 0755
  end
end

cookbook_file "/usr/local/nagios/etc/nrpe_local/override.cfg" do
  source "usr/local/nagios/etc/nrpe_local/override.cfg"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[opsview-agent]", :delayed
end
