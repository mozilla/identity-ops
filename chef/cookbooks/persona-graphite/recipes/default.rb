#
# Cookbook Name:: persona-graphite
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

remote_file "#{Chef::Config[:file_cache_path]}/cloudwatch2graphite-1-1.x86_64.rpm" do
   source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/cloudwatch2graphite-1-1.x86_64.rpm"
end

package "cloudwatch2graphite-1-1.x86_64.rpm" do
  source "#{Chef::Config[:file_cache_path]}/cloudwatch2graphite-1-1.x86_64.rpm"
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
  content "* * * * * root node /opt/cloudwatch2graphite/cw2graphite.js > /dev/null 2>&1"
  owner "root"
  group "root"
  mode 0644
end
