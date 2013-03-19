#
# Cookbook Name:: access
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

directory "/root/.ssh" do
  owner "root"
  group "root"
  mode 0700
end

cookbook_file "/root/.ssh/authorized_keys" do
  source "root/.ssh/authorized_keys"
  owner "root"
  group "root"
  mode 0600
end
