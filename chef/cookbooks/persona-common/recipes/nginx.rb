#
# Cookbook Name:: persona-common
# Recipe:: nginx
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

group "nginx" do
  gid node[:persona][:nginx_uid]
end

user "nginx" do
  comment "Nginx User"
  uid node[:persona][:nginx_uid]
  gid node[:persona][:nginx_uid]
  home "/var/lib/nginx"
  shell "/bin/false"
end

package "nginx"

daemontools_service "nginx" do
  directory "/var/services/nginx"
  template "nginx"
  action [:enable, :start]
  log true
end

for filename in ["/etc/nginx/conf.d/default.conf",
                 "/etc/nginx/conf.d/ssl.conf",
                 "/etc/nginx/conf.d/virtual.conf"] do
  file filename do
    content ""
    owner "root"
    group "root"
    mode 0644
    notifies :restart, "daemontools_service[nginx]", :delayed
  end
end

cookbook_file "/etc/nginx/nginx.conf" do
  source "etc/nginx/nginx.conf"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "daemontools_service[nginx]", :delayed
end

