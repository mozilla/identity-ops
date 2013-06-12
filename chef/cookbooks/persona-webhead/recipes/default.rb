#
# Cookbook Name:: persona-webhead
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"
include_recipe "persona-common::app"

rpms = [node[:persona][:webhead][:rpms]["browserid-server"],
        node[:persona][:webhead][:rpms][:nodejs]]

for rpm in rpms do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
     source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpm}"
  end
end

package "nodejs" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:webhead][:rpms][:nodejs]}"
  notifies :restart, "daemontools_service[browserid-webhead]", :delayed
  notifies :restart, "daemontools_service[browserid-router]", :delayed
  notifies :restart, "daemontools_service[browserid-verifier]", :delayed
  notifies :restart, "daemontools_service[browserid-static]", :delayed
end

package "browserid-server" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:webhead][:rpms]["browserid-server"]}"
  notifies :restart, "daemontools_service[browserid-webhead]", :delayed
  notifies :restart, "daemontools_service[browserid-router]", :delayed
  notifies :restart, "daemontools_service[browserid-verifier]", :delayed
  notifies :restart, "daemontools_service[browserid-static]", :delayed
end

template "/opt/browserid/config/production.json" do
  source "opt/browserid/config/production.json.erb"
  owner "root"
  group "root"
  mode 0644

  vars = {}
  # We can change this to some other form of localized discovery later (e.g. DNS, chef-server environments, etc)
  if node[:persona][:webhead][:database][:host].is_a? Hash and node.include? :aws_region then
    vars[:database_host] = node[:persona][:webhead][:database][:host][node[:aws_region]]
  else
    vars[:database_host] = node[:persona][:webhead][:database][:host]
  end
  vars[:zone] = node[:persona][:site_name].split('.')[1..-1].join('.')
  variables vars
  notifies :restart, "daemontools_service[browserid-webhead]", :delayed
  notifies :restart, "daemontools_service[browserid-router]", :delayed
  notifies :restart, "daemontools_service[browserid-verifier]", :delayed
  notifies :restart, "daemontools_service[browserid-static]", :delayed
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
  # example public_url : "https://login.anosrep.org"
  variables(:site_name => node[:persona][:public_url][/https?:\/\/([^\/]*)/, 1],
            :base_site_name => node[:persona][:public_url][/https?:\/\/([^\/]*)/, 1].split('.')[-2..-1].join('.'))
  notifies :restart, "daemontools_service[nginx]", :delayed
end

template "/etc/nginx/conf.d/redirect.conf" do
  source "etc/nginx/conf.d/redirect.conf.erb"
  owner "root"
  group "root"
  mode 0644
  variables(:site_name => node[:persona][:public_url][/https?:\/\/([^\/]*)/, 1],
            :base_site_name => node[:persona][:public_url][/https?:\/\/([^\/]*)/, 1].split('.')[-2..-1].join('.'))
  notifies :restart, "daemontools_service[nginx]", :delayed
end
