#
# Cookbook Name:: persona-common
# Recipe:: default
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Because "chef_gem" occurs during the compile phase (not the convergence phase)
# so that the gem can be used inside the current chef run, and because the "aws-sdk"
# gem depends on libxml2 and libxslt, I need to install those two packages during
# the compile phase, instead of the convergence phase. This is done by creating the
# resource and then calling run_action on it explicitly instead of waiting for convergence
[package("libxml2-devel"), package("libxslt-devel")].each { |pkg| pkg.run_action(:install) }

include_recipe "persona-common::hostname"
include_recipe "persona-common::prompt"
include_recipe "persona-common::daemontools"
include_recipe "persona-common::iptables"
include_recipe "persona-common::access"
include_recipe "persona-common::sysctl"

link "/etc/localtime" do
  to "/usr/share/zoneinfo/America/Los_Angeles"
end

service "ntpd" do
  action [:enable, :start]
end

package "yum-plugin-security"
package "yum-autoupdate"

cookbook_file "/etc/sysconfig/yum-autoupdate" do
  source "etc/sysconfig/yum-autoupdate"
  owner "root"
  group "root"
  mode 0644
end

chef_gem "aws-sdk"
