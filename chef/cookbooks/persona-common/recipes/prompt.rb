#
# Cookbook Name:: persona-common
# Recipe:: prompt
#
# Copyright 2013, YOUR_COMPANY_NAME
#
# All rights reserved - Do Not Redistribute
#

if node[:stack][:name] && node[:stack][:type] && node[:aws_region] then
  ruby_block "set_root_prompt" do
    nocolor='\[\e[m\]'
    if node[:stack][:type] == "prod" then
      ps_location='\[\e[1;32m\]' + node[:stack][:name] + nocolor + ":" + node[:aws_region]
    else
      ps_location='\[\e[34m\]' + node[:stack][:name] + nocolor
    end
    prompt = "[#{node[:tier]}:#{ps_location}]" + '[\u@\h \W]\$ '
    block do
      f = Chef::Util::FileEdit.new("/root/.bash_profile")
      f.insert_line_if_no_match(/^[ "\$PS1" ] && PS1=/, "[ \"$PS1\" ] && PS1=\"#{prompt}\"")
      f.write_file
    end
    not_if do
      open('/root/.bash_profile') { |f| f.lines.find { |line| line.include?("[ \"$PS1\" ] && PS1=") } }
    end
  end
end