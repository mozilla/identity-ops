#
# Cookbook Name:: persona-admin
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"
#include_recipe "persona-db::monitor"

cookbook_file "/usr/local/bin/get_hosts" do
  source "usr/local/bin/get_hosts"
  owner "root"
  group "root"
  mode 0755
end

cookbook_file "/usr/local/bin/get_region" do
  source "usr/local/bin/get_region"
  owner "root"
  group "root"
  mode 0755
end

package "httpd"
package "php"

service "httpd" do
  action [:start, :enable]
end

for rpm in ["yajl-2.0.4-2.el6.x86_64.rpm", "mod_auth_browserid-0.1-1.el6.x86_64.rpm"] do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
    source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpm}"
  end
end

package "yajl" do
  source "#{Chef::Config[:file_cache_path]}/yajl-2.0.4-2.el6.x86_64.rpm"
end

package "mod_auth_browserid" do
  source "#{Chef::Config[:file_cache_path]}/mod_auth_browserid-0.1-1.el6.x86_64.rpm"
  notifies :restart, "service[httpd]", :delayed
end

for file in ["var/www/html/browserid_login.php",
             "var/www/html/persona_sign_in_blue.png",
             "var/www/mod_browserid_users"] do
  cookbook_file "/#{file}" do
    source file
    owner "root"
    group "root"
    mode 0644
  end
end

template "/etc/httpd/conf.d/persona-admin.conf" do
  source "etc/httpd/conf.d/persona-admin.conf.erb"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[httpd]", :delayed
end
