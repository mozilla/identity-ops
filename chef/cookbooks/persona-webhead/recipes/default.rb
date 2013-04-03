#
# Cookbook Name:: persona-webhead
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"
include_recipe "persona-common::daemontools"

rpms = [node[:persona][:webhead][:rpms]["browserid-server"],
        node[:persona][:webhead][:rpms][:nodejs]]

for rpm in rpms do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
     source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpm}"
 end
end

package "nodejs" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:webhead][:rpms][:nodejs]}"
end

package "browserid-server" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:webhead][:rpms]["browserid-server"]}"
end

template "/opt/browserid/config/production.json" do
  source "opt/browserid/config/production.json.erb"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "daemontools_service[browserid-webhead]", :delayed
end

file "/var/browserid/browserid_cookie.sekret" do
  content node[:persona][:cookie_sekret]
  mode 0640
  user "root"
  group "browserid"
  notifies :restart, "daemontools_service[browserid-webhead]", :delayed
  notifies :restart, "daemontools_service[browserid-verifier]", :delayed
  notifies :restart, "daemontools_service[browserid-router]", :delayed
  notifies :restart, "daemontools_service[browserid-static]", :delayed
end

file "/var/browserid/root.cert" do
  content node[:persona][:root_cert]
  mode 0644
  user "root"
  group "browserid"
  notifies :restart, "daemontools_service[browserid-webhead]", :delayed
end

for svc in ["webhead", "verifier", "router", "static" ] do
  daemontools_service "browserid-#{svc}" do
    directory "/var/services/browserid-#{svc}"
    template "browserid-generic"
    variables :svc => svc
    action [:enable, :start]
    log true
  end
end

include_recipe "persona-webhead::metrics"

include_recipe "persona-common::nginx"

template "/etc/nginx/conf.d/idweb.conf" do
  source "etc/nginx/conf.d/idweb.conf.erb"
  owner "root"
  group "root"
  mode 0644
  variables(:site_name => node[:persona][:webhead][:public_url][/https?:\/\/([^\/]*)/, 1])
  notifies :restart, "daemontools_service[nginx]", :delayed
end

#cookbook_file "/etc/nginx/conf.d/redirect.conf" do
#  source "etc/nginx/conf.d/redirect.conf"
#  owner "root"
#  group "root"
#  mode 0644
#  notifies :restart, "daemontools_service[nginx]", :delayed
#end
