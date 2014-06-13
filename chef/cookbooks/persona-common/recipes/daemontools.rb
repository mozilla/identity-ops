#
# Cookbook Name:: persona-common
# Recipe:: daemontools
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

node.normal["daemontools"]["service_dir"] = "/service"
node.normal["daemontools"]["install_method"] = 'package'

cookbook_file "/etc/yum.repos.d/djbware.repo" do
  source "etc/yum.repos.d/djbware.repo"
  mode 0644
  backup false
end  

directory node.normal[:daemontools][:service_dir]

directory "/var/services"

include_recipe "daemontools::default"

execute "initctl reload-configuration" do
  action :nothing
end

execute "initctl start svscan" do
  action :nothing
end

cookbook_file "/etc/init/svscan.conf" do
  source "etc/init/svscan.conf"
  mode 0644
  backup false
  notifies :run, 'execute[initctl reload-configuration]', :immediately
  notifies :run, 'execute[initctl start svscan]', :immediately
end