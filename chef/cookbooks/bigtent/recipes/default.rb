#
# Cookbook Name:: bigtent
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

rpms = [node[:bigtent][:rpms][:bigtent],
        node[:bigtent][:rpms][:certifier],
        node[:bigtent][:rpms][:nodejs]]

for rpm in rpms do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
    source "https://s3-us-west-2.amazonaws.com/svcops-us-west-2/identity/rpms/#{rpm}"
  end
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

for dir in ["/var/browserid/certifier",
            "/var/browserid/log",
            ] do
  directory dir do
    owner "browserid"
    group "browserid"
    recursive true
  end
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
end

template "/opt/certifier/config/production.json" do
  source "opt/certifier/config/production.json.erb"
  owner "root"
  group "root"
  mode 0644
end

file "/var/browserid/certifier/key.publickey" do
  owner "root"
  group "root"
  mode 0644
  content node[:bigtent][:publickey]
end

file "/var/browserid/certifier/key.secretkey" do
  owner "root"
  group "root"
  mode 0644
  content node[:bigtent][:secretkey]
end

include_recipe "bigtent::nginx"

include_recipe "bigtent::daemontools"
