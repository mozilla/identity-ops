#
# Cookbook Name:: persona-webhead
# Recipe:: logrotate
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is so we use cron instead of anacron.
# This results in a fixed run time and no makeups if the machine was off at the time.
file "/etc/cron.daily/logrotate" do
  action :delete
end

cookbook_file "/usr/local/bin/logrotate.cron" do
  source "usr/local/bin/logrotate.cron"
  owner "root"
  group "root"
  mode 0755
end

file "/etc/cron.d/logrotate" do
  content "0 3 * * * root /usr/local/bin/logrotate.cron > /tmp/logrotate.output 2>&1\n"
  owner "root"
  group "root"
  mode 0644
  notifies :run, "execute[touch /etc/cron.d]", :immediately
end

execute "touch /etc/cron.d" do
  action :nothing
end

cookbook_file "/etc/logrotate.d/persona" do
  source "etc/logrotate.d/persona"
  owner "root"
  group "root"
  mode 0644
end
