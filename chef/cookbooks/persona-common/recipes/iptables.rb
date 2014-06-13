#
# Cookbook Name:: persona-common
# Recipe:: iptables
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
