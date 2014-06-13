#
# Cookbook Name:: identity-gateway
# Recipe:: default
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
             "var/www/mod_browserid_users",
             "etc/httpd/conf.d/graphite-web.conf",
             "etc/httpd/conf.d/mod_browserid.include"] do
  cookbook_file "/#{file}" do
    source file
    owner "root"
    group "root"
    mode 0644
  end
end

template "/etc/httpd/conf.d/identity-gateway.conf" do
  source "etc/httpd/conf.d/identity-gateway.conf.erb"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[httpd]", :delayed
end

package "mod_ssl" do
  notifies :restart, "service[httpd]", :delayed
end

file "/etc/httpd/conf.d/ssl.conf" do
  content ""
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[httpd]", :delayed
end

file "/etc/pki/tls/certs/identity-gateway.crt" do
  content node[:persona][:identity_gateway][:cert][:cert_body]
  owner "root"
  group "root"
  mode 0600
  notifies :restart, "service[httpd]", :delayed
end

file "/etc/pki/tls/private/identity-gateway.key" do
  content node[:persona][:identity_gateway][:cert][:private_key]
  owner "root"
  group "root"
  mode 0600
  notifies :restart, "service[httpd]", :delayed
end
