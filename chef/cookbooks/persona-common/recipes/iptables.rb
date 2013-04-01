#
# Cookbook Name:: persona-common
# Recipe:: iptables
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

cookbook_file "/etc/sysconfig/iptables" do
  source "etc/sysconfig/iptables"
  owner "root"
  group "root"
  mode 0600
end