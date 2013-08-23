#
# Cookbook Name:: access
# Recipe:: default
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

include_recipe "chef-solo-search" # https://github.com/edelight/chef-solo-search
include_recipe "users" # https://github.com/opscode-cookbooks/users

for team in node[:access][:teams][:create] do
  users_manage team do
    group_id node[:access][:teams][:gid][team]
  end

  file "/etc/sudoers.d/#{team}" do
    mode 0660
    owner "root"
    group "root"
    content "%#{team} ALL = NOPASSWD: ALL"
  end
end

directory "/root/.ssh" do
  owner "root"
  group "root"
  mode 0700
end

cookbook_file "/root/.ssh/authorized_keys" do
  source "root/.ssh/authorized_keys"
  owner "root"
  group "root"
  mode 0600
end

package "emacs"
package "ngrep"

