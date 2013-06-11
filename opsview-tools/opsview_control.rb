#!/usr/bin/ruby
#
# This will import or export your opsview settings
#

require 'rubygems'
require 'rest_client'
require 'json'
require 'logger'
require 'json'
require 'trollop'

class OpsviewManager
  def initialize(opts)
    @url, @username, @password, @dryrun = opts[:url], opts[:username], opts[:password], opts[:dryrun]
    @token_header = get_token
    @logger = Logger.new(STDOUT)
    begin
      @logger.level = Logger.const_get(opts[:loglevel])
    rescue NameError
      raise "Log level #{opts[:loglevel]} is not allowed"
    end
  end

  def get_token
    begin
      response = RestClient.post [@url, 'login'].join('/'),
        {'username' => @username, 'password' => @password}.to_json,
        :content_type => :json,
        :accept => :json
    rescue => e
      raise "Could not reach opsview at #{@url}. #{e}."
    end
    {:x_opsview_username => @username,
     :x_opsview_token => JSON.parse(response.body)['token'],
     :content_type => :json,
     :accept => :json}
  end

  def reload
    if not @dryrun then
      begin
        response = RestClient.post [@url, 'reload'].join('/'),
          '',
          @token_header
      rescue => e
        case e.http_code
        when 409
          @logger.info("Opsview reload already running")
        else
          raise "Failed to reload Opsview. #{e}."
        end
      else
        @logger.info("Opsview config reloaded")
      end
    end
  end

  def export_section(section, filter=nil, strip_keys=[])
    begin
      filter_hash = filter ? {:params => {:json_filter => filter.to_json}} : {}
      response = RestClient.get [@url, 'config', section].join('/'),
        @token_header.merge(filter_hash)
    rescue => e
      raise "Could not reach opsview at #{server_url}. #{e}. #{e.http_body}"
    end  
    # TODO : Check if 'list' is longer than 50 indicating pagination
    data = JSON.parse(response)
    data.delete('summary')
    strip_keys.each do |x|
      data['list'].each do |y|
        y.delete x
      end
    end
    data
  end

  def import_from_file(section, filename)
    # We'll assume that we're importing into a stock opsview installation
  
    payload = JSON.parse(File.read(filename))
    
    begin
      response = RestClient.get [@url, 'config', section].join('/'),
        @token_header
    rescue => e
      raise "Could not reach opsview at #{server_url}. #{e}. #{e.http_body}"
    end
    existing_objects = JSON.parse(response)['list']
    ids = existing_objects.map {|x| x['id']}.compact
    payload['list'].select {|x| ids.include? x['id']}.each {|y|
      @logger.info("Skipping import of #{section}:#{y['name']} because it already exists")
    }
    payload['list'].delete_if {|x| ids.include? x['id']}
  
    @logger.info("About to import #{section}:#{payload['list'].map {|x| [x['id'], x['name']]}.compact.to_json}")
    @logger.info("Beginning import of #{section}")
  
    if not @dryrun then
      begin
        response = RestClient.put [@url, 'config', section].join('/'),
          payload.to_json,
          @token_header
      rescue => e
        raise "Could not reach opsview at #{@url}. #{e}. #{e.http_body}"
      end
      @logger.info("Import of #{section} complete")
    end
  end

  def get_section_export_details(section)
    case section
    when 'attribute'
      filter = nil
      strip_keys = ["servicechecks"]
    when 'role'
      filter = {"-and" => 
                 [
                   {"name" => 
                     {
                       "-like" => "%Opsview Client%"
                     }
                   }
                 ]
               }
      strip_keys = ["contacts"]
    when 'contact'
      filter = {"-and" => 
                 [
                   {"name" => 
                     {
                       "-like" => "%opsviewclient%"
                     }
                   }
                 ]
               }
      strip_keys = []
    when 'servicegroup'
      filter = {"-and" => 
                 [
                   {"name" => 
                     {
                       "-like" => "%Identity%"
                     }
                   }
                 ]
               }
      strip_keys = ["servicechecks"]
    when 'servicecheck'
      filter = {"-and" => 
                 [
                   {"description" => 
                     {
                       "-like" => "%(mozilla)%"
                     }
                   }
                 ]
               }
      strip_keys = ["hosttemplates", "hosts"]
    when 'hosttemplate'
      filter = {"-and" => 
                 [
                   {"description" => 
                     {
                       "-like" => "%(mozilla)%"
                     }
                   }
                 ]
               }
      strip_keys = ["hosts"]
    when 'notificationmethod'
      filter = nil
      strip_keys = ["notificationprofiles"]
    else
      # can't find section
    end
    [filter, strip_keys]
  end  

  def export(section)
    filter, strip_keys = get_section_export_details(section)
    output = export_section(section, filter, strip_keys)
    File.open(section + '.json', 'w') { |file| file.write(JSON.pretty_generate output) }
  end

  def delete_hosts_in_hostgroup(host_group_name)
    filter = {"-and" => 
               [
                 {"name" => 
                   {
                     "-like" => host_group_name
                   }
                 }
               ]
             }
    filter_hash = filter ? {:params => {:json_filter => filter.to_json}} : {}
    @logger.info("Fetching ids of hosts in #{host_group_name}")
    begin
      response = RestClient.get [@url, 'config', 'hostgroup'].join('/'),
        @token_header.merge(filter_hash)
    rescue => e
      raise "Could not reach opsview at #{server_url}. #{e}. #{e.http_body}"
    end  
    data = JSON.parse(response)
  
    if data['list'].length > 1 then
      raise "got multiple results"
    end
  
    @logger.debug("data is #{data.to_json}")
  
    hosts = data['list'][0]['hosts']
    ids = hosts.map {|x| x['ref'].split('/')[-1]}.compact
    
    ids.each do |id|
      @logger.info("Deleting host #{id}")
      if not @dryrun then
        begin
          response = RestClient.delete [@url, 'config', 'host', id].join('/'),
            @token_header
          @logger.info("response was #{response.to_json}")
        rescue => e
          raise "Could not reach opsview at #{server_url}. #{e}. #{e.http_body}"
        end
      end
    end
  end
end

SUB_COMMANDS = %w(import export destroystack)
p = Trollop::Parser.new do
  banner <<-EOS
OpsView Control

Usage:
       ./opsview_control.rb import --sections attribute --sections role [options]
       ./opsview_control.rb export --url http://localhost:10000/rest [options]
       ./opsview_control.rb destroystack --hostgroup "identity-dev Stack 0514" [options]
       ./opsview_control.rb export --help
EOS
  stop_on SUB_COMMANDS
end
global_opts = Trollop::with_standard_exception_handling p do
  p.parse ARGV
  raise Trollop::HelpNeeded if ARGV.empty? # show help screen
end

cmd = ARGV.shift # get the subcommand
opts = case cmd
  when "import"
    Trollop::options do
      opt :sections, "Config sections you would like to import", 
        :default => ['attribute', 'role', 'contact', 'servicegroup', 'servicecheck', 'hosttemplate', 'notificationmethod']
      opt :username, "OpsView API User Name", :type => :string, :default => 'admin'
      opt :password, "OpsView API User Password", :type => :string, :default => 'initial'
      opt :url, "OpsView API URL", :type => :string, :default => 'http://localhost/rest'
      opt :loglevel, "Logging verbosity", :default => "INFO"
      opt :dryrun, "Don't actually do anything"
    end
  when "export"
    Trollop::options do
      opt :sections, "Config sections you would like to export", 
        :default => ['attribute', 'role', 'contact', 'servicegroup', 'servicecheck', 'hosttemplate', 'notificationmethod']
      opt :username, "OpsView API User Name", :type => :string, :default => 'admin'
      opt :password, "OpsView API User Password", :type => :string, :default => 'initial'
      opt :url, "OpsView API URL", :type => :string, :default => 'http://localhost/rest'
      opt :loglevel, "Logging verbosity", :default => "INFO"
      opt :dryrun, "Don't actually do anything"
    end
  when "destroystack"
    Trollop::options do
      opt :hostgroup, "Name of the hostgroup to destroy", :type => :string
      opt :username, "OpsView API User Name", :type => :string, :default => 'admin'
      opt :password, "OpsView API User Password", :type => :string, :default => 'initial'
      opt :url, "OpsView API URL", :type => :string, :default => 'http://localhost/rest'
      opt :loglevel, "Logging verbosity", :default => "INFO"
      opt :dryrun, "Don't actually do anything"
    end
  when nil
    global_opts.educate
    exit
  else
    Trollop::die "unknown subcommand #{cmd.inspect}"
  end

mgr = OpsviewManager.new opts
case cmd
when "import"
  cmd_opts[:sections].each do |section|
    mgr.import_from_file section, "#{section}.json"
  end
  mgr.reload
when "export"
  cmd_opts[:sections].each do |section|
    mgr.export section
  end
when "destroystack"
  mgr.delete_hosts_in_hostgroup opts[:hostgroup]
  mgr.reload
end

