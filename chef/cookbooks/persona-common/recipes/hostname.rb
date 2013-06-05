#
# Cookbook Name:: persona-common
# Recipe:: hostname
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#
# This is all done at compile time and not during convergence so that the 
# new node[:fqdn] is available on the first run for use. To accomplish this
# we must 1) add the fqdn to /etc/hosts 2) update the hostname with the
# hosname command 3) reload ohai
# Ohai determines the node[:fqdn] by running "hostname --fqdn" which depends
# on 1) and 2)
#
# Inspiration from
# https://github.com/opscode-cookbooks/ohai/blob/master/recipes/default.rb
#
# This also contains an ohai hint to tell ohai that we're in AWS which
# we're loading here so that the resulting ohai ec2 data is available for the entire run
# http://www.opscode.com/blog/2012/05/30/ohai-6-14-0-released/

reload_ohai=false

res = directory "/etc/chef/ohai/hints" do
        user "root"
        group "root"
        mode 0755
        recursive true
      end
res.run_action(:create)

res = file "/etc/chef/ohai/hints/ec2.json" do
        user "root"
        group "root"
        mode 0644
      end
res.run_action(:create)
reload_ohai ||= res.updated?

new_hostname="ip-#{node[:ipaddress].tr('.','-')}" + 
             (node[:tier] != nil ? ".#{node[:tier]}" : "") + 
             (node[:stack][:name] != nil ? ".#{node[:stack][:name]}" : "") +  
             (node[:stack][:type] != nil ? ".#{node[:stack][:type]}" : "") +
             (node[:aws_region] != nil ? ".#{node[:aws_region]}" : "") +
             ".allizomaws.com"

res = template "/etc/hosts" do
        source "etc/hosts.erb"
        variables(
          :hostname => new_hostname
        )
        user "root"
        group "root"
        mode 0644
      end
res.run_action(:create)
reload_ohai ||= res.updated?

res = execute "hostname #{new_hostname}" do
        not_if {node[:fqdn] == new_hostname}
      end
res.run_action(:run)
reload_ohai ||= res.updated?

if reload_ohai then
  res = ohai "reload"
  res.run_action(:reload)
end

ruby_block "inject_hostname" do
  block do
    f = Chef::Util::FileEdit.new("/etc/sysconfig/network")
    f.search_file_replace_line(/^HOSTNAME=/, "HOSTNAME=#{new_hostname}")
    f.write_file
  end
  not_if do
    open('/etc/sysconfig/network') { |f| f.lines.find { |line| line.include?("HOSTNAME=#{new_hostname}") } }
  end
end

# template "/etc/sysconfig/network" do
  # source "etc/sysconfig/network.erb"
  # variables(
    # :hostname => new_hostname
  # )
  # user "root"
  # group "root"
  # mode 0644
# end
