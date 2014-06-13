#
# Cookbook Name:: bigtent
# Recipe:: default
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

include_recipe "persona-common::default"
include_recipe "persona-common::postfix"

rpms = [node[:bigtent][:rpms][:bigtent],
        node[:bigtent][:rpms][:certifier],
        node[:bigtent][:rpms][:nodejs]]

for rpm in rpms do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
    source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpm}"
  end
end

group "browserid" do
  gid 450
end

user "browserid" do
  home "/opt/browserid"
  comment "Browserid Application User"
  shell "/bin/bash"
  uid 450
  gid 450
end

for dir in ["/var/browserid", "/var/browserid/certifier", "/var/browserid/log"]
  directory dir do
    owner "browserid"
    group "browserid"
    mode 0700
  end
end

package "nodejs" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:bigtent][:rpms][:nodejs]}"
end

package "browserid-certifier" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:bigtent][:rpms][:certifier]}"
  notifies :restart, "daemontools_service[browserid-certifier]", :delayed
end

package "browserid-bigtent" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:bigtent][:rpms][:bigtent]}"
  notifies :restart, "daemontools_service[browserid-bigtent]", :delayed
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
  notifies :restart, "daemontools_service[browserid-bigtent]", :delayed
end

file "/var/browserid/certifier/key.secretkey" do
  owner "browserid"
  group "browserid"
  mode 0600
  content node[:bigtent][:secretkey]
  notifies :restart, "daemontools_service[browserid-certifier]", :delayed
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

include_recipe "persona-common::nginx"

cookbook_file "/etc/nginx/conf.d/idbigtent.conf" do
  source "etc/nginx/conf.d/idbigtent.conf"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "daemontools_service[nginx]", :delayed
end

include_recipe "persona-common::monitor"
