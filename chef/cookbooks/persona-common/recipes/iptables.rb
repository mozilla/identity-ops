#
# Cookbook Name:: persona-common
# Recipe:: iptables
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

template "/etc/sysconfig/iptables" do
  source "etc/sysconfig/iptables.erb"
  owner "root"
  group "root"
  mode 0600
  notifies :restart, "service[iptables]", :delayed
end

service "iptables" do
  action :nothing
end
