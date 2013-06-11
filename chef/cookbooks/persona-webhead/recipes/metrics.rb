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

file "/opt/bid_metrics/.ssh/id_rsa" do
  content node[:persona][:webhead][:metrics][:id_rsa]
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

template "/usr/local/bin/push_bid_metrics_logs.sh" do
  source "usr/local/bin/push_bid_metrics_logs.sh.erb"
  owner "root"
  group "root"
  mode 0755
end

file "/etc/cron.d/bid_metrics-scp" do
  content "1 4 * * * bid_metrics /usr/local/bin/push_bid_metrics_logs.sh > /tmp/bid_metrics-scp.out 2>&1\n"
  owner "root"
  group "root"
  mode 0644
end

