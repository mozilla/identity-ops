#
# Cookbook Name:: persona-keysign
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"
include_recipe "persona-common::app"

rpms = [node[:persona][:keysign][:rpms]["browserid-server"],
        node[:persona][:keysign][:rpms][:nodejs]]

for rpm in rpms do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
     source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpm}"
 end
end

package "nodejs" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:keysign][:rpms][:nodejs]}"
  notifies :restart, "daemontools_service[browserid-keysign]", :delayed
end

package "browserid-server" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:keysign][:rpms]["browserid-server"]}"
  notifies :restart, "daemontools_service[browserid-keysign]", :delayed
end

template "/opt/browserid/config/production.json" do
  source "opt/browserid/config/production.json.erb"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "daemontools_service[browserid-keysign]", :delayed
end

file "/var/browserid/browserid_cookie.sekret" do
  content node[:persona][:cookie_sekret]
  mode 0640
  user "root"
  group "browserid"
  notifies :restart, "daemontools_service[browserid-keysign]", :delayed
end

file "/var/browserid/root.cert" do
  content node[:persona][:root_cert]
  mode 0644
  user "root"
  group "browserid"
  notifies :restart, "daemontools_service[browserid-keysign]", :delayed
end

file "/var/browserid/root.secretkey" do
  content node[:persona][:keysign][:root_secretkey]
  mode 0640
  user "root"
  group "browserid"
  notifies :restart, "daemontools_service[browserid-keysign]", :delayed
end

daemontools_service "browserid-keysign" do
  directory "/var/services/browserid-keysign"
  template "browserid-keysign"
  action [:enable, :start]
  log true
end

include_recipe "persona-common::nginx"

cookbook_file "/etc/nginx/conf.d/idkeysign.conf" do
  source "etc/nginx/conf.d/idkeysign.conf"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "daemontools_service[nginx]", :delayed
end
