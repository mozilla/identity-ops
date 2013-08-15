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

# Set some constants
STRIP=1
COPY=2 #This is for keys which would normally be looked up but for which the OpsView API doesn't support it

class Hash
  def diff(other)
    (self.keys + other.keys).uniq.inject({}) do |memo, key|
      unless self[key] == other[key]
        if self[key].kind_of?(Hash) &&  other[key].kind_of?(Hash)
          memo[key] = self[key].diff(other[key])
        else
          memo[key] = [self[key], other[key]] 
        end
      end
      memo
    end
  end
end

class OpsviewManager
  def initialize(opts)
    @url, @username, @password, @dryrun, @session_cookie_name, @session_cookie_value = opts[:url], opts[:username], opts[:password], opts[:dryrun], opts[:session_cookie_name], opts[:session_cookie_value]
    @logger = Logger.new(STDOUT)
    begin
      @logger.level = Logger.const_get(opts[:loglevel])
    rescue NameError
      raise "Log level #{opts[:loglevel]} is not allowed"
    end
    @token_header = get_token
    @cache = {}
  end

  def get_token
    request_headers = {:content_type => :json,
      :accept => :json}
    if @session_cookie_name and @session_cookie_value then
      request_headers[:cookies] = {@session_cookie_name => @session_cookie_value}
    end
    @logger.debug("Getting ready to pass #{request_headers.to_json} to /login")
    begin
      response = RestClient.post [@url, 'login'].join('/'),
        {'username' => @username, 'password' => @password}.to_json,
        request_headers
    rescue => e
      raise "Could not reach opsview at #{@url}. #{e}."
    end
    token_header = {:x_opsview_username => @username,
     :x_opsview_token => JSON.parse(response.body)['token'],
     :content_type => :json,
     :accept => :json}
    if @session_cookie_name and @session_cookie_value then
      token_header[:cookies] = {@session_cookie_name => @session_cookie_value}
    end
    token_header
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

  def get_section(section, filter=nil)
    if not filter and @cache.include? section then
      @cache[section]
    else
      totalpages = 1
      page = 1
      result = {'list' => []}
      while page <= totalpages do
        @logger.debug("Fetching page #{page} of #{section}")
        begin
          params = {:params => {:page => page}}
          params[:params][:json_filter] = filter.to_json if filter
          response = RestClient.get [@url, 'config', section].join('/'),
            @token_header.merge(params)
        rescue => e
          raise "Could not reach opsview at #{@url}. #{e}. #{e.http_body}"
        end
        data = JSON.parse(response)
        totalpages = data['summary']['totalpages'].to_i
        result['list'] = result['list'] + data['list']
        page = page + 1
      end
      if not filter then
        @cache[section] = result
      end
      result    
    end
  end

  def export_section(section, filter=nil, strip_keys=[])
    @logger.info("exporting section #{section}")
    data = get_section(section, filter)
    strip_keys.each do |x|
      data['list'].each do |y|
        y.delete x
      end
    end
    data
  end

  def lookup_by_name(section, name)
    data = get_section(section)
    #@logger.debug(data.to_json)
    id = data['list'].map {|x| x['id'] if x['name'] == name}.compact
    raise "We got back multiple objects with the same name #{name} in section #{section}" if id.length > 1
    raise "Found no item with name #{name} in section #{section}" if id.length == 0
    @logger.debug("Found id #{id[0]} for object #{name}")
    {'ref' => "/rest/config/#{section}/#{id[0]}",
     'name' => name}
  end

  def import_from_file(section, filename)
    key_config = get_section_import_config(section)
    existing_objects = export_section(section)['list']
    existing_object_names = existing_objects.map {|x| x['name']}.compact
    existing_object_ids = existing_objects.map {|x| x['id']}.compact
    payload = JSON.parse(File.read(filename))
    @logger.info("Beginning transformation of #{payload['list'].length} items")

    def process_lookup(section, child, parent)
      @logger.debug("Looking up #{section}:#{child} for #{parent}")
      lookup_by_name(section, child)
    end

    payload['list'].map! do |obj|
      @logger.info("Beginning transformation of #{obj['name']}")
      for i in key_config.keys do
        case key_config[i]
        when STRIP
          @logger.debug("Stripping #{i} from #{obj['name']}")
          obj.delete i
          #obj[i] = nil
        when COPY
          # do nothing
        else
          # lord, this is super obfuscated. gotta come up with a better way to do this
          if key_config[i].class == Hash
            obj[i].map! do |subobj|
              for j in key_config[i].keys do
                # @logger.debug("key_config[i][j] #{key_config[i][j]}")
                # @logger.debug("j.class #{j.class}")
                # @logger.debug("j #{j}")
                # @logger.debug("subobj[j] #{subobj[j]}")
                # @logger.debug("subobj[j].class #{subobj[j].class}")
                #@logger.debug("subobj #{subobj.to_json}")
                # @logger.debug("subobj['name'] #{subobj['name']}")
                if subobj[j].class == Array
                  subobj[j].map! do |subsubobj|
                    process_lookup(key_config[i][j], subsubobj['name'], subobj['name'])
                  end
                elsif subobj[j].class == NilClass then
                  # Do no transformation
                else
                  subobj[j] = process_lookup(key_config[i][j], subobj[j]['name'], subobj['name'])
                end
              end
            subobj
            end
          else
            if obj[i].class == Array then
              obj[i].map! do |subobj|
                process_lookup(key_config[i], subobj['name'], obj['name'])
              end
            elsif obj[i].class == NilClass then
              # Do no transformation
            else
              # @logger.debug("key_config[i] #{key_config[i]}")
              # @logger.debug("i #{i}")
              # @logger.debug("obj[i] #{obj[i]}")
              # @logger.debug("obj[i].class #{obj[i].class}")
              #@logger.debug("obj #{obj.to_json}")
              # @logger.debug("obj['name'] #{obj['name']}")
              obj[i] = process_lookup(key_config[i], obj[i]['name'], obj['name'])
            end
          end
        end
      end
      @logger.info("Completed transforming #{obj['name']}")
      obj
    end

    payload['list'].map! do |obj|
      if existing_object_names.include? obj['name'] then
        # This object already exists
        existing_obj = existing_objects.map {|x| x if x['name'] == obj['name']}.compact
        if existing_obj.length > 1 then
          raise 'We got back multiple objects with the same name'
        end
        obj['id'] = existing_obj[0]['id']
      else
        if existing_object_ids.include? obj['id']
          # The object doesn't already exist but the id is in use
          obj.delete 'id'
        end
      end  
      obj
    end

    # Crazy one off
    # https://secure.opsview.com/wsvn/wsvn/opsview/trunk/opsview-core/lib/Opsview/ResultSet/Timeperiods.pm#Line43
    if section == 'timeperiod' then
      payload['list'].delete_if {|x| x['id'] == '1'}
    end
  
    @logger.info("About to import #{section}:#{payload['list'].map {|x| [x['id'], x['name']]}.compact.to_json}")
    @logger.info("Beginning import of #{payload['list'].length} items into #{section}")
  
    if not @dryrun then
      begin
        response = RestClient.put [@url, 'config', section].join('/'),
          payload.to_json,
          @token_header
      rescue => e
        raise "Could not reach opsview at #{@url}. #{e}. #{e.http_body}"
      end
      @logger.debug(response)
      @logger.info("Imported #{JSON.parse(response)['objects_updated']} items into #{section}")
      @logger.info("Import of #{section} complete")
    else
      print "dryrun : Would have imported : \n"
      print JSON.pretty_generate(payload)
      print "\ndryrun : over the existing : \n"
      print JSON.pretty_generate(existing_objects)
    end
  end

  def get_section_import_config(section)
    # This represents the order that each section should be imported in
    # (the order of the case statements) and what to do with the keys inside
    # each section when it's imported.
    #
    # Keys marked as STRIP should be stripped from the object before importing
    # These keys relationship with the stripped object will be represented
    # when the referenced object is imported later in the process
    #
    # Keys marked as 'string' should have the referenced object looked up by name
    # This will allow for differing object IDs between different OpsView
    # installations.
    #
    # Keys marked as COPY would normally be looked up just as 'string' except
    # that OpsView is missing the required API endpoint to look them up
    # As a result we just copy them across without doing a lookup.
    # This could result in a collision or duplication if these items
    # have been changed on one installation and not the other

    case section
    when 'monitoringserver'
      # Never import this section
    when 'keyword'
      key_config = {'hosts'=> STRIP,
                    'roles'=> STRIP,
                    'servicechecks' => STRIP}
    when 'timeperiod'
      key_config = {'servicecheck_notification_periods' => STRIP,
                    'servicecheck_check_periods' => STRIP,
                    'host_check_periods' => STRIP,
                    'host_notification_periods' => STRIP}
    when 'attribute'
      key_config = {'servicechecks' => STRIP}
    when 'servicegroup'
      key_config = {'servicechecks' => STRIP}
    when 'notificationmethod'
      key_config = {'notificationprofiles' => COPY}
    when 'hostcheckcommand'
      key_config = {'plugin' => COPY,
                    'hosts' => STRIP}
    when 'hostgroup'
      key_config = {'parent' => 'hostgroup',
                    'children' => STRIP}
    when 'role'
      key_config = {'contacts' => STRIP,
                    'monitoringservers' => 'monitoringserver',
                    'hostgroups' => 'hostgroup',
                    'accesses' => COPY,
                    'access_hostgroups' => 'hostgroup',
                    'access_servicegroups' => 'servicegroup',
                    'access_keywords' => 'keyword'}
    when 'contact'
      key_config = {# 'servicegroups' => 'servicegroup', # The docs imply this should be here but an actual export doesn't have it
                    # http://docs.opsview.com/doku.php?id=opsview-community:restapi:config#contacts
                    'notificationprofiles' => {'servicegroups' => 'servicegroup',
                                               'hostgroups' => 'hostgroup',
                                               'notification_period' => 'timeperiod'},
                    # 'keywords' => 'keyword', # The docs imply this should be here but an actual export doesn't have it
                    # http://docs.opsview.com/doku.php?id=opsview-community:restapi:config#contacts
                    # 'hostgroups' => 'hostgroup', # The docs imply this should be here but an actual export doesn't have it
                    # http://docs.opsview.com/doku.php?id=opsview-community:restapi:config#contacts
                    'role' => 'role'}
    when 'servicecheck'
      key_config = {'dependencies' => 'servicecheck',
                    'keywords' => 'keyword',
                    'attribute' => 'attribute',
                    'check_period' => 'timeperiod',
                    'notification_period' => 'timeperiod',
                    'snmptraprules' => COPY,
                    'plugin' => COPY,
                    'checktype' => COPY,
                    'hosttemplates' => STRIP, # this isn't mentioned in the docs but is returned
                    'servicegroup' => 'servicegroup'}
    when 'hosttemplate'
      key_config = {'hosts' => STRIP,
                    'servicechecks' => 'servicecheck'}
    when 'host'
      key_config = {'hosttemplates' => 'hosttemplate',
                    'check_period' => 'timeperiod',
                    'notification_period' => 'timeperiod',
                    'hostgroup' => 'hostgroup',
                    'monitored_by' => 'monitoringserver',
                    'parents' => 'host',
                    'servicechecks' => 'servicecheck',
                    'check_command' => 'hostcheckcommand'}
    else
      # can't find section
    end
      key_config
  end  


  def export_to_file(section)
    output = export_section(section)
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
    @logger.info("Fetching ids of hosts in #{host_group_name}")
    data = get_section('hostgroup', filter)

    if data['list'].length > 1 then
      raise "got multiple results"
    end
  
    @logger.debug("data is #{data.to_json}")
  
    hg_id = data['list'][0]['id']
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

    if not @dryrun then
      @logger.info("Deleting hostgroup #{hg_id}")
      begin
        response = RestClient.delete [@url, 'config', 'hostgroup', hg_id].join('/'),
          @token_header
        @logger.info("response was #{response.to_json}")
      rescue => e
        raise "Could not reach opsview at #{server_url}. #{e}. #{e.http_body}"
      end
    end

  end
end

SUB_COMMANDS = %w(import export destroystack)
p = Trollop::Parser.new do
  banner <<-EOS
OpsView Control

Usage:
       ./opsview_control.rb import --sections attribute role [options]
       ./opsview_control.rb export --url http://localhost:10000/rest [options]
       ./opsview_control.rb destroystack --hostgroup "identity-dev Stack 0514" [options]
       ./opsview_control.rb destroystack --hostgroup "identity-dev Stack 0514" --session-cookie-name myauthcookie --session-cookie-value user@example.com|ZgtjMZuFnsaopw6IDt3twGr9aDU= [options]
       ./opsview_control.rb export --help
EOS
  stop_on SUB_COMMANDS
end
global_opts = Trollop::with_standard_exception_handling p do
  p.parse ARGV
  raise Trollop::HelpNeeded if ARGV.empty? # show help screen
end

ordered_section_list = ['keyword',
                        'timeperiod',
                        'attribute',
                        'servicegroup',
                        'notificationmethod',
                        'hostcheckcommand',
                        'hostgroup',
                        'role',
                        'contact',
                        'servicecheck',
                        'hosttemplate']
# Add 'host' onto the end if you want to import hosts

cmd = ARGV.shift # get the subcommand
opts = case cmd
  when "import"
    Trollop::options do
      opt :sections, "Config sections you would like to import", :type => :strings,
        :default => ordered_section_list
      opt :username, "OpsView API User Name", :type => :string, :default => 'admin'
      opt :password, "OpsView API User Password", :type => :string, :default => 'initial'
      opt :url, "OpsView API URL", :type => :string, :default => 'http://localhost/rest'
      opt :loglevel, "Logging verbosity", :default => "INFO"
      opt :session_cookie_name, "Name of a cookie to pass to Opsview or an authentication gateway in front of it", :type => :string
      opt :session_cookie_value, "Session cookie value", :type => :string
      opt :dryrun, "Don't actually do anything"
    end
  when "export"
    Trollop::options do
      opt :sections, "Config sections you would like to export", :type => :strings, 
        :default => ordered_section_list
      opt :username, "OpsView API User Name", :type => :string, :default => 'admin'
      opt :password, "OpsView API User Password", :type => :string, :default => 'initial'
      opt :url, "OpsView API URL", :type => :string, :default => 'http://localhost/rest'
      opt :loglevel, "Logging verbosity", :default => "INFO"
      opt :session_cookie_name, "Name of a cookie to pass to Opsview or an authentication gateway in front of it", :type => :string
      opt :session_cookie_value, "Session cookie value", :type => :string
      opt :dryrun, "Don't actually do anything"
    end
  when "destroystack"
    Trollop::options do
      opt :hostgroup, "Name of the hostgroup to destroy", :type => :string
      opt :username, "OpsView API User Name", :type => :string, :default => 'admin'
      opt :password, "OpsView API User Password", :type => :string, :default => 'initial'
      opt :url, "OpsView API URL", :type => :string, :default => 'http://localhost/rest'
      opt :loglevel, "Logging verbosity", :default => "INFO"
      opt :session_cookie_name, "Name of a cookie to pass to Opsview or an authentication gateway in front of it", :type => :string
      opt :session_cookie_value, "Session cookie value", :type => :string
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
  opts[:sections].each do |section|
    mgr.import_from_file section, "#{section}.json"
    mgr.reload
  end
when "export"
  opts[:sections].each do |section|
    mgr.export_to_file section
  end
when "destroystack"
  mgr.delete_hosts_in_hostgroup opts[:hostgroup]
  mgr.reload
end

