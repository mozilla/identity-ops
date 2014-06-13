#
# Cookbook Name:: persona-common
# Recipe:: access
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

include_recipe "chef-solo-search" # https://github.com/edelight/chef-solo-search
include_recipe "users" # https://github.com/opscode-cookbooks/users

for team in node[:access][:teams][:create] do
  users_manage team do
    group_id node[:access][:teams][:gid][team]
  end

  file "/etc/sudoers.d/#{team}" do
    mode 0440
    owner "root"
    group "root"
    content "%#{team} ALL = NOPASSWD: ALL\n"
  end
end

package "emacs"
package "ngrep"
