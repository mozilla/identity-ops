#
# Cookbook Name:: persona-common
# Recipe:: sysctl
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# manage the whole file to configure net.ipv4.ip_local_port_range
cookbook_file '/etc/sysctl.conf' do
  source 'etc/sysctl.conf'
  owner 'root'
  group 'root'
  mode 0644
end

# make sure the change to ip_local_port_range is live
bash 'ip_local_port_range' do
  user 'root'
  code 'echo "1024 65535" > /proc/sys/net/ipv4/ip_local_port_range'
  not_if 'cat /proc/sys/net/ipv4/ip_local_port_range | grep -qx "1024\s65535"'
end
