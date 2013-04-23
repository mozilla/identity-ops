#
# Cookbook Name:: persona-monitor
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

cookbook_file "/etc/yum.repos.d/opsview.repo" do
  source "etc/yum.repos.d/opsview.repo"
  mode 0644
  backup false
end 

package "opsview"

service "mysqld" do
  action [:enable, :start]
end

execute "/usr/bin/mysqladmin -u root password '#{node[:persona][:monitor][:mysql][:root_password]}'" do
  action :run
  only_if "/usr/bin/mysql -u root -e 'show databases;'"
end

template "/usr/local/nagios/etc/opsview.conf" do
  source "usr/local/nagios/etc/opsview.conf.erb"
  owner "nagios"
  group "nagios"
  mode 0640
end

execute "/usr/local/nagios/bin/db_mysql -u root -p#{node[:persona][:monitor][:mysql][:root_password]}" do
  action :run
  user "nagios"
  not_if "/usr/bin/mysql -uopsview -p#{node[:persona][:monitor][:dbpasswd]} -e 'show databases;'"
end

execute "/usr/local/nagios/bin/db_opsview db_install" do
  action :run
  user "nagios"
  not_if "/usr/bin/mysql -uopsview -p#{node[:persona][:monitor][:dbpasswd]} -e 'DESCRIBE monitoringservers;' opsview"
end

execute "/usr/local/nagios/bin/db_runtime db_install" do
  action :run
  user "nagios"
  not_if "/usr/bin/mysql -unagios -p#{node[:persona][:monitor][:runtime_dbpasswd]} -e 'DESCRIBE snmptrapexceptions;' runtime"
end

execute "/usr/local/nagios/bin/rc.opsview gen_config" do
  action :run
  user "nagios"
  creates "/usr/local/nagios/configs/Master Monitoring Server/nagios.cfg"
end

service "opsview-web" do
  action :start
end

service "httpd" do
  action [:enable, :start]
end

cookbook_file "/etc/httpd/conf.d/opsview.conf" do
  source "etc/httpd/conf.d/opsview.conf"
  mode 0644
  backup false
  notifies :restart, "service[httpd]", :delayed
end 

  
