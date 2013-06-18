#
# Cookbook Name:: identity-bridge-gmail
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"

# Setup the user
user "browserid-bridge-gmail" do
  comment "Browserid Bridge Gmail Application User"
  uid node["browserid-bridge-gmail"][:uid]
  gid node["browserid-bridge-gmail"][:uid]
  home "/opt/browserid-bridge-gmail"
  supports :manage_home => true
end

# Setup directories
directory "/var/browserid-bridge-gmail" do
  owner "root"
  group "browserid-bridge-gmail"
  mode 0755
end

directory "/var/browserid-bridge-gmail/log" do
  owner "browserid-bridge-gmail"
  group "browserid-bridge-gmail"
  mode 0755
end

# Install rpms
rpms = [node["browserid-bridge-gmail"][:rpms]["browserid-bridge-gmail"],
        node["browserid-bridge-gmail"][:rpms][:nodejs]]

for rpm in rpms do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
    source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpm}"
  end
end

package "nodejs" do
  source "#{Chef::Config[:file_cache_path]}/#{node["browserid-bridge-gmail"][:rpms][:nodejs]}"
end

package "browserid-bridge-gmail" do
  source "#{Chef::Config[:file_cache_path]}/#{node["browserid-bridge-gmail"][:rpms]["browserid-bridge-gmail"]}"
  notifies :restart, "daemontools_service[browserid-bridge-gmail]", :delayed
end

# Configure
directory "/opt/browserid-bridge-gmail/config" do
  owner "root"
  group "root"
  mode 0755
end

template "/opt/browserid-bridge-gmail/config/production.json" do
  source "opt/browserid-bridge-gmail/config/production.json.erb"
  owner "root"
  group "root"
  mode 0644
  variables(:site_name => ["browserid-bridge-gmail"][:browserid_server][/https?:\/\/([^\/]*)/, 1])
  notifies :restart, "daemontools_service[browserid-bridge-gmail]", :delayed
end

file "/var/browserid-bridge-gmail/key.publickey" do
  content node["browserid-bridge-gmail"][:publickey]
  mode 0644
  owner "root"
  group "root"
end

file "/var/browserid-bridge-gmail/key.secretkey" do
  content node["browserid-bridge-gmail"][:secretkey]
  mode 0640
  owner "root"
  group "browserid-bridge-gmail"
end

# Start the node process
daemontools_service "browserid-bridge-gmail" do
  directory "/var/services/browserid-bridge-gmail"
  template "browserid-bridge-gmail"
  action [:enable, :start]
  log true
end


# Configure nginx
include_recipe "persona-common::nginx"

cookbook_file "/etc/nginx/conf.d/idbridgegmail.conf" do
  source "etc/nginx/conf.d/idbridgegmail.conf"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "daemontools_service[nginx]", :delayed
end

