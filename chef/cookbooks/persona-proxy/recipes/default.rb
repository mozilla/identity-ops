#
# Cookbook Name:: persona-proxy
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

package "squid"

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
