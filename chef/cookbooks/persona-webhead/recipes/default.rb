#
# Cookbook Name:: persona-webhead
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"
include_recipe "persona-common::daemontools"

rpms = [node[:persona][:webhead][:rpms]["browserid-server"],
        node[:persona][:webhead][:rpms][:nodejs]]

for rpm in rpms do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
    source "https://s3-us-west-2.amazonaws.com/svcops-us-west-2/identity/rpms/#{rpm}"
  end
end

package "nodejs" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:webhead][:rpms][:nodejs]}"
end

package "browserid-server" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:webhead][:rpms]["browserid-server"]}"
end

template "/opt/browserid/config/production.json" do

end

template "/opt/browserid/config/webhead.json" do
end

template "/opt/browserid/config/webhead.json" do
end