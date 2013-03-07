#
# Cookbook Name:: bigtent
# Recipe:: daemontools
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

node.normal[:daemontools][:service_dir] = "/service"

cookbook_file "/etc/yum.repos.d/djbware.repo" do
  source "etc/yum.repos.d/djware.repo"
  backup false
end  

include_recipe "daemontools::default"

daemontools_service "browserid-certifier" do
  directory "/service/browserid-certifier"
  action [:enable]
end

daemontools_service "browserid-bigtent" do
  directory "/service/browserid-bigtent"
  action [:enable]
end
