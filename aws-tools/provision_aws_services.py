import logging
logging.basicConfig(level=logging.DEBUG)

import json
import time
import pickle
import os

def global_one_time_provision(path):
    region = 'universal'

    # Upload certificates
    import boto.iam
    # Note here we don't use region because IAM isn't bound to a region
    conn_iam = boto.iam.connect_to_region(region)

    existing_certs = conn_iam.get_all_server_certs(path_prefix=path)['list_server_certificates_response']['list_server_certificates_result']['server_certificate_metadata_list']

    for cert_params in secrets['certs']:
        if cert_params['cert_name'] not in [x['server_certificate_name'] for x in existing_certs]:
            if 'path' not in cert_params:
                cert_params['path'] = path
            conn_iam_response = conn_iam.upload_server_cert(**cert_params)
            logging.debug('added certificate %s' % cert_params['cert_name'])
    logging.debug('certs added')

def create_iam_roles(path):
    import boto.iam
    import string
    region = 'universal'
    conn_iam = boto.iam.connect_to_region(region)

    #user = conn_iam.get_user()['get_user_response']['get_user_result']['user']
    #account_id = user['arn'].split(':')[4]
    account_alias = conn_iam.get_account_alias()['list_account_aliases_response']['list_account_aliases_result']['account_aliases'][0]
    
    # arn:aws:<service>:<region>:<namespace>:<relative-id>
    policy_document_template = '''{
  "Statement": [
    {
      "Action": [
        "elasticloadbalancing:DescribeInstanceHealth",
        "elasticloadbalancing:DescribeLoadBalancers"
      ],
      "Effect": "Allow",
      "Resource": [
        "*"
      ]
    },
    {
      "Action": [
        "s3:GetObject",
        "s3:GetObjectTorrent",
        "s3:GetObjectVersion",
        "s3:GetObjectVersionTorrent"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:s3:::${account_alias}-us-standard/${environment}/${tier}/*"
      ]
    },
    {
      "Action": [
        "ec2:AllocateAddress",
        "ec2:AssociateAddress",
        "ec2:DescribeAddresses",
        "ec2:DescribeTags"
      ],
      "Effect": "Allow",
      "Resource": [
        "*"
      ]
    }
  ]
}'''

#        "ec2:DisassociateAddress",
#        "ec2:ReleaseAddress"

#    {
#      "Action": [
#        "route53:ChangeResourceRecordSets",
#        "route53:GetChange",
#        "route53:ListResourceRecordSets"
#      ],
#      "Effect": "Allow",
#      "Resource": [
#        "*"
#      ]
#    }
    
    existing_instance_profiles = conn_iam.list_instance_profiles(path)['list_instance_profiles_response']['list_instance_profiles_result']['instance_profiles']
    for environment in ['identity-dev', 'identity-prod']:
        for tier in ['webhead', 'bigtent', 'keysign', 'dbwrite', 'dbread', 'dbmaster', 'proxy', 'admin']:
            if '%s-%s' % (environment, tier) in [x['instance_profile_name'] for x in existing_instance_profiles]:
                # This instance profile exists already
                continue
            template_vars = {'environment':environment,
                             'tier':tier,
                             'account_alias':account_alias}
            instance_profile_name = '%s-%s' % (environment, tier)
            role_name = instance_profile_name
            policy_name = '%s-base' % instance_profile_name

            instance_profile = conn_iam.create_instance_profile(instance_profile_name, path)
            role = conn_iam.create_role(role_name, None, path)
            conn_iam.add_role_to_instance_profile(instance_profile_name, role_name)
            policy_document = string.Template(policy_document_template).safe_substitute(template_vars)
            logging.debug('about to add policy to %s : "%s"' % (role_name, policy_document))
            conn_iam.put_role_policy(role_name, policy_name, policy_document)

def one_time_provision(secrets, path, region, availability_zones, key_name = None):
    # 1 region
    # 2 VPCs, prod and nonprod
    # 3 AZs in each VPC
    # 6 subnets per AZ
    # 6*3 = 18 subnets
    # 32 /26 subnets in the VPC's /21

    from netaddr import IPNetwork # sudo pip install netaddr

    subnet_size = 24
    desired_security_groups = json.load(open('config/security_groups.json', 'r'))
    
    import boto.vpc
    import boto.ec2
    import boto.exception

    vpcs = {}

    vpcs[region] = {}
    conn_vpc = boto.vpc.connect_to_region(region)
    conn_ec2 = boto.ec2.connect_to_region(region)

    desired_vpcs = {'us-west-2': 
                       [{'Name':'identity-dev',
                         'App':'identity',
                         'Env':'dev',
                         'cidr':'10.148.24.0/21'},
                        {'Name':'identity-prod',
                         'App':'identity',
                         'Env':'prod',
                         'cidr':'10.148.32.0/21',
                         'vpn_target': '63.245.216.58'}
                       ],
                    'us-east-1':
                       [{'Name':'identity-dev',
                         'App':'identity',
                         'Env':'dev',
                         'cidr':'10.146.24.0/21'},
                        {'Name':'identity-prod',
                         'App':'identity',
                         'Env':'prod',
                         'cidr':'10.146.32.0/21',
                         'vpn_target': '63.245.216.58'}
                       ]
                    }

    asn_map = {'us-west-2': 65148,
               'us-east-1': 65146}

    ami_map = json.load(open('config/ami_map.json', 'r'))

    if not key_name:
        key_name = 'svcops-sl62-base-key-%s' % region

    for desired_vpc in desired_vpcs[region]:
        environment=desired_vpc['Name']
        existing_vpcs = conn_vpc.get_all_vpcs()
        if desired_vpc['Name'] in [x.tags['Name'] for x in existing_vpcs if 'Name' in x.tags]:
            logging.debug('skipping creation of vpc %s since it already exists' % desired_vpc['Name'])
            #continue
        vpcs[region][environment] = {}

        # Create VPCs
        vpcs[region][environment]['vpc'] = [x.tags['Name'] for x in existing_vpcs if 'Name' in x.tags]
        vpcs[region][environment]['vpc'] = conn_vpc.create_vpc(desired_vpc['cidr'])
        vpc = vpcs[region][environment]['vpc']
        logging.debug('created vpc %s with id %s and ip range %s' % (environment, vpc.id, vpc.cidr_block))
        if vpc.state != 'available':
            time.sleep(1)
            vpc = conn_vpc.get_all_vpcs([vpc.id])[0]
        vpc.add_tag('Name', environment)
        vpc.add_tag('App', desired_vpc['App'])
        vpc.add_tag('Env', desired_vpc['Env'])
        logging.debug('tagged vpc %s with %s' % (vpc.cidr_block, environment))

        # Create all security groups
        vpcs[region][environment]['security-groups'] = {}
        for security_group_definition in desired_security_groups:
            security_group_name = environment + '-' + security_group_definition[0]
            vpcs[region][environment]['security-groups'][security_group_name] = conn_ec2.create_security_group(
                      security_group_name, 
                      security_group_name, 
                      vpc.id)
            security_group = vpcs[region][environment]['security-groups'][security_group_name]

            # This loop is to workaround the race condition between creating the security group
            # and the security group being available for use
            attempts=0
            while True:
                try:
                    # This is to workaround the fact that AWS only returns the groupId when CreateSecurityGroup is called
                    # instead of the entire object
                    attempts += 1
                    security_group = conn_ec2.get_all_security_groups(group_ids=[security_group.id])[0]
                    break
                except boto.exception.EC2ResponseError:
                    time.sleep(1)
                    if attempts > 5:
                        raise

            security_group.add_tag('Name', security_group_name)
            security_group.add_tag('App', desired_vpc['App'])
            security_group.add_tag('Env', desired_vpc['Env'])

            # Delete the default egress authorization
            conn_ec2.revoke_security_group_egress(group_id=security_group.id, ip_protocol=-1, cidr_ip='0.0.0.0/0')
            # And create an internal egress authorization
            conn_ec2.authorize_security_group_egress(group_id=security_group.id, ip_protocol=-1, cidr_ip=desired_vpc['cidr'])

            logging.debug('created security group %s in VPC %s' % (security_group.name, security_group.vpc_id))
            for security_group_definition_rule in security_group_definition[1]:
                rule = security_group_definition_rule.copy()
                rule['group_id'] = security_group.id

                # Handle rules where we set the cidr_ip to "vpc"
                if 'cidr_ip' in rule and rule['cidr_ip'] == 'vpc':
                    rule['cidr_ip'] = desired_vpc['cidr']
                
                if 'direction' not in rule:
                    rule['direction'] = 'ingress'

                # This is to deal with the fact that ingress and egress authorizations work differently
                if 'src_security_group_name' in rule:
                    rule['src_security_group_name'] = environment + '-' + rule['src_security_group_name']
                    src_group = vpcs[region][environment]['security-groups'][rule['src_security_group_name']]
                    if rule['direction'] == 'egress':
                        # egress
                        rule['src_group_id'] = src_group.id
                    else:
                        # ingress
                        rule['src_security_group_owner_id'] = src_group.owner_id
                        rule['src_security_group_group_id'] = src_group.id
                    del rule['src_security_group_name']

                if rule['direction'] == 'ingress':
                    del rule['direction']
                    if not conn_ec2.authorize_security_group(**rule):
                        logging.error('failed to add ingress rule %s to security group %s' % (rule,security_group_name))
                else:
                    del rule['direction']
                    if not conn_ec2.authorize_security_group_egress(**rule):
                        logging.error('failed to add egress rule %s to security group %s' % (rule,security_group_name))
                logging.debug('added rule %s to security group %s' % (rule, security_group_name))

        # Create internet gateway (a separate one is required for each VPC)
        vpcs[region][environment]['internet_gateway'] = conn_vpc.create_internet_gateway()
        # not testing to validate that the ig exists
        internet_gateway = vpcs[region][environment]['internet_gateway']
        if not conn_vpc.attach_internet_gateway(internet_gateway.id, vpc.id):
            logging.error('failed to attach internet gateway %s to vpc %s' % (internet_gateway.id, vpc.id))
        # TODO : tag the internet_gateway

        # Create VPN to PHX1
        if 'vpn_target' in desired_vpc:
            customer_gateway = conn_vpc.create_customer_gateway('ipsec.1', desired_vpc['vpn_target'], asn_map[region])
            vpn_gateway = conn_vpc.create_vpn_gateway('ipsec.1')
            vpn_connection = conn_vpc.create_vpn_connection('ipsec.1', customer_gateway.id, vpn_gateway.id)
            # routing : dynamic
            customer_gateway_configuration = vpn_connection.customer_gateway_configuration
            
            # TODO set the route table to allow route propoation from the VGW

            vpn_gateway_attachment = conn_vpc.attach_vpn_gateway(vpn_gateway.id, vpc.id)
            #conn_vpc.create_vpn_connection_route(destination_cidr_block, vpn_connection_id)
            #conn_vpc.create_route(route_table_id, destination_cidr_block, gateway_id=None, instance_id=None)

        # Create subnets
        vpcs[region][environment]['availability_zones'] = {}
        ip = IPNetwork(vpc.cidr_block)
        available_subnets = ip.subnet(subnet_size)
        for availability_zone in [region + x for x in availability_zones]:
            vpcs[region][environment]['availability_zones'][availability_zone] = {}
            vpcs[region][environment]['availability_zones'][availability_zone]['subnets'] = {}
            for subnet_type in ['public', 'private']:
                vpcs[region][environment]['availability_zones'][availability_zone]['subnets'][subnet_type] = conn_vpc.create_subnet(
                        vpc.id, 
                        available_subnets.next(), 
                        availability_zone=availability_zone)
                subnet = vpcs[region][environment]['availability_zones'][availability_zone]['subnets'][subnet_type]
                if subnet.state != 'available':
                    time.sleep(1)
                    subnet = conn_vpc.get_all_subnets([subnet.id])[0]
                subnet.add_tag('Name', environment + '-' + subnet_type + '-' + availability_zone)
                subnet.add_tag('App', desired_vpc['App'])
                subnet.add_tag('Env', desired_vpc['Env'])
                logging.debug('created %s subnet %s in VPC %s in AZ %s' % (subnet_type, subnet.cidr_block, subnet.vpc_id, subnet.availability_zone)) 
                # http://docs.aws.amazon.com/AWSEC2/latest/APIReference/ApiReference-ItemType-SubnetType.html

        # Spin up a NAT instance
        # We'll just put it in the first availability zone, whatever that is
        reservation = conn_ec2.run_instances(image_id = ami_map['ami-vpc-nat-1.0.0-beta.i386-ebs'][region],
                               key_name = key_name,
                               security_group_ids = [vpcs[region][environment]['security-groups'][environment + '-' + 'natsg'].id],
                               instance_type = 't1.micro',
                               subnet_id = vpcs[region][environment]['availability_zones'][region + availability_zones[0]]['subnets']['public'].id)
        vpcs[region][environment]['nat_instance'] = {}
        
        # Loop to wait for the instance to spin up
        attempts = 0
        sleep_time = 10
        max_attempts = 600
        while True:
            try:
                nat_instance_state = conn_ec2.get_all_instances([reservation.instances[0].id])[0].instances[0].state
            except (boto.exception.EC2ResponseError, IndexError):
                nat_instance_state = False
            attempts += 1
            if nat_instance_state != 'running':
                logging.debug('waiting 10 seconds while instance %s enters a "running" state in order to assign it\'s EIP' % reservation.instances[0].id) 
                time.sleep(sleep_time)
                if attempts > max_attempts:
                    logging.error('after 10 minutes instance %s remains in a state other than "running". continuing with EIP association which will fail' % reservation.instances[0].id)
            else:
                break

        vpcs[region][environment]['nat_instance']['instance'] = conn_ec2.get_all_instances([reservation.instances[0].id])[0].instances[0]
        nat_instance = vpcs[region][environment]['nat_instance']['instance']

        nat_instance.add_tag('Name', environment + '-nat_instance')
        nat_instance.add_tag('App', desired_vpc['App'])
        nat_instance.add_tag('Env', desired_vpc['Env'])

        # Get and assign EIP to NAT instance
        vpcs[region][environment]['nat_instance']['address'] = conn_ec2.allocate_address('vpc')
        address = vpcs[region][environment]['nat_instance']['address']

        # TODO : tag the address

        conn_ec2.associate_address(instance_id=nat_instance.id,
                                   public_ip=None,
                                   allocation_id=address.allocation_id
                                   )

        # Not using address.associate while waiting for merge of  https://github.com/boto/boto/pull/1310
        # address.associate(nat_instance.id)
        
        # Disabling Source/Destination Checks
        if not conn_ec2.modify_instance_attribute(nat_instance.id, 'sourceDestCheck', False):
            logging.error('failed to disable Source/Desk Checks on nat_instance %s' % nat_instance.id)
        
        # Route tables
        vpcs[region][environment]['route_tables'] = {}

        # Create public route table
        vpcs[region][environment]['route_tables']['public'] = conn_vpc.create_route_table(vpc.id)
        route_table = vpcs[region][environment]['route_tables']['public']
        if not conn_vpc.create_route(route_table_id = route_table.id,
                                     destination_cidr_block = '0.0.0.0/0',
                                     gateway_id = internet_gateway.id):
            logging.error('failed to add route sending 0.0.0.0/0 traffic to internet gateway %s in route table %s' % (internet_gateway.id, route_table.id))

        # TODO : tag the route_table

        # Associate public subnets with route table
        for availability_zone in [region + x for x in availability_zones]:
            subnet = vpcs[region][environment]['availability_zones'][availability_zone]['subnets']['public']
            route_table_association = conn_vpc.associate_route_table(route_table.id,
                                                                     subnet.id)
            logging.debug('associated subnet %s with route table %s' % (subnet.id, route_table.id)) 

        # Create private route table
        vpcs[region][environment]['route_tables']['private'] = conn_vpc.create_route_table(vpc.id)
        route_table = vpcs[region][environment]['route_tables']['private']

        # TODO : tag the route_table

        # TODO add a route for the PHX1 DB 10.18.20.21/32

        # Associate private subnets with route table
        for availability_zone in [region + x for x in availability_zones]:
            subnet = vpcs[region][environment]['availability_zones'][availability_zone]['subnets']['private']
            route_table_association = conn_vpc.associate_route_table(route_table.id,
                                                                     subnet.id)
            logging.debug('associated subnet %s with route table %s' % (subnet.id, route_table.id)) 

        # Set Instance NAT as gateway route for private route table
        if not conn_vpc.create_route(route_table_id = route_table.id,
                                     destination_cidr_block = '0.0.0.0/0',
                                     instance_id = nat_instance.id):
            logging.error('failed to add route sending 0.0.0.0/0 traffic to nat instance %s in route table %s' % (nat_instance.id, route_table.id))

        if 'vpn_target' in desired_vpc:
            logging.info('Customer Gateway Configuration = "\n%s\n"' % customer_gateway_configuration)
        logging.debug('vpc created')
        #pickle.dump(vpcs[region][environment], open(pkl_filename, 'wb'))
        #logging.debug('pickled vpc to %s' % pkl_filename)

    return vpcs

def get_secrets():
    if 'AWS_CONFIG_DIR' in os.environ:
        secrets_filename = os.path.join(os.environ['AWS_CONFIG_DIR'], 'identity-secrets.json')
    else:
        secrets_filename = 'config/secrets.example.json'
    with open(secrets_filename, 'rb') as secrets_file:
        logging.debug('loading secrets from %s' % secrets_filename)
        return json.load(secrets_file)

if __name__ == '__main__':
    secrets = get_secrets()
    path = "/identity/"

    #region = 'us-west-1'
    #availability_zones = ['b','c']

    #region = 'us-west-2'
    #availability_zones = ['a','b','c']

    region = 'us-east-1'
    availability_zones = ['a','b','d']

    global_data = global_one_time_provision(path)
    # create_iam_roles(path)
    vpcs = one_time_provision(secrets, path, region, availability_zones, None)
    