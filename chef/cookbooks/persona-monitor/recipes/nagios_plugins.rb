#
# Cookbook Name:: persona-monitor
# Recipe:: nagios_plugins
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

# Install the Rackspace IUS repo to get python 2.7
remote_file "#{Chef::Config[:file_cache_path]}/ius-release-1.0-11.ius.centos6.noarch.rpm" do
  source "http://dl.iuscommunity.org/pub/ius/stable/CentOS/6/x86_64/ius-release-1.0-11.ius.centos6.noarch.rpm"
end
package "ius-release" do
  source "#{Chef::Config[:file_cache_path]}/ius-release-1.0-11.ius.centos6.noarch.rpm"
end

package "python27"
package "python27-distribute"

easy_install_package "boto" do
  easy_install_binary "/usr/bin/easy_install-2.7"
  python_binary "/usr/bin/python2.7"
end

for nagios_plugin in ["check_http_hash",
                      "check_dynect_gslb_region",
                      "check_instance_elb_membership"] do
  cookbook_file "/usr/local/nagios/libexec/#{nagios_plugin}" do
    source "usr/local/nagios/libexec/#{nagios_plugin}"
    mode 0755
    owner "root"
    group "root"
    backup false
  end 
end

# Used by check_dynect_gslb_region
package "ruby-devel" # required by gem_package "dynect_rest"
gem_package "dynect_rest"
gem_package "trollop"
template "/etc/dynect-credentials.json" do
  source "etc/dynect-credentials.json.erb"
  mode 0640
  owner "root"
  group "nagios"
  backup false
end 

# Used by check_http_hash
cookbook_file "/etc/allowed-hashes.txt" do
  source "etc/allowed-hashes.txt"
  mode 0644
  owner "root"
  group "root"
  backup false
end 

for nagios_notification_plugin in ["pagerduty_nagios.pl",
                                   "submit_notify_by_nma_script"] do
  cookbook_file "/usr/local/nagios/libexec/notifications/#{nagios_notification_plugin}" do
    source "usr/local/nagios/libexec/notifications/#{nagios_notification_plugin}"
    mode 0755
    owner "root"
    group "root"
    backup false
  end 
end

cookbook_file "/usr/local/nagios/libexec/notifications/org.persona.notificationmethods.email.tt" do
  source "usr/local/nagios/libexec/notifications/org.persona.notificationmethods.email.tt"
  mode 0644
  owner "root"
  group "root"
  backup false
end 

for nagios_tools in ["notify_by_nma.pl"] do
  cookbook_file "/usr/local/bin/#{nagios_tools}" do
    source "usr/local/bin/#{nagios_tools}"
    mode 0755
    owner "root"
    group "root"
    backup false
  end 
end