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


rpm_names = ["persona-manage_s3_secrets",
             "python-stack_control"]

for rpm_name in rpm_names do
  remote_file "#{Chef::Config[:file_cache_path]}/#{node[:persona][:builder][:rpms][rpm_name]}" do
     source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{node[:persona][:builder][:rpms][rpm_name]}"
  end
  
  package rpm_name do
    source "#{Chef::Config[:file_cache_path]}/#{node[:persona][:builder][:rpms][rpm_name]}"
  end
end
