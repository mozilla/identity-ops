#
# Cookbook Name:: bigtent
# Recipe:: daemontools
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

node.normal[:daemontools][:service_dir] = "/service"
node.normal[:daemontools][:install_method] = 'package'

cookbook_file "/etc/yum.repos.d/djbware.repo" do
  source "etc/yum.repos.d/djbware.repo"
  backup false
end  

directory node.normal[:daemontools][:service_dir]

directory "/var/services"

include_recipe "daemontools::default"

daemontools_service "browserid-certifier" do
  directory "/var/services/browserid-certifier"
  action [:enable]
end

daemontools_service "browserid-bigtent" do
  directory "/var/services/browserid-bigtent"
  action [:enable]
end
