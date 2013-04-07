#
# Cookbook Name:: persona-common
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::daemontools"
include_recipe "persona-common::iptables"

service "ntpd" do
  action :start
end
