#
# Cookbook Name:: persona-splash
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"

rpms = {"apr" => "apr-1.4.6-1.x86_64.rpm",
        "apr-util" => "apr-util-1.5.2-1.x86_64.rpm",
        "apr-util-ldap" => "apr-util-ldap-1.5.2-1.x86_64.rpm",
        "httpd" => "httpd-2.4.4-1.x86_64.rpm",
        "httpd-tools" => "httpd-tools-2.4.4-1.x86_64.rpm",
        "mod_ssl" => "mod_ssl-2.4.4-1.x86_64.rpm"}

# TODO : This doesn't work for apr-util-ldap and apr-util because of circular dependencies
# TODO : This doesn't work for httpd, mod_ssl, and httpd-tools because of circular dependencies

for rpm in rpms.keys do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpms[rpm]}" do
    source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpms[rpm]}"
  end
end
for rpm in rpms.keys do
  package rpm do
    source "#{Chef::Config[:file_cache_path]}/#{rpms[rpm]}"
  end
end

package "httpd"
package "mod_ssl"

service "httpd" do
  action [:enable]
end

file "/etc/httpd/conf.d/ssl.conf" do
  action :delete
  notifies :restart, "service[httpd]", :delayed
end

cookbook_file "/etc/httpd/conf/httpd.conf" do
  source "etc/httpd/conf/httpd.conf"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[httpd]", :delayed
end

directory "/opt/splash" do
  owner "root"
  group "root"
  mode 0755
end

# Could fetch the zip : https://github.com/mozilla/persona.org/archive/prod.zip
execute "git clone https://github.com/mozilla/persona.org --branch prod --depth=1 /opt/splash" do
  not_if { ::File.exists?("/opt/splash/.git")}
end

execute "git pull https://github.com/mozilla/persona.org prod" do
  cwd "/opt/splash"
  not_if %q#git fetch -v --dry-run 2>&1 | awk '$NF == "origin/prod" {print $0}' | grep 'up to date'#
end

file "/etc/pki/tls/certs/multisan-www.persona.org.crt" do
  content node[:persona][:splash][:cert_body]
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[httpd]", :delayed
end
file "/etc/pki/tls/private/multisan-www.persona.org.key" do
  content node[:persona][:splash][:private_key]
  owner "root"
  group "root"
  mode 0600
  notifies :restart, "service[httpd]", :delayed
end
file "/etc/pki/tls/certs/multisan-www.persona.org.chain.crt" do
  content node[:persona][:splash][:cert_chain]
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[httpd]", :delayed
end

file "/etc/httpd/conf.d/ssl.conf" do
  action :delete
  notifies :restart, "service[httpd]", :delayed
end

template "/etc/httpd/conf.d/splash.conf" do
  source "etc/httpd/conf.d/splash.conf.erb"
  if node[:persona][:splash][:ip].is_a? Hash then
    variables(:ip => node[:persona][:splash][:ip][node[:aws_region]])
  else
    variables(:ip => node[:persona][:splash][:ip])
  end
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[httpd]", :delayed
end

service "httpd" do
  action [:start]
end