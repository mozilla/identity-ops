cookbook_file "/etc/yum.repos.d/opsview.repo" do
  source "etc/yum.repos.d/opsview.repo"
  mode 0644
  backup false
end 

package "libmcrypt"
package "opsview-agent"
service "opsview-agent" do
  action :nothing
end

opsview_client "#{node[:stack][:environment]} Stack #{node[:stack][:name]}" do
  # We can change this to some other form of localized discovery later (e.g. DNS, chef-server environments, etc)
  if node[:opsview_client][:server_url].is_a? Hash and node.include? :aws_region then
    server_url node[:opsview_client][:server_url][node[:aws_region]]
  else
    server_url node[:opsview_client][:server_url]
  end
  username node[:opsview_client][:username]
  password node[:opsview_client][:password]
  host_templates node[:opsview_client][:host_templates]
  host_attributes node[:opsview_client][:host_attributes]
end

["logwarn-1.0.10-1.x86_64.rpm", "logwarn-nagios-plugin-1.0.10-1.noarch.rpm"].each do |rpm|
  remote_file "#{Chef::Config[:file_cache_path]}/#{rpm}" do
    source "https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/#{rpm}"
  end
end
package "logwarn" do
  source "#{Chef::Config[:file_cache_path]}/logwarn-1.0.10-1.x86_64.rpm"
end

package "logwarn-nagios-plugin" do
  source "#{Chef::Config[:file_cache_path]}/logwarn-nagios-plugin-1.0.10-1.noarch.rpm"
end
