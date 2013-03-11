#
# Cookbook Name:: bigtent
# Recipe:: nginx
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

group "nginx" do
  gid 452
end

user "nginx" do
  comment "Nginx User"
  uid 452
  gid 452
  home "/var/lib/nginx"
  shell "/bin/false"
end

package "nginx"

cookbook_file "/etc/nginx/nginx.conf" do
  source "etc/nginx/nginx.conf"
  owner "root"
  group "root"
  mode 0644
end

cookbook_file "/etc/nginx/conf.d/idbigtent.conf" do
  source "etc/nginx/conf.d/idbigtent.conf"
  owner "root"
  group "root"
  mode 0644
end

daemontools_service "nginx" do
  directory "/var/services/nginx"
  template "nginx"
  action [:enable, :start]
end