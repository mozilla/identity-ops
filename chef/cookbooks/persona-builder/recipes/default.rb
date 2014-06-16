#
# Cookbook Name:: persona-builder
# Recipe:: default
#
# Copyright 2014, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"

package "python-psutil"
package "python-gnupg"
package "python-boto"


rpm = node[:persona][:builder][:rpms]["persona-manage_s3_secrets"]

remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
   source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpm}"
end

package "python-manage_s3_secrets" do
  source "#{Chef::Config[:file_cache_path]}/#{rpm}"
end


rpm = node[:persona][:builder][:rpms]["python-stack_control"]

remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
   source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpm}"
end

package "python-stack_control" do
  source "#{Chef::Config[:file_cache_path]}/#{rpm}"
end
