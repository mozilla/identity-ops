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

template "/opt/cloudwatch2graphite/conf/metrics.json" do
  source "opt/cloudwatch2graphite/conf/metrics.json.erb"
  owner "root"
  group "root"
  mode 0644
end

template "/opt/cloudwatch2graphite/conf/names.json" do
  source "opt/cloudwatch2graphite/conf/names.json.erb"
  owner "root"
  group "root"
  mode 0644
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
  notifies :run, "execute[touch /etc/cron.d]", :immediately
end

execute "touch /etc/cron.d" do
  action :nothing
end
