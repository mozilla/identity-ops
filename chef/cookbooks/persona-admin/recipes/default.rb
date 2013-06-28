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

