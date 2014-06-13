#
# Cookbook Name:: persona-common
# Recipe:: app
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

group "browserid" do
  gid node[:persona][:browserid_uid]
end

user "browserid" do
  comment "Browserid Application User"
  uid node[:persona][:browserid_uid]
  gid node[:persona][:browserid_uid]
  home "/opt/browserid"
  supports :manage_home => true
end

directory "/var/browserid" do
  owner "root"
  group "browserid"
  mode 0755
end

directory "/var/browserid/log" do
  owner "browserid"
  group "browserid"
  mode 0755
end
