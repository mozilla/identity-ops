#
# Cookbook Name:: persona-metrics
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "persona-common::default"

user "bid_metrics" do
  comment "browserid metrics"
  uid 900
  home "/opt/bid_metrics"
  supports :manage_home => true
end

for dir in [".ssh", 
            "queue",
            "bin",
            "incoming",
            "etl",
            "etl/input",
            "etl/output",
            "etl/config",
            "etl/etl",
            "tmp"]
  directory "/opt/bid_metrics/" + dir do
    owner "bid_metrics"
    group "bid_metrics"
    mode 0700
  end
end

file "/opt/bid_metrics/.ssh/authorized_keys" do
  # This is the keypair enabling webheads to ssh to persona-metrics
  content "no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty #{node[:persona][:metrics][:authorized_keys]}"
  owner "bid_metrics"
  group "bid_metrics"
  mode 0600
end

file "/opt/bid_metrics/.ssh/id_rsa" do
  # This is the keypair enabling persona-metrics to ssh to metrics-logger1.private.scl3.mozilla.com
  content node[:persona][:metrics][:id_rsa]
  owner "bid_metrics"
  group "bid_metrics"
  mode 0600
end

file "/opt/bid_metrics/.ssh/known_hosts" do
  content "10.22.75.50 ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAm2r7bw+6bkpmNECqMiOgvR3rV3blfkWLiqZQ+oMe7WxSunvRQIzTqsfrQnozHeZlO8Zn5qpqzEwx5IGICmfpR5SiGSqcS9cXJhbYzbeV4gjD8Paxrv2Ej37IM590En1Hz4VInM/MhXm9prdSgjtiT3NDu1qGkg6YsflNXsydrXfpWiz/rKFdJpWkQ5nqapfq5vOuZHEediIB5gbzbXEWFh6k/apqJvUQBMxYy460Z+zK3FHKpB5d9dhEbIvr/8tObam1zOdit3vv/BcTIi/sZkt0SDuKcoL4xzkSEneIv4OadHQtSo3fVqo//3K5pIxmMbKYpkUHuZ51Bf48wD4MNw=="
  owner "bid_metrics"
  group "bid_metrics"
  mode 0644
end

# Install kettle
remote_file "#{Chef::Config[:file_cache_path]}/pdi-ce-4.4.0-stable.tar.gz" do
   source "http://downloads.sourceforge.net/project/pentaho/Data%20Integration/4.4.0-stable/pdi-ce-4.4.0-stable.tar.gz"
   checksum "acb4040492b2fec82a67c6694bc500929cea3bdb5a54a898bf1892385fcc77ad"
   notifies :run, "bash[install_kettle]", :immediately
end

bash "install_kettle" do
  user "root"
  cwd "/opt/bid_metrics/etl"
  code "tar -zxf #{Chef::Config[:file_cache_path]}/pdi-ce-4.4.0-stable.tar.gz && mv data-integration kettle"
  action :nothing
end

# Install GeoIPCity.dat
s3_file "/opt/bid_metrics/etl/GeoIPCity.dat.gz" do
  # This resource gets no key or secret and instead uses temporary
  # credentials from it's IAM Role, "identity", which grants read
  # permissions on the "mozilla-identity-us-standard" bucket
  source "s3://mozilla-identity-us-standard/assets/GeoIPCity.dat.gz"
  #access_key_id "key"
  #secret_access_key "secret"
  owner "bid_metrics"
  group "bid_metrics"
  mode 0600
  checksum "3e4abecbd18edb8acb0a4ee9d1ff74b4ac8f48c2cc616c3ad210ad626b3cf502"
  notifies :run, "execute[gunzip GeoIPCity.dat.gz > GeoIPCity.dat]", :immediately
end

execute "gunzip GeoIPCity.dat.gz > GeoIPCity.dat" do
  user "bid_metrics"
  cwd "/opt/bid_metrics/etl"
  creates "/opt/bid_metrics/etl/GeoIPCity.dat"
  action :nothing
end

directory "/usr/local/share/GeoIP" do
  owner "root"
  group "root"
  0755
end

link "/usr/local/share/GeoIP/GeoIPCity.dat" do
  to "/opt/bid_metrics/etl/GeoIPCity.dat"
end

# Configure kettle
for file in ["opt/bid_metrics/etl/config/config.properties", 
             "opt/bid_metrics/etl/etl/main.kjb", 
             "opt/bid_metrics/etl/etl/regexp_others.properties", 
             "opt/bid_metrics/etl/etl/tables.xls", 
             "opt/bid_metrics/etl/etl/t_archiveFiles.ktr", 
             "opt/bid_metrics/etl/etl/t_parseFiles.ktr", 
             "opt/bid_metrics/etl/etl/t_processUserAgentString.ktr", 
             "opt/bid_metrics/etl/etl/t_readProperties.ktr", 
             "opt/bid_metrics/etl/etl/t_setDate.ktr", 
             "opt/bid_metrics/etl/etl/t_setRegexp.ktr", 
             "opt/bid_metrics/etl/etl/t_setToday.ktr"
             ]
  cookbook_file "/#{file}" do
    source "#{file}"
    owner "bid_metrics"
    group "bid_metrics"
    mode 0644
  end
end

cookbook_file "/opt/bid_metrics/etl/run.sh" do
  source "opt/bid_metrics/etl/run.sh"
  owner "bid_metrics"
  group "bid_metrics"
  mode 0755
end

cookbook_file "/etc/cron.d/process_metrics" do
  source "etc/cron.d/process_metrics"
  owner "root"
  group "root"
  mode 0644
end

cookbook_file "/opt/bid_metrics/bin/process_metrics.sh" do
  source "opt/bid_metrics/bin/process_metrics.sh"
  owner "bid_metrics"
  group "bid_metrics"
  mode 0755
end