#
# Cookbook Name:: persona-monitor
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"
include_recipe "persona-common::postfix"

cookbook_file "/etc/yum.repos.d/opsview.repo" do
  source "etc/yum.repos.d/opsview.repo"
  mode 0644
  backup false
end 

package "opsview-agent" do
  # opsview-agent conflicts with opsview and must not be present
  action :purge
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
  #user "nagios"
  # We're supposed to run this as "nagios" however line 1786 of https://secure.opsview.com/svn/opsview/trunk/opsview-core/bin/nagconfgen.pl
  # depends on the "nagios" user being able to chown change the group of files that it owns which it can't
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

cookbook_file "/usr/local/nagios/share/images/favicon.png" do
  owner "root"
  group "root"
  mode 0644
  case node[:aws_region] + '-' + node[:stack][:type]
  when "us-west-2-stage"
    source "usr/local/nagios/share/images/opsview_favicon_stage.png"
  when "us-west-2-prod"
    source "usr/local/nagios/share/images/opsview_favicon_west.png"
  when "us-east-1-prod"
    source "usr/local/nagios/share/images/opsview_favicon_east.png"
  else
    source "usr/local/nagios/share/images/opsview_favicon_unknown.png"
  end
end

for patch_file in ["usr/local/opsview-web/root/wrappers/default",
                   "usr/local/opsview-web/root/navmenu/megamenu",
                   "usr/local/opsview-web/lib/Opsview/Web/Controller/NavMenu.pm",
                   "usr/local/opsview-web/root/wrapper_footer"] do
  cookbook_file "/#{patch_file}.patch" do
     source "#{patch_file}.patch"
     owner "root"
     group "root"
     mode 0644
  end
  execute "patch --input /#{patch_file}.patch --forward --silent /#{patch_file}" do
    only_if "patch --input /#{patch_file}.patch --forward --silent --dry-run /#{patch_file}"
    notifies :restart, "service[opsview-web]", :delayed
  end
end

include_recipe "persona-monitor::nagios_plugins"
