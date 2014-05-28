#
# Cookbook Name:: persona-dbwrite
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"
include_recipe "persona-common::app"
include_recipe "persona-common::postfix"

rpms = [node[:persona][:dbwrite][:rpms]["browserid-server"]]

for rpm in rpms do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
     source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpm}"
 end
end

package "nodejs-svcops" do
  notifies :restart, "daemontools_service[browserid-dbwrite]", :delayed
end

package "browserid-server" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:dbwrite][:rpms]["browserid-server"]}"
  notifies :restart, "daemontools_service[browserid-dbwrite]", :delayed
end

template "/opt/browserid/config/production.json" do
  source "opt/browserid/config/production.json.erb"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "daemontools_service[browserid-dbwrite]", :delayed
end

file "/var/browserid/browserid_cookie.sekret" do
  content node[:persona][:cookie_sekret]
  mode 0640
  user "root"
  group "browserid"
  notifies :restart, "daemontools_service[browserid-dbwrite]", :delayed
end

file "/var/browserid/root.cert" do
  content node[:persona][:root_cert]
  mode 0644
  user "root"
  group "browserid"
  notifies :restart, "daemontools_service[browserid-dbwrite]", :delayed
end

daemontools_service "browserid-dbwrite" do
  directory "/var/services/browserid-dbwrite"
  template "browserid-dbwrite"
  action [:enable, :start]
  log true
end

include_recipe "persona-common::nginx"

cookbook_file "/etc/nginx/conf.d/iddbwrite.conf" do
  source "etc/nginx/conf.d/iddbwrite.conf"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "daemontools_service[nginx]", :delayed
end

include_recipe "persona-common::monitor"
