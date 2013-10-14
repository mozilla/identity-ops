#
# Cookbook Name:: persona-rootzone
# Recipe:: splash
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

directory "/opt/splash" do
  owner "root"
  group "root"
  mode 0755
end

# Could fetch the zip : https://github.com/mozilla/persona.org/archive/prod.zip
execute "git clone https://github.com/mozilla/persona.org --branch prod --depth=1 /opt/splash" do
  not_if { ::File.exists?("/opt/splash/.git")}
end

execute "git pull https://github.com/mozilla/persona.org prod" do
  cwd "/opt/splash"
  not_if %q#git --git-dir=/opt/splash/.git fetch -v --dry-run 2>&1 | awk '$NF == "origin/prod" {print $0}' | grep 'up to date'#
end