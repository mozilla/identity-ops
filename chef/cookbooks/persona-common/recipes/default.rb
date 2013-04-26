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
  action :start
end

package "libxml2-devel"
package "libxslt-devel"
chef_gem "aws-sdk"
