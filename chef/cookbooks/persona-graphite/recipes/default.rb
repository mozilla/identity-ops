#
# Cookbook Name:: persona-graphite
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

rpm = node[:persona][:graphite][:rpms]["cloudwatch2graphite"]

remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
   source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpm}"
end

package "cloudwatch2graphite" do
  source "#{Chef::Config[:file_cache_path]}/#{rpm}"
end

template "/opt/cloudwatch2graphite/conf/graphite.json" do
  source "opt/cloudwatch2graphite/conf/graphite.json.erb"
  owner "root"
  group "root"
  mode 0644
end

file "/etc/cron.d/cloudwatch2graphite" do
  content "* * * * * root node /opt/cloudwatch2graphite/cw2graphite.js > /dev/null 2>&1\n"
  owner "root"
  group "root"
  mode 0644
  notifies :run, "execute[touch /etc/cron.d]", :delayed
end

file "/etc/cron.d/generate_cloudwatch_metrics_list" do
  content "0 * * * * root /usr/local/bin/generate_cloudwatch_metrics_list.py > /tmp/generate_cloudwatch_metrics_list.lastrun 2>&1\n"
  owner "root"
  group "root"
  mode 0644
  notifies :run, "execute[touch /etc/cron.d]", :delayed
end

execute "touch /etc/cron.d" do
  action :nothing
end

cookbook_file "/usr/local/bin/generate_cloudwatch_metrics_list.py" do
  source "usr/local/bin/generate_cloudwatch_metrics_list.py"
  owner "root"
  group "root"
  mode 0755
end

execute "/usr/local/bin/generate_cloudwatch_metrics_list.py" do
  creates "/opt/cloudwatch2graphite/conf/metrics.json"
end
