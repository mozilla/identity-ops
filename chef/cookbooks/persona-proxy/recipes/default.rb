#
# Cookbook Name:: persona-proxy
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"

remote_file "#{Chef::Config[:file_cache_path]}/#{node[:persona][:proxy][:rpms][:squid]}" do
   source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{node[:persona][:proxy][:rpms][:squid]}"
end

package "squid" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:proxy][:rpms][:squid]}"
end

cookbook_file "/etc/squid/cacert.pem" do
  source "etc/squid/cacert.pem"
end

template "/etc/squid/squid.conf" do
  source "etc/squid/squid.conf.erb"
  notifies :restart, "service[squid]", :delayed
end

service "squid" do
  action [:enable, :start]
end

include_recipe "persona-common::monitor"
