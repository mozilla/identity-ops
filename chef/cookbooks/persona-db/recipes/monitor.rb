#
# Cookbook Name:: persona-db
# Recipe:: monitor
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

for file in ["usr/local/nagios/libexec/check_mysql_innodb",
             "usr/local/nagios/libexec/check_mysql_percona_heartbeat"]
  cookbook_file "/#{file}" do
    source file
    owner "root"
    group "root"
    mode 0755
  end
end

cookbook_file "/usr/local/nagios/etc/nrpe_local/override.cfg" do
  source "usr/local/nagios/etc/nrpe_local/override.cfg"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[opsview-agent]", :delayed
end
