#
# Cookbook Name:: persona-common
# Recipe:: postfix
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

package "postmap"
service "postmap" do
  action [:enable, :start]
end

execute "/usr/sbin/postmap /etc/postfix/sasl_passwd" do
  action :nothing
end

execute "/usr/sbin/postmap /etc/postfix/transport" do
  action :nothing
end

if node[:persona][:postfix][:smtp_host] then
  file "/etc/postfix/sasl_passwd" do
    owner "root"
    group "root"
    mode 0600
    content "#{node[:persona][:postfix][:smtp_host]} #{node[:persona][:postfix][:smtp_user]}:#{node[:persona][:postfix][:smtp_password]}\n"
    notifies :run, 'execute[/usr/sbin/postmap /etc/postfix/sasl_passwd]', :immediately
    notifies :restart, 'service[postfix]', :delayed
  end

  file "/etc/postfix/transport" do
    owner "root"
    group "root"
    mode 0600
    content "loadtest.domain error:loadtest mail is disabled\n"
    notifies :run, 'execute[/usr/sbin/postmap /etc/postfix/transport]', :immediately
    notifies :restart, 'service[postfix]', :delayed
  end
end

temlpate "/etc/postfix/main.cf" do
  source "etc/postfix/main.cf.erb"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, 'service[postfix]', :delayed
end
