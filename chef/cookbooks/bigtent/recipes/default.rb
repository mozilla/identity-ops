#
# Cookbook Name:: bigtent
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "bigtent::daemontools"

rpms = [node[:bigtent][:rpms][:bigtent],
        node[:bigtent][:rpms][:certifier],
        node[:bigtent][:rpms][:nodejs]]

for rpm in rpms do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
    source "https://s3-us-west-2.amazonaws.com/svcops-us-west-2/identity/rpms/#{rpm}"
  end
end

service "ntpd" do
  action :start
end

group "browserid" do
  gid 450
end

user "browserid" do
  comment "Browserid Application User"
  uid 450
  gid 450
  home "/opt/browserid"
end

directory "/var/browserid" do
  owner "root"
  group "browserid"
  mode 0755
end

directory "/var/browserid/certifier" do
  owner "browserid"
  group "browserid"
  mode 0700
end

directory "/var/browserid/log" do
  owner "browserid"
  group "browserid"
  mode 0755
end

package "nodejs" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:bigtent][:rpms][:nodejs]}"
end

package "browserid-certifier" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:bigtent][:rpms][:certifier]}"
end

package "browserid-bigtent" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:bigtent][:rpms][:bigtent]}"
end

template "/opt/bigtent/config/production.json" do
  source "opt/bigtent/config/production.json.erb"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "daemontools_service[browserid-bigtent]", :delayed
end

template "/opt/certifier/config/production.json" do
  source "opt/certifier/config/production.json.erb"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "daemontools_service[browserid-certifier]", :delayed
end

file "/var/browserid/certifier/key.publickey" do
  owner "browserid"
  group "browserid"
  mode 0600
  content node[:bigtent][:publickey]
end

file "/var/browserid/certifier/key.secretkey" do
  owner "browserid"
  group "browserid"
  mode 0600
  content node[:bigtent][:secretkey]
end

daemontools_service "browserid-certifier" do
  directory "/var/services/browserid-certifier"
  template "browserid-certifier"
  action [:enable, :start]
  log true
end

daemontools_service "browserid-bigtent" do
  directory "/var/services/browserid-bigtent"
  template "browserid-bigtent"
  action [:enable, :start]
  log true
end

include_recipe "bigtent::nginx"

