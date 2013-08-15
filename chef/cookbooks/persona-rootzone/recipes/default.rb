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


rpms = {"apr" => "apr-1.4.6-1.x86_64.rpm",
        "apr-util" => "apr-util-1.5.2-1.x86_64.rpm",
        "apr-util-ldap" => "apr-util-ldap-1.5.2-1.x86_64.rpm",
        "httpd" => "httpd-2.4.4-1.x86_64.rpm",
        "httpd-tools" => "httpd-tools-2.4.4-1.x86_64.rpm",
        "mod_ssl" => "mod_ssl-2.4.4-1.x86_64.rpm"}

# TODO : This doesn't work for apr-util-ldap and apr-util because of circular dependencies
# TODO : This doesn't work for httpd, mod_ssl, and httpd-tools because of circular dependencies

for rpm in rpms.keys do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpms[rpm]}" do
    source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpms[rpm]}"
  end
  package rpm do
    source "#{Chef::Config[:file_cache_path]}/#{rpms[rpm]}"
  end
end

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
  file "/etc/sysconfig/network-scripts/ifcfg-#{x[:interface]}" do
    content "DEVICE=#{x[:interface]}\nBOOTPROTO=static\nIPADDR=#{x[:ip][node[:aws_region]]}\nNETMASK=255.255.255.0\n"
    owner "root"
    group "root"
    mode 0644
    notifies :restart, "service[network]", :delayed
  end
  if x.include? :gateway then
    ruby_block "inject_gateway" do
      block do
        f = Chef::Util::FileEdit.new("/etc/sysconfig/network")
        f.insert_line_if_no_match(/^GATEWAY=/, "GATEWAY=#{x[:gateway][node[:aws_region]]}")
        f.write_file
      end
      not_if do
        open('/etc/sysconfig/network') { |f| f.lines.find { |line| line.include?("GATEWAY=#{x[:gateway][node[:aws_region]]}") } }
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

cookbook_file "/etc/httpd/conf/httpd.conf" do
  source "etc/httpd/conf/httpd.conf"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[httpd]", :delayed
end

service "httpd" do
  action [:start]
end