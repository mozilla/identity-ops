#
# Cookbook Name:: persona-rootzone
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"

package "httpd"
package "mod_ssl"

service "httpd" do
  action [:enable]
end

service "network" do
  action :nothing
end

file "/etc/resolv.conf" do
  content "nameserver 8.8.8.8"
  owner "root"
  group "root"
  mode 0644
end

node[:persona][:rootzone].each do |x|
  file "/etc/pki/tls/certs/#{x[:cert][:cert_name]}.crt" do
    content x[:cert][:cert_body]
    owner "root"
    group "root"
    mode 0644
    notifies :restart, "service[httpd]", :delayed
  end
  file "/etc/pki/tls/private/#{x[:cert][:cert_name]}.key" do
    content x[:cert][:private_key]
    owner "root"
    group "root"
    mode 0600
    notifies :restart, "service[httpd]", :delayed
  end
  file "/etc/pki/tls/certs/#{x[:cert][:cert_name]}.chain.crt" do
    content x[:cert][:cert_chain]
    owner "root"
    group "root"
    mode 0644
    notifies :restart, "service[httpd]", :delayed
  end
  if x.include? :gateway then
    ruby_block "inject_gateway" do
      block do
        f = Chef::Util::FileEdit.new("/etc/sysconfig/network")
        f.insert_line_if_no_match(/^GATEWAY=/, "GATEWAY=#{x[:gateway]}")
        f.write_file
      end
      not_if do
        open('/etc/sysconfig/network') { |f| f.lines.find { |line| line.include?("GATEWAY=#{x[:gateway]}") } }
      end
      notifies :restart, "service[network]", :delayed
    end
  end
end


file "/etc/httpd/conf.d/ssl.conf" do
  action :delete
  notifies :restart, "service[httpd]", :delayed
end

template "/etc/httpd/conf.d/rootzone.conf" do
  source "etc/httpd/conf.d/rootzone.conf.erb"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[httpd]", :delayed
end

service "httpd" do
  action [:start]
end