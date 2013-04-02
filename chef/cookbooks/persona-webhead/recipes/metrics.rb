#
# Cookbook Name:: persona-webhead
# Recipe:: metrics
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

user "bid_metrics" do
  comment "browserid metrics"
  uid 900
  home "/opt/bid_metrics"
  supports :manage_home => true
end

for dir in ["/opt/bid_metrics/.ssh", "/opt/bid_metrics/queue"]
  directory dir do
    owner "bid_metrics"
    group "bid_metrics"
    mode 0700
  end
end

cookbook_file "/opt/bid_metrics/.ssh/authorized_keys" do
  source "opt/bid_metrics/.ssh/authorized_keys"
  owner "bid_metrics"
  group "bid_metrics"
  mode 0600
end

cookbook_file "/etc/logrotate.d/bid_metrics" do
  source "etc/logrotate.d/bid_metrics"
  owner "root"
  group "root"
  mode 0644
end

# This is so we use cron instead of anacron. 
# This results in a fixed run time and no makeups if the machine was off at the time.
file "/etc/cron.daily/logrotate" do
  action :delete
end

cookbook_file "/usr/local/bin/logrotate.cron" do
  source "usr/local/bin/logrotate.cron"
  owner "root"
  group "root"
  mode 0644
end

file "/etc/cron.d/logrotate" do
  content "0 3 * * * root /usr/local/bin/logrotate.cron"
  owner "root"
  group "root"
  mode 0644
end
