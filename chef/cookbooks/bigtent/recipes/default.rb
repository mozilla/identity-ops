#
# Cookbook Name:: bigtent
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

rpms = ['browserid-bigtent-0.2013.01.17-10.el6_112837.x86_64.rpm',
        'browserid-certifier-0.2013.02.14-2.el6.x86_64.rpm',
        'nodejs-0.8.17-1.el6.x86_64.rpm',
        'daemontools-0.76-1moz.x86_64.rpm']

for rpm in rpms do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
    source "https://s3-us-west-2.amazonaws.com/svcops-us-west-2/identity/rpms/#{rpm}"
  end
end

directory "/opt/bigtent/config/" do
  owner "root"
  group "root"
  recursive true
end

directory "/var/browserid/certifier" do
  owner "root"
  group "root"
  recursive true
end
