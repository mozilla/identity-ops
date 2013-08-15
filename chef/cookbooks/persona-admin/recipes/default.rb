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

# Install the Rackspace IUS repo to get python 2.7
remote_file "#{Chef::Config[:file_cache_path]}/ius-release-1.0-11.ius.centos6.noarch.rpm" do
  source "http://dl.iuscommunity.org/pub/ius/stable/CentOS/6/x86_64/ius-release-1.0-11.ius.centos6.noarch.rpm"
end
package "ius-release" do
  source "#{Chef::Config[:file_cache_path]}/ius-release-1.0-11.ius.centos6.noarch.rpm"
end

package "pssh"
package "mosh"

package "python27"
package "python27-distribute"

for pkg in ["boto", "dnspython"] do
  easy_install_package pkg do
    easy_install_binary "/usr/bin/easy_install-2.7"
    python_binary "/usr/bin/python2.7"
  end
end

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

