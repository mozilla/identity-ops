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

link "/etc/localtime" do
  to "/usr/share/zoneinfo/America/Los_Angeles"
end

service "ntpd" do
  action [:enable, :start]
end

cookbook_file "/etc/sysconfig/yum-autoupdate" do
  source "etc/sysconfig/yum-autoupdate"
  owner "root"
  group "root"
  mode 0644
end

# Because "chef_gem" occurs during the compile phase (not the convergence phase)
# so that the gem can be used inside the current chef run, and because the "aws-sdk"
# gem depends on libxml2 and libxslt, I need to install those two packages during
# the compile phase, instead of the convergence phase. This is done by creating the
# resource and then calling run_action on it explicitly instead of waiting for convergence
[package("libxml2-devel"), package("libxslt-devel")].each { |pkg| pkg.run_action(:install) }
chef_gem "aws-sdk"
