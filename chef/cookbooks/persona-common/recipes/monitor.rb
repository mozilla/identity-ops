if node.include? :opsview_client then
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
    server_url node[:opsview_client][:server_url].is_a? Hash and node.include? :aws_region ? 
      node[:opsview_client][:server_url][node[:aws_region]] :
      node[:opsview_client][:server_url]
    username node[:opsview_client][:username]
    password node[:opsview_client][:password]
    host_templates node[:opsview_client][:host_templates]
    host_attributes node[:opsview_client][:host_attributes]
  end
end