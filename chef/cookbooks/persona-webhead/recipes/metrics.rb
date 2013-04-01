#
# Cookbook Name:: persona-webhead
# Recipe:: metrics
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

user "bid_metrics" do
  comment "browserid metrics"
  uid 900
  home "/opt/bid_metrics"
  supports "{:manage_home => true}"
end

directory "/opt/bid_metrics/.ssh" do
  owner "bid_metrics"
  group "bid_metrics"
  mode 0700
end

