#
# Cookbook Name:: bigtent
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

default[:bigtent][:client_session_secret] = "Rrop8eT9clHDkJUBPJnpQta6iWxkPCRC"
default[:bigtent][:browserid_server] = "https://login.anosrep.org"
default[:bigtent][:issuer] = "yahoo.login.anosrep.org"
# Note these is an example key pair that will be overwritten by your actual keypair
default[:bigtent][:secretkey] = '"{\\"algorithm\\":\\"DS\\",\\"y\\":\\"cd33fd7f3c3a26754e5c1d992b0cfa82609588723cc2628bc63d9bef540a67b50efc03451dc3e6b3aa47e74df52d0d089908fa13c923171775df670d4c6f54ecaeb2dc69ee83c6afa6b7c08c19b68cc75e7b61e2d81291bac1d9f0003603cfe1dc211f6c45f0797a0470e59857a15242b99a4bd915ea089d1705f2eb9ed524cb3dbe2035bf9153f77ba2ec4d05c4b262ff7ab50ca81659d63e4d69b5f7f52215a08a62fa2cf44ab46b362da7d526114f9b087371dccbbb0d7e726236ad33e3565ce664cfe8b6f2b3e18e52318b532fa693fdf0a5885f5419570994ebfa4dab85445b6c14e31ffafa1e1762c4cb9395930ff3dfc84a0f33f9efc406fc87d552aa\\",\\"p\\":\\"d6c4e5045697756c7a312d02c2289c25d40f9954261f7b5876214b6df109c738b76226b199bb7e33f8fc7ac1dcc316e1e7c78973951bfc6ff2e00cc987cd76fcfb0b8c0096b0b460fffac960ca4136c28f4bfb580de47cf7e7934c3985e3b3d943b77f06ef2af3ac3494fc3c6fc49810a63853862a02bb1c824a01b7fc688e4028527a58ad58c9d512922660db5d505bc263af293bc93bcd6d885a157579d7f52952236dd9d06a4fc3bc2247d21f1a70f5848eb0176513537c983f5a36737f01f82b44546e8e7f0fabc457e3de1d9c5dba96965b10a2a0580b0ad0f88179e10066107fb74314a07e6745863bc797b7002ebec0b000a98eb697414709ac17b401\\",\\"q\\":\\"b1e370f6472c8754ccd75e99666ec8ef1fd748b748bbbc08503d82ce8055ab3b\\",\\"g\\":\\"9a8269ab2e3b733a5242179d8f8ddb17ff93297d9eab00376db211a22b19c854dfa80166df2132cbc51fb224b0904abb22da2c7b7850f782124cb575b116f41ea7c4fc75b1d77525204cd7c23a15999004c23cdeb72359ee74e886a1dde7855ae05fe847447d0a68059002c3819a75dc7dcbb30e39efac36e07e2c404b7ca98b263b25fa314ba93c0625718bd489cea6d04ba4b0b7f156eeb4c56c44b50e4fb5bce9d7ae0d55b379225feb0214a04bed72f33e0664d290e7c840df3e2abb5e48189fa4e90646f1867db289c6560476799f7be8420a6dc01d078de437f280fff2d7ddf1248d56e1a54b933a41629d6c252983c58795105802d30d7bcd819cf6ef\\"}"'
default[:bigtent][:publickey] = '"{\\"algorithm\\":\\"DS\\",\\"x\\":\\"a763837db70d317f1f027a6c5271fa1b658d0bf020bdf199e66a4070353164c1\\",\\"p\\":\\"d6c4e5045697756c7a312d02c2289c25d40f9954261f7b5876214b6df109c738b76226b199bb7e33f8fc7ac1dcc316e1e7c78973951bfc6ff2e00cc987cd76fcfb0b8c0096b0b460fffac960ca4136c28f4bfb580de47cf7e7934c3985e3b3d943b77f06ef2af3ac3494fc3c6fc49810a63853862a02bb1c824a01b7fc688e4028527a58ad58c9d512922660db5d505bc263af293bc93bcd6d885a157579d7f52952236dd9d06a4fc3bc2247d21f1a70f5848eb0176513537c983f5a36737f01f82b44546e8e7f0fabc457e3de1d9c5dba96965b10a2a0580b0ad0f88179e10066107fb74314a07e6745863bc797b7002ebec0b000a98eb697414709ac17b401\\",\\"q\\":\\"b1e370f6472c8754ccd75e99666ec8ef1fd748b748bbbc08503d82ce8055ab3b\\",\\"g\\":\\"9a8269ab2e3b733a5242179d8f8ddb17ff93297d9eab00376db211a22b19c854dfa80166df2132cbc51fb224b0904abb22da2c7b7850f782124cb575b116f41ea7c4fc75b1d77525204cd7c23a15999004c23cdeb72359ee74e886a1dde7855ae05fe847447d0a68059002c3819a75dc7dcbb30e39efac36e07e2c404b7ca98b263b25fa314ba93c0625718bd489cea6d04ba4b0b7f156eeb4c56c44b50e4fb5bce9d7ae0d55b379225feb0214a04bed72f33e0664d290e7c840df3e2abb5e48189fa4e90646f1867db289c6560476799f7be8420a6dc01d078de437f280fff2d7ddf1248d56e1a54b933a41629d6c252983c58795105802d30d7bcd819cf6ef\\"}"'
default[:proxy][:host] = "proxy.example.com"
default[:proxy][:port] = 3128

default[:bigtent][:rpms][:bigtent] = 'browserid-bigtent-0.2013.01.17-10.el6_112837.x86_64.rpm'
default[:bigtent][:rpms][:certifier] = 'browserid-certifier-0.2013.02.14-2.el6.x86_64.rpm'
default[:bigtent][:rpms][:nodejs] = 'browserid-certifier-0.2013.02.14-2.el6.x86_64.rpm'

rpms = [node[:bigtent][:rpms][:bigtent],
        node[:bigtent][:rpms][:certifier],
        node[:bigtent][:rpms][:nodejs]]

for rpm in rpms do
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
    source "https://s3-us-west-2.amazonaws.com/svcops-us-west-2/identity/rpms/#{rpm}"
  end
end

group "browserid" do
  gid 450
end

user "browserid" do
  comment "Browserid Application User"
  uid 450
  gid 450
  home "/opt/browserid"
end

for dir in ["/var/browserid/certifier",
            "/var/browserid/log",
            ] do
  directory dir do
    owner "browserid"
    group "browserid"
    recursive true
  end
end

package "browserid-nodejs" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:bigtent][:rpms][:nodejs]}"
end

package "browserid-certifier" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:bigtent][:rpms][:certifier]}"
end

package "browserid-bigtent" do
  source "#{Chef::Config[:file_cache_path]}/#{node[:bigtent][:rpms][:bigtent]}"
end

template "/opt/bigtent/config/production.json" do
  source "opt/bigtent/config/production.json.erb"
  owner root
  group root
  mode 0644
end

template "/opt/certifier/config/production.json" do
  source "opt/certifier/config/production.json.erb"
  owner root
  group root
  mode 0644
end

file "/var/browserid/certifier/key.publickey" do
  owner root
  group root
  mode 0644
  content node[:bigtent][:publickey]
end

file "/var/browserid/certifier/key.secretkey" do
  owner root
  group root
  mode 0644
  content node[:bigtent][:secretkey]
end

include_recipe "bigtent::daemontools"

service "browserid-certifier" do
  action :start
end

service "browserid-bigent" do
  action :start
end
