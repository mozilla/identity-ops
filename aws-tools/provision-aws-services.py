import logging
import json

def one_time_provision(secrets, path):
    # 1 region
    # 2 VPCs, prod and nonprod
    # 3 AZs in each VPC
    # 6 subnets per AZ
    # 6*3 = 18 subnets
    # 32 /26 subnets in the VPC's /21

    import pickle
    pkl_filename = 'vpcs.pkl'
    try:
        with open(pkl_filename, 'rb') as pkl_file:
            logging.debug('loading vpcs from %s' % pkl_filename)
            vpcs = pickle.load(pkl_file)
            return vpcs
    except IOError as e:
        # We haven't run this before and the vpcs object hasn't been created
        pass
    
    from netaddr import * # sudo pip install netaddr
    region = 'us-west-2'
    availability_zones = ['a','b','c']
    subnet_size = 24
    desired_security_groups_json = '''
[
    [
        "identity-admin",
        [
            {
                "ip_protocol": "tcp",
                "from_port": 22,
                "to_port": 22,
                "cidr_ip": "0.0.0.0/0"
            }
        ]
    ],
    [
        "identity-administrable",
        [
            {
                "ip_protocol": "tcp",
                "from_port": 22,
                "to_port": 22,
                "src_group": "identity-admin"
            }
        ]
    ],
    [
        "identity-public-loadbalancer",
        [
            {
                "direction": "ingress",
                "ip_protocol": "tcp",
                "from_port": 80,
                "to_port": 80,
                "cidr_ip": "0.0.0.0/0"
            },
            {
                "ip_protocol": "tcp",
                "from_port": 443,
                "to_port": 443,
                "cidr_ip": "0.0.0.0/0"
            }
        ]
    ],
    [
        "identity-frontend",
        [
            {
                "ip_protocol": "tcp",
                "from_port": 80,
                "to_port": 80,
                "src_group": "identity-public-loadbalancer"
            }
        ]
    ],
    [
        "identity-private-loadbalancer",
        [
            {
                "ip_protocol": "tcp",
                "from_port": 80,
                "to_port": 80,
                "src_group": "identity-frontend"
            }
        ]
    ],
    [
        "identity-middleware-http",
        [
            {
                "ip_protocol": "tcp",
                "from_port": 80,
                "to_port": 80,
                "src_group": "identity-private-loadbalancer"
            }
        ]

    [
        "identity-dbwrite",
        []
    ],
    [
        "identity-db-ro",
        [
            {
                "ip_protocol": "tcp",
                "from_port": 3306,
                "to_port": 3306,
                "src_group": "identity-private-loadbalancer"
            }
        ]
    ],
    [
        "identity-db-rw",
        [
            {
                "ip_protocol": "tcp",
                "from_port": 3306,
                "to_port": 3306,
                "src_group": "identity-db-ro"
            },
            {
                "ip_protocol": "tcp",
                "from_port": 3306,
                "to_port": 3306,
                "src_group": "identity-dbwrite"
            }
        ]
    ],
    [
        "identity-internet-outbound",
        []
    ],
    [
        "identity-proxy-loadbalancer",
        [
            {
                "ip_protocol": "tcp",
                "from_port": 8888,
                "to_port": 8888,
                "src_group": "identity-internet-outbound"
            }
        ]
    ],
    [
        "identity-proxy",
        [
            {
                "ip_protocol": "tcp",
                "from_port": 80,
                "to_port": 80,
                "src_group": "identity-proxy-loadbalancer"
            }
        ]
    ]
]
'''
    desired_security_groups = json.loads(desired_security_groups_json)
    
    # do we need to revoke egress on everything? and grant it on the proxy with authorize_security_group_egress?
    # yes
    # revoking on the command line fails due to a bug : https://forums.aws.amazon.com/thread.jspa?threadID=104639

    import boto.vpc
    import boto.ec2
    conn_vpc = boto.vpc.connect_to_region(region)

    desired_vpcs = {'identity-dev' : '10.148.24.0/21',
                    'identity-prod' : '10.148.32.0/21'}
    vpcs = {}
    for environment in desired_vpcs.keys():
        vpcs[region] = {}
        vpcs[region][environment] = {}

        # Create VPCs
        new_vpc = conn_vpc.create_vpc(desired_vpcs[environment])
        logging.debug('created vpc %s with id %s and ip range %s' % (environment, new_vpc.id, new_vpc.cidr_block))
        # TODO : boto.ec2.ec2object.add_tag('prod')
        vpcs[region][environment]['vpc'] = new_vpc

        ip = IPNetwork(vpc.cidr_block)
        available_subnets = ip.subnet(subnet_size)

        vpcs[region][environment]['availability_zones'] = {}
        # Create subnets
        for availability_zone in [region + x for x in availability_zones]:
            vpcs[region][environment]['availability_zones'][availability_zone] = {}
            vpcs[region][environment]['availability_zones'][availability_zone]['subnets'] = {}
            subnet = conn_vpc.create_subnet(vpc.id, available_subnets.next(), availability_zone=availability_zone)
            vpcs[region][environment]['availability_zones'][availability_zone]['subnets']['public']=subnet
            logging.debug('created public subnet %s in VPC %s in AZ %s' % (subnet.cidr_block, subnet.vpc_id, subnet.availability_zone)) 
            subnet = conn_vpc.create_subnet(vpc.id, available_subnets.next(), availability_zone=availability_zone)
            vpcs[region][environment]['availability_zones'][availability_zone]['subnets']['private']=subnet
            logging.debug('created private subnet %s in VPC %s in AZ %s' % (subnet.cidr_block, subnet.vpc_id, subnet.availability_zone)) 
            # http://docs.aws.amazon.com/AWSEC2/latest/APIReference/ApiReference-ItemType-SubnetType.html

        # Create all security groups
        conn_ec2 = boto.ec2.connect_to_region(region)
        vpcs[region][environment]['security-groups'] = {}
        for security_group_definition in desired_security_groups:
            security_group_name = environment + '-' + security_group_definition[0]
            security_group = conn_ec2.create_security(security_group_name, security_group_name, vpc.id)
            vpcs[region][environment]['security-groups'][security_group_name] = security_group
            logging.debug('created security group %s in VPC %s' % (security_group.name, security_group.vpc_id))
            for rule in security_group_definition[1]:
                if not vpcs[region][environment]['security-groups'][security_group_name].authorize(**rule):
                    logging.error('failed to add rule to security group %s' % security_group.vpc_id)
                else:
                    logging.debug('added rule %s to security group %s' % (rule, security_group.vpc_id))

        # Upload certificates
        import boto.iam
        # Note here we don't use region because IAM isn't bound to a region
        conn_iam = boto.iam.connect_to_region('universal')

        vpcs[region][environment]['certs'] = {}
        for cert_params in secrets[environment]['certs']:
            if 'path' not in cert_params:
                cert_params['path'] = path
            cert = conn_iam.upload_server_cert(**cert_params)
            logging.debug('added certificate %s with id %s' % (cert.server_certificate_name, cert.server_certificate_id))
            vpcs[region][environment]['certs'][cert_name] = cert
            # cert.ServerCertificateId
            # http://docs.aws.amazon.com/IAM/latest/APIReference/API_ServerCertificateMetadata.html

    pickle.dump(vpcs, open(pkl_filename, 'wb'))
    return vpcs

def create_stack(region, environment, stack_type, vpc, arn_prefix, path):
    desired_elbs_json = {}
    # I'm not sure the best way to do this. I don't want to deviate from the prod/dev environment split
    # but I need to do 3 stack types, prod stage and dev here.
    desired_elbs_json['stage'] = '''
[
    {
        "name": "public-anosrep.org",
        "subnets" : 
        [
            "public"
        ],
        "security_groups" :
        [
            "identity-public-loadbalancer"
        ],
        "is_internal" : false,
        "listeners" : 
        [
            [
                443,
                80,
                "HTTPS",
                "wildcard.anosrep.org"
            ],
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "public-login.anosrep.org",
        "subnets" : 
        [
            "public"
        ],
        "security_groups" :
        [
            "identity-public-loadbalancer"
        ],
        "is_internal" : false,
        "listeners" : 
        [
            [
                443,
                80,
                "HTTPS",
                "wildcard.login.anosrep.org"
            ],
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "public-diresworb.org",
        "subnets" : 
        [
            "public"
        ],
        "security_groups" :
        [
            "identity-public-loadbalancer"
        ],
        "is_internal" : false,
        "listeners" : 
        [
            [
                443,
                80,
                "HTTPS",
                "wildcard.diresworb.org"
            ],
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "public-bigtent.login.anosrep.org",
        "subnets" : 
        [
            "public"
        ],
        "security_groups" :
        [
            "identity-public-loadbalancer"
        ],
        "is_internal" : false,
        "listeners" : 
        [
            [
                443,
                80,
                "HTTPS",
                "wildcard.login.anosrep.org"
            ]
        ]
    },
    {
        "name": "private-keysign",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-private-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "private-dbwrite",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-private-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "private-dbread",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-private-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                3306,
                3306,
                "TCP"
            ]
        ],
        "healthcheck" :
        {
            "interval" : 30,
            "target" : "TCP:3306",
            "healthy_threshold" : 3,
            "timeout" : 5,
            "unhealthy_threshold" : 5
        }
    },
    {
        "name": "private-proxy",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-proxy-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                8888,
                8888,
                "TCP"
            ]
        ],
        "healthcheck" :
        {
            "interval" : 30,
            "target" : "TCP:8888",
            "healthy_threshold" : 3,
            "timeout" : 5,
            "unhealthy_threshold" : 5
        }
    }
]
'''
    desired_elbs_json['dev'] = '''
[
    {
        "name": "public-personatest.org",
        "subnets" : 
        [
            "public"
        ],
        "security_groups" :
        [
            "identity-public-loadbalancer"
        ],
        "is_internal" : false,
        "listeners" : 
        [
            [
                443,
                80,
                "HTTPS",
                "wildcard.personatest.org"
            ],
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "public-bigtent.login.personatest.org",
        "subnets" : 
        [
            "public"
        ],
        "security_groups" :
        [
            "identity-public-loadbalancer"
        ],
        "is_internal" : false,
        "listeners" : 
        [
            [
                443,
                80,
                "HTTPS",
                "wildcard.personatest.org"
            ],
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "private-keysign",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-private-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "private-dbwrite",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-private-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "private-dbread",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-private-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                3306,
                3306,
                "TCP"
            ]
        ],
        "healthcheck" :
        {
            "interval" : 30,
            "target" : "TCP:3306",
            "healthy_threshold" : 3,
            "timeout" : 5,
            "unhealthy_threshold" : 5
        }
    },
    {
        "name": "private-proxy",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-proxy-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                8888,
                8888,
                "TCP"
            ]
        ],
        "healthcheck" :
        {
            "interval" : 30,
            "target" : "TCP:8888",
            "healthy_threshold" : 3,
            "timeout" : 5,
            "unhealthy_threshold" : 5
        }
    }

]
'''
    desired_elbs_json['prod'] = '''
[
    {
        "name": "public-persona.org",
        "subnets" : 
        [
            "public"
        ],
        "security_groups" :
        [
            "identity-public-loadbalancer"
        ],
        "is_internal" : false,
        "listeners" : 
        [
            [
                443,
                80,
                "HTTPS",
                "multisan-www.persona.org"
            ],
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "public-browserid.org",
        "subnets" : 
        [
            "public"
        ],
        "security_groups" :
        [
            "identity-public-loadbalancer"
        ],
        "is_internal" : false,
        "listeners" : 
        [
            [
                443,
                80,
                "HTTPS",
                "www.browserid.org"
            ],
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "public-bigtent.login.persona.org",
        "subnets" : 
        [
            "public"
        ],
        "security_groups" :
        [
            "identity-public-loadbalancer"
        ],
        "is_internal" : false,
        "listeners" : 
        [
            [
                443,
                80,
                "HTTPS",
                "bigtent.login.persona.org"
            ]
        ]
    },
    {
        "name": "private-keysign",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-private-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "private-dbwrite",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-private-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                80,
                80,
                "HTTP"
            ]
        ]
    },
    {
        "name": "private-dbread",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-private-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                3306,
                3306,
                "TCP"
            ]
        ],
        "healthcheck" :
        {
            "interval" : 30,
            "target" : "TCP:3306",
            "healthy_threshold" : 3,
            "timeout" : 5,
            "unhealthy_threshold" : 5
        }
    },
    {
        "name": "private-proxy",
        "subnets" : 
        [
            "private"
        ],
        "security_groups" :
        [
            "identity-proxy-loadbalancer"
        ],
        "is_internal" : true,
        "listeners" : 
        [
            [
                8888,
                8888,
                "TCP"
            ]
        ],
        "healthcheck" :
        {
            "interval" : 30,
            "target" : "TCP:8888",
            "healthy_threshold" : 3,
            "timeout" : 5,
            "unhealthy_threshold" : 5
        }
    }
]
'''
    import boto.ec2
    from boto.ec2.elb import HealthCheck
    stack = {}
    availability_zones = vpc[region][environment]['availability_zones'].keys()
    conn_elb = boto.ec2.elb.connect_to_region(region)
    stack['loadbalancer'] = []
    for load_balancers in json.loads(desired_elbs_json[stack_type]):
        if len(load_balancer['listeners']) == 4:
            # http://docs.aws.amazon.com/IAM/latest/UserGuide/Using_Identifiers.html
            load_balancer['listeners'][3] = "%s:server-certificate%s%s" % (arn_prefix, path, load_balancer['listeners'][3])
        subnets = []
        for availability_zone in availability_zones:
            for subnet_name in load_balancer['subnets']:
                subnets.append(vpc[region][environment]['availability_zones'][availability_zone]['subnets'][subnet_name].subnetId)

        lb = conn.create_load_balancer(load_balancer[name], 
                                       availability_zones, 
                                       load_balancer[listeners],
                                       subnets,
                                       [environment + '-' + x for x in load_balancer['security_groups']],
                                       'internal' if load_balancer['is_internal'] else 'internet-facing'
                                       )
        healthcheck_params = load_balancer['healthcheck'] if 'healthcheck' in load_balancer else {
            "interval" : 30,
            "target" : "HTTP:80/__heartbeat__",
            "healthy_threshold" : 3,
            "timeout" : 5,
            "unhealthy_threshold" : 5
        }
        # healthcheck_params['access_point'] = load_balancer[name]
        lb.configure_health_check(HealthCheck(**healthcheck_params))
        stack['loadbalancer'].append(lb)

    desired_launch_configuration_json = {}
    # image_id will need to be variable in a multi-region context
    desired_launch_configuration_json['prod'] = '''
[
    {
        "name" : "webhead",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-frontend",
            "identity-administrable"
        ]
    },
    {
        "name" : "bigtent",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-frontend",
            "identity-administrable"
        ]
    },
    {
        "name" : "keysign",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-middleware",
            "identity-administrable"
        ]
    },
    {
        "name" : "dbwrite",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-middleware",
            "identity-dbwrite",
            "identity-administrable"
        ]
    },
    {
        "name" : "dbread",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-db-ro",
            "identity-administrable"
        ]
    },
    {
        "name" : "dbmaster",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-db-rw",
            "identity-administrable"
        ]
    },
    {
        "name" : "proxy",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-proxy",
            "identity-administrable"
        ]
    },
    {
        "name" : "admin",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-admin"
        ]
    }
]
'''
    desired_launch_configuration_json['stage'] = '''
[
    {
        "name" : "webhead",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-frontend",
            "identity-administrable"
        ]
    },
    {
        "name" : "bigtent",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-frontend",
            "identity-administrable"
        ]
    },
    {
        "name" : "keysign",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-middleware",
            "identity-administrable"
        ]
    },
    {
        "name" : "dbwrite",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-middleware",
            "identity-dbwrite",
            "identity-administrable"
        ]
    },
    {
        "name" : "dbread",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-db-ro",
            "identity-administrable"
        ]
    },
    {
        "name" : "dbmaster",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-db-rw",
            "identity-administrable"
        ]
    },
    {
        "name" : "proxy",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-proxy",
            "identity-administrable"
        ]
    },
    {
        "name" : "admin",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-admin"
        ]
    }
]
'''
    desired_launch_configuration_json['dev'] = '''
[
    {
        "name" : "webhead",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-frontend",
            "identity-administrable"
        ]
    },
    {
        "name" : "bigtent",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-frontend",
            "identity-administrable"
        ]
    },
    {
        "name" : "keysign",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-middleware",
            "identity-administrable"
        ]
    },
    {
        "name" : "dbwrite",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-middleware",
            "identity-dbwrite",
            "identity-administrable"
        ]
    },
    {
        "name" : "dbread",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-db-ro",
            "identity-administrable"
        ]
    },
    {
        "name" : "dbmaster",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-db-rw",
            "identity-administrable"
        ]
    },
    {
        "name" : "proxy",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-proxy",
            "identity-administrable"
        ]
    },
    {
        "name" : "admin",
        "image_id" : "ami-5867ec68",
        "key_name" : "svcops-sl62-base-key-us-west-2",
        "security_groups" : 
        [
            "identity-admin"
        ]
    }
]
'''
   
    # auto scale
    import boto.ec2.autoscale
    conn_autoscale = boto.ec2.autoscale.connect_to_region(region)

    # I'm going to combine launch configuration and autoscale group because I don't
    # see us having more than one autoscale group for each launch configuration
    # A scenario where we would need this would be if 
    for launch_configuration in json.loads(desired_launch_configuration_json[stack_type]):
        launch_configuration['name'] = environment + '-' + launch_configuration['name']
        lc = boto.ec2.autoscale.LaunchConfiguration(**launch_configuration)
        conn_autoscale.create_launch_configuration(lc)

        ag = boto.ec2.autoscale.AutoScalingGroup(group_name='my_group', 
                                                 load_balancers=['my-lb'],
                                                 availability_zones=availability_zones,
                                                 launch_config=lc, 
                                                 min_size=4, 
                                                 max_size=8,
                                                 connection=conn_autoscale)
        conn_autoscale.create_auto_scaling_group(ag)

    return stack

def get_secrets():
    example_secrets_json = '''
{
    "identity-dev": {
        "certs": 
        [
            {
                "cert_name" : "wildcard.anosrep.org",
                "cert_body": "-----BEGIN CERTIFICATE-----\nMIIEsjCCApoCAQEwDQYJKoZIhvcNAQEFBQAwIzEhMB8GA1UEAwwYaW50ZXJtZWRp\nYXRlLmV4YW1wbGUuY29tMB4XDTEzMDIyMjIyNDcwOVoXDTE4MDIyMTIyNDcwOVow\nGzEZMBcGA1UEAwwQdGVzdC5leGFtcGxlLmNvbTCCAiIwDQYJKoZIhvcNAQEBBQAD\nggIPADCCAgoCggIBANtN16kUaeySGXtzhF5OZ93Xp1+pA99AkWYdEDLoeEPfpc8A\nnpU0CLg74wLqC0bTTgxj7y689fw315jegFjWsG5GaBk/aFYSCp2NclnjThsGRls/\n5mE5w4lJlK7FurFKNwPYNDFRgsrEhPcFBe/u0UZBHZoefuCgyws1y1Lrds9mvVWn\nEokXPirLHokfy8CTNeASkoEXKnmKtz5DC+RHmacp+nYT8/dGfX2ETiq/Weo9y/yC\nHhFpj1+SvmN/f9ay3+l9hZmiuBHlzJgt5n7xhXMGgz2j8fKZSdz8WDMYITIKQoSN\nKLhrsswyXG12pjdY/UWqbP9YJ+JD22gPOv5/T4tezSr54G6GnBf0fX86SxdVJtiC\nQ5Fq9qk5L+n37YYc4ONixfhcw5C8p/ClAQIt80mAiiuYcNLcN8RJLZnKvvbN4puK\nEAXF2hA7cBFbPAJy9/ms/Revbw3nvU6P80aQrMfyiHlOFKov4QLNwx34XOYa3deL\nLOy6zyxG+JyHXDS59En1e6up7B+lzmcc4IFzX7VbXkpAisllXutzM0uRz/M9M395\nkenGdQDaQ6JLnt9l+tS2iPVAfmG3ZuqAAhfb1B25w7MeQdwqVVWBMexoaX5z1OT+\ngitC1h+oFj/ak4784OYMvQPMi79oztuxZYL88xDhcwWOo73DL+y/zkvI5DbrAgMB\nAAEwDQYJKoZIhvcNAQEFBQADggIBABmZbSGWE5CeLjhyKVuQI6pRZxuIGPu14tvF\nB+zq6elkkPYVs/Z6XLdZZGOORX+qHLTAbdnlAxTbNfE1edMIUvGgVDgm/rMhArF1\n7o9LzqlgMEeJJf2Lzl4p06KNLOILt6DrLEeS2tzZAMeWDQJgPe/mXt9DOtuoP+C0\nynDgn/zlXdAkqI1cUwDG3vTlsbWjjHTDp/3k90Qkgxg+cCwDdKQf59pA3cvgMZOv\nK7U/y1W6iQmekn1j+1XruicHt0yhTSMV/ufmTGBlSnufIc3UbcJqLVLOTK2j70X8\nRIS5NsWZ4Jzt+BJO90QcDFFXwpMWL81080XBtlL5D/3WFkyBnduScHZa6RQtpMIw\nGslP0Z1ECObj4CxAOAxYEQlKtIFbqV6f4NIxNT/Leihx9S5IVVUAhkeAJqoYTr5R\nXzNyhCf0pPCEwlwGzSEMy1IK0eQ2BaNBZSWVMChJW5lpJVU8AMcZ9ye33OywxkSz\n7681ZfRPFcCj0e3EcCCQJuQ69fSpiq4pqveTehwSrr7oxn/BnY0MqVNrkrNKEMwy\nQrl3Z0B8gQrDNnA1CPgWBHl4Bz2ppMYaGGbOhNuGr6mDZPJsmV0nod7UFeAlOa+2\nOQNvs1LqDdlS398Nh8bhl00gkTiUIsf3I9TTmV7QGa0dS99W1pKtm3Tka831AreH\n9PZH15Pd\n-----END CERTIFICATE-----",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----\n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\n-----END RSA PRIVATE KEY-----",
                "cert_chain": "-----BEGIN CERTIFICATE-----\nMIIEsDCCApgCAQEwDQYJKoZIhvcNAQEFBQAwGTEXMBUGA1UEAwwOY2EuZXhhbXBs\nZS5jb20wHhcNMTMwMjIyMjI0NTU1WhcNMTgwMjIxMjI0NTU1WjAjMSEwHwYDVQQD\nDBhpbnRlcm1lZGlhdGUuZXhhbXBsZS5jb20wggIiMA0GCSqGSIb3DQEBAQUAA4IC\nDwAwggIKAoICAQDEAB/+wPqHvN4IdUG9c7+2mD3SqI+BwQCMHF+rSzkcun7bYAqc\ncatDme5ErFuaMtgUPC4Q+zLCLHL1GT0lRjZV++4JrlnoZh2M7175Z9Y814UQJd7D\nxPgH+0c3H+BqgwBvW917gvNhl8vRFabXEHgzgErBiXbg9GS0eF/Z5Ywz7jf0EmQF\nlc9VcnzPAPTxW1pFKj9/50rh7OVW2BsWi/HOtN68K5hB+mKDkBgWu9fbHG6P/Arc\neVFKZraMN+OQ0nFoESzE+k0H1oQLGkkhYdES1hJJA0OK7qYAutHTMtwHxfZEvr+e\nhf4pAEMFTzqiieVAJ1C07DY8vwLqjdkNzjShkkAlI1ghLaFqeLU2Pr5PjC020qr4\n4vEHa646uBitnweQ6UMpoy/6MrqFVDAwyLazL80DC5cgWH72vYewoyOvJ5/5n7rM\nu2ZXsVyVS8YngbKm15nsZI8fVl1nbe/yO84EG3BdHKNeyRFfZQN9J2Xn6VXw8+Gb\ngButAvFnTIA1Y6hAP2k97OBggmHuCWI6NydB44fe88/k3gs/PmrampBIEPTnscnH\nvd7DkduFz5weAJOLKoyPHDihaKRz6Di9icCi4NRVzlz6slUQlwZlEOdS1q4B9dB+\nB3M1yCa3Fnye6Sn/rnelQGE39QErAN7VY4wgiRwJshSQWgyJn0H5MpzryQIDAQAB\nMA0GCSqGSIb3DQEBBQUAA4ICAQANYGNHRjDO+w+X+Ud2ait28WTPbXofvhR8mZab\n7f3lbMevXUQH5ZKw+G7vsy1ujT/tnLqc+sKaZnDS6sgw9TFG7ZPMiwmibaNiWSrz\nWYadfpPrxfN9QEHh7eJvQq9Z8ShlBaBPQHn6pBBzrO/D8IbwqYWQh9/IRfrB/+jt\nXCgGFswIBF4bKbqvFMYfp59Z/IJ6veVbjtWBSHK8GyFr65HxIsFNM36h1mZZCs6B\n4CPSG+iUke2tmEOl7sV8559ktjdlcHMARzYiF8KVgfXmw+EUtjuQ0Nr22c1pEgoB\npOSmvloWKNTEVZElKRVcIymVMw8BxlIFza7xYsnba+tOBffHp2Xjk2GaWdw7PoR8\nl6hY3vRUzYR9yYB5tQeptbOKctpdInjAylCSJxnBOabcIP6Ws28wPBQ01qMlw4NV\nS5yj3+AzzCBhUS7Fy68/3gWGXJFAcQwOP68exLPcYSQJosEv4UzQeHztgIQSVffG\nxmF/sbm57P2udKgCxWzaTiB1KkGGXgQ1RPIxU8eOQM3XswsXYr2HqR/W4Q2i5sDs\nVst92TGEHkqwI88yUF+tXu0mI198pWuh7svsM+m4YGNMQ16gbr1HR4rVruHv5760\nNqqj9fH92j1WaJ8GW4XQy0NJgKSBuJzpOJf5Y8VbHGT4W3BA7y5trtXieskyGSUj\nsvHoEQ==\n-----END CERTIFICATE-----"
            },
            {
                "cert_name" : "wildcard.login.anosrep.org",
                "cert_body": "-----BEGIN CERTIFICATE-----\nMIIEsjCCApoCAQEwDQYJKoZIhvcNAQEFBQAwIzEhMB8GA1UEAwwYaW50ZXJtZWRp\nYXRlLmV4YW1wbGUuY29tMB4XDTEzMDIyMjIyNDcwOVoXDTE4MDIyMTIyNDcwOVow\nGzEZMBcGA1UEAwwQdGVzdC5leGFtcGxlLmNvbTCCAiIwDQYJKoZIhvcNAQEBBQAD\nggIPADCCAgoCggIBANtN16kUaeySGXtzhF5OZ93Xp1+pA99AkWYdEDLoeEPfpc8A\nnpU0CLg74wLqC0bTTgxj7y689fw315jegFjWsG5GaBk/aFYSCp2NclnjThsGRls/\n5mE5w4lJlK7FurFKNwPYNDFRgsrEhPcFBe/u0UZBHZoefuCgyws1y1Lrds9mvVWn\nEokXPirLHokfy8CTNeASkoEXKnmKtz5DC+RHmacp+nYT8/dGfX2ETiq/Weo9y/yC\nHhFpj1+SvmN/f9ay3+l9hZmiuBHlzJgt5n7xhXMGgz2j8fKZSdz8WDMYITIKQoSN\nKLhrsswyXG12pjdY/UWqbP9YJ+JD22gPOv5/T4tezSr54G6GnBf0fX86SxdVJtiC\nQ5Fq9qk5L+n37YYc4ONixfhcw5C8p/ClAQIt80mAiiuYcNLcN8RJLZnKvvbN4puK\nEAXF2hA7cBFbPAJy9/ms/Revbw3nvU6P80aQrMfyiHlOFKov4QLNwx34XOYa3deL\nLOy6zyxG+JyHXDS59En1e6up7B+lzmcc4IFzX7VbXkpAisllXutzM0uRz/M9M395\nkenGdQDaQ6JLnt9l+tS2iPVAfmG3ZuqAAhfb1B25w7MeQdwqVVWBMexoaX5z1OT+\ngitC1h+oFj/ak4784OYMvQPMi79oztuxZYL88xDhcwWOo73DL+y/zkvI5DbrAgMB\nAAEwDQYJKoZIhvcNAQEFBQADggIBABmZbSGWE5CeLjhyKVuQI6pRZxuIGPu14tvF\nB+zq6elkkPYVs/Z6XLdZZGOORX+qHLTAbdnlAxTbNfE1edMIUvGgVDgm/rMhArF1\n7o9LzqlgMEeJJf2Lzl4p06KNLOILt6DrLEeS2tzZAMeWDQJgPe/mXt9DOtuoP+C0\nynDgn/zlXdAkqI1cUwDG3vTlsbWjjHTDp/3k90Qkgxg+cCwDdKQf59pA3cvgMZOv\nK7U/y1W6iQmekn1j+1XruicHt0yhTSMV/ufmTGBlSnufIc3UbcJqLVLOTK2j70X8\nRIS5NsWZ4Jzt+BJO90QcDFFXwpMWL81080XBtlL5D/3WFkyBnduScHZa6RQtpMIw\nGslP0Z1ECObj4CxAOAxYEQlKtIFbqV6f4NIxNT/Leihx9S5IVVUAhkeAJqoYTr5R\nXzNyhCf0pPCEwlwGzSEMy1IK0eQ2BaNBZSWVMChJW5lpJVU8AMcZ9ye33OywxkSz\n7681ZfRPFcCj0e3EcCCQJuQ69fSpiq4pqveTehwSrr7oxn/BnY0MqVNrkrNKEMwy\nQrl3Z0B8gQrDNnA1CPgWBHl4Bz2ppMYaGGbOhNuGr6mDZPJsmV0nod7UFeAlOa+2\nOQNvs1LqDdlS398Nh8bhl00gkTiUIsf3I9TTmV7QGa0dS99W1pKtm3Tka831AreH\n9PZH15Pd\n-----END CERTIFICATE-----",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----\n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\n-----END RSA PRIVATE KEY-----",
                "cert_chain": "-----BEGIN CERTIFICATE-----\nMIIEsDCCApgCAQEwDQYJKoZIhvcNAQEFBQAwGTEXMBUGA1UEAwwOY2EuZXhhbXBs\nZS5jb20wHhcNMTMwMjIyMjI0NTU1WhcNMTgwMjIxMjI0NTU1WjAjMSEwHwYDVQQD\nDBhpbnRlcm1lZGlhdGUuZXhhbXBsZS5jb20wggIiMA0GCSqGSIb3DQEBAQUAA4IC\nDwAwggIKAoICAQDEAB/+wPqHvN4IdUG9c7+2mD3SqI+BwQCMHF+rSzkcun7bYAqc\ncatDme5ErFuaMtgUPC4Q+zLCLHL1GT0lRjZV++4JrlnoZh2M7175Z9Y814UQJd7D\nxPgH+0c3H+BqgwBvW917gvNhl8vRFabXEHgzgErBiXbg9GS0eF/Z5Ywz7jf0EmQF\nlc9VcnzPAPTxW1pFKj9/50rh7OVW2BsWi/HOtN68K5hB+mKDkBgWu9fbHG6P/Arc\neVFKZraMN+OQ0nFoESzE+k0H1oQLGkkhYdES1hJJA0OK7qYAutHTMtwHxfZEvr+e\nhf4pAEMFTzqiieVAJ1C07DY8vwLqjdkNzjShkkAlI1ghLaFqeLU2Pr5PjC020qr4\n4vEHa646uBitnweQ6UMpoy/6MrqFVDAwyLazL80DC5cgWH72vYewoyOvJ5/5n7rM\nu2ZXsVyVS8YngbKm15nsZI8fVl1nbe/yO84EG3BdHKNeyRFfZQN9J2Xn6VXw8+Gb\ngButAvFnTIA1Y6hAP2k97OBggmHuCWI6NydB44fe88/k3gs/PmrampBIEPTnscnH\nvd7DkduFz5weAJOLKoyPHDihaKRz6Di9icCi4NRVzlz6slUQlwZlEOdS1q4B9dB+\nB3M1yCa3Fnye6Sn/rnelQGE39QErAN7VY4wgiRwJshSQWgyJn0H5MpzryQIDAQAB\nMA0GCSqGSIb3DQEBBQUAA4ICAQANYGNHRjDO+w+X+Ud2ait28WTPbXofvhR8mZab\n7f3lbMevXUQH5ZKw+G7vsy1ujT/tnLqc+sKaZnDS6sgw9TFG7ZPMiwmibaNiWSrz\nWYadfpPrxfN9QEHh7eJvQq9Z8ShlBaBPQHn6pBBzrO/D8IbwqYWQh9/IRfrB/+jt\nXCgGFswIBF4bKbqvFMYfp59Z/IJ6veVbjtWBSHK8GyFr65HxIsFNM36h1mZZCs6B\n4CPSG+iUke2tmEOl7sV8559ktjdlcHMARzYiF8KVgfXmw+EUtjuQ0Nr22c1pEgoB\npOSmvloWKNTEVZElKRVcIymVMw8BxlIFza7xYsnba+tOBffHp2Xjk2GaWdw7PoR8\nl6hY3vRUzYR9yYB5tQeptbOKctpdInjAylCSJxnBOabcIP6Ws28wPBQ01qMlw4NV\nS5yj3+AzzCBhUS7Fy68/3gWGXJFAcQwOP68exLPcYSQJosEv4UzQeHztgIQSVffG\nxmF/sbm57P2udKgCxWzaTiB1KkGGXgQ1RPIxU8eOQM3XswsXYr2HqR/W4Q2i5sDs\nVst92TGEHkqwI88yUF+tXu0mI198pWuh7svsM+m4YGNMQ16gbr1HR4rVruHv5760\nNqqj9fH92j1WaJ8GW4XQy0NJgKSBuJzpOJf5Y8VbHGT4W3BA7y5trtXieskyGSUj\nsvHoEQ==\n-----END CERTIFICATE-----"
            },
            {
                "cert_name" : "wildcard.diresworb.org",
                "cert_body": "-----BEGIN CERTIFICATE-----\nMIIEsjCCApoCAQEwDQYJKoZIhvcNAQEFBQAwIzEhMB8GA1UEAwwYaW50ZXJtZWRp\nYXRlLmV4YW1wbGUuY29tMB4XDTEzMDIyMjIyNDcwOVoXDTE4MDIyMTIyNDcwOVow\nGzEZMBcGA1UEAwwQdGVzdC5leGFtcGxlLmNvbTCCAiIwDQYJKoZIhvcNAQEBBQAD\nggIPADCCAgoCggIBANtN16kUaeySGXtzhF5OZ93Xp1+pA99AkWYdEDLoeEPfpc8A\nnpU0CLg74wLqC0bTTgxj7y689fw315jegFjWsG5GaBk/aFYSCp2NclnjThsGRls/\n5mE5w4lJlK7FurFKNwPYNDFRgsrEhPcFBe/u0UZBHZoefuCgyws1y1Lrds9mvVWn\nEokXPirLHokfy8CTNeASkoEXKnmKtz5DC+RHmacp+nYT8/dGfX2ETiq/Weo9y/yC\nHhFpj1+SvmN/f9ay3+l9hZmiuBHlzJgt5n7xhXMGgz2j8fKZSdz8WDMYITIKQoSN\nKLhrsswyXG12pjdY/UWqbP9YJ+JD22gPOv5/T4tezSr54G6GnBf0fX86SxdVJtiC\nQ5Fq9qk5L+n37YYc4ONixfhcw5C8p/ClAQIt80mAiiuYcNLcN8RJLZnKvvbN4puK\nEAXF2hA7cBFbPAJy9/ms/Revbw3nvU6P80aQrMfyiHlOFKov4QLNwx34XOYa3deL\nLOy6zyxG+JyHXDS59En1e6up7B+lzmcc4IFzX7VbXkpAisllXutzM0uRz/M9M395\nkenGdQDaQ6JLnt9l+tS2iPVAfmG3ZuqAAhfb1B25w7MeQdwqVVWBMexoaX5z1OT+\ngitC1h+oFj/ak4784OYMvQPMi79oztuxZYL88xDhcwWOo73DL+y/zkvI5DbrAgMB\nAAEwDQYJKoZIhvcNAQEFBQADggIBABmZbSGWE5CeLjhyKVuQI6pRZxuIGPu14tvF\nB+zq6elkkPYVs/Z6XLdZZGOORX+qHLTAbdnlAxTbNfE1edMIUvGgVDgm/rMhArF1\n7o9LzqlgMEeJJf2Lzl4p06KNLOILt6DrLEeS2tzZAMeWDQJgPe/mXt9DOtuoP+C0\nynDgn/zlXdAkqI1cUwDG3vTlsbWjjHTDp/3k90Qkgxg+cCwDdKQf59pA3cvgMZOv\nK7U/y1W6iQmekn1j+1XruicHt0yhTSMV/ufmTGBlSnufIc3UbcJqLVLOTK2j70X8\nRIS5NsWZ4Jzt+BJO90QcDFFXwpMWL81080XBtlL5D/3WFkyBnduScHZa6RQtpMIw\nGslP0Z1ECObj4CxAOAxYEQlKtIFbqV6f4NIxNT/Leihx9S5IVVUAhkeAJqoYTr5R\nXzNyhCf0pPCEwlwGzSEMy1IK0eQ2BaNBZSWVMChJW5lpJVU8AMcZ9ye33OywxkSz\n7681ZfRPFcCj0e3EcCCQJuQ69fSpiq4pqveTehwSrr7oxn/BnY0MqVNrkrNKEMwy\nQrl3Z0B8gQrDNnA1CPgWBHl4Bz2ppMYaGGbOhNuGr6mDZPJsmV0nod7UFeAlOa+2\nOQNvs1LqDdlS398Nh8bhl00gkTiUIsf3I9TTmV7QGa0dS99W1pKtm3Tka831AreH\n9PZH15Pd\n-----END CERTIFICATE-----",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----\n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\n-----END RSA PRIVATE KEY-----",
                "cert_chain": "-----BEGIN CERTIFICATE-----\nMIIEsDCCApgCAQEwDQYJKoZIhvcNAQEFBQAwGTEXMBUGA1UEAwwOY2EuZXhhbXBs\nZS5jb20wHhcNMTMwMjIyMjI0NTU1WhcNMTgwMjIxMjI0NTU1WjAjMSEwHwYDVQQD\nDBhpbnRlcm1lZGlhdGUuZXhhbXBsZS5jb20wggIiMA0GCSqGSIb3DQEBAQUAA4IC\nDwAwggIKAoICAQDEAB/+wPqHvN4IdUG9c7+2mD3SqI+BwQCMHF+rSzkcun7bYAqc\ncatDme5ErFuaMtgUPC4Q+zLCLHL1GT0lRjZV++4JrlnoZh2M7175Z9Y814UQJd7D\nxPgH+0c3H+BqgwBvW917gvNhl8vRFabXEHgzgErBiXbg9GS0eF/Z5Ywz7jf0EmQF\nlc9VcnzPAPTxW1pFKj9/50rh7OVW2BsWi/HOtN68K5hB+mKDkBgWu9fbHG6P/Arc\neVFKZraMN+OQ0nFoESzE+k0H1oQLGkkhYdES1hJJA0OK7qYAutHTMtwHxfZEvr+e\nhf4pAEMFTzqiieVAJ1C07DY8vwLqjdkNzjShkkAlI1ghLaFqeLU2Pr5PjC020qr4\n4vEHa646uBitnweQ6UMpoy/6MrqFVDAwyLazL80DC5cgWH72vYewoyOvJ5/5n7rM\nu2ZXsVyVS8YngbKm15nsZI8fVl1nbe/yO84EG3BdHKNeyRFfZQN9J2Xn6VXw8+Gb\ngButAvFnTIA1Y6hAP2k97OBggmHuCWI6NydB44fe88/k3gs/PmrampBIEPTnscnH\nvd7DkduFz5weAJOLKoyPHDihaKRz6Di9icCi4NRVzlz6slUQlwZlEOdS1q4B9dB+\nB3M1yCa3Fnye6Sn/rnelQGE39QErAN7VY4wgiRwJshSQWgyJn0H5MpzryQIDAQAB\nMA0GCSqGSIb3DQEBBQUAA4ICAQANYGNHRjDO+w+X+Ud2ait28WTPbXofvhR8mZab\n7f3lbMevXUQH5ZKw+G7vsy1ujT/tnLqc+sKaZnDS6sgw9TFG7ZPMiwmibaNiWSrz\nWYadfpPrxfN9QEHh7eJvQq9Z8ShlBaBPQHn6pBBzrO/D8IbwqYWQh9/IRfrB/+jt\nXCgGFswIBF4bKbqvFMYfp59Z/IJ6veVbjtWBSHK8GyFr65HxIsFNM36h1mZZCs6B\n4CPSG+iUke2tmEOl7sV8559ktjdlcHMARzYiF8KVgfXmw+EUtjuQ0Nr22c1pEgoB\npOSmvloWKNTEVZElKRVcIymVMw8BxlIFza7xYsnba+tOBffHp2Xjk2GaWdw7PoR8\nl6hY3vRUzYR9yYB5tQeptbOKctpdInjAylCSJxnBOabcIP6Ws28wPBQ01qMlw4NV\nS5yj3+AzzCBhUS7Fy68/3gWGXJFAcQwOP68exLPcYSQJosEv4UzQeHztgIQSVffG\nxmF/sbm57P2udKgCxWzaTiB1KkGGXgQ1RPIxU8eOQM3XswsXYr2HqR/W4Q2i5sDs\nVst92TGEHkqwI88yUF+tXu0mI198pWuh7svsM+m4YGNMQ16gbr1HR4rVruHv5760\nNqqj9fH92j1WaJ8GW4XQy0NJgKSBuJzpOJf5Y8VbHGT4W3BA7y5trtXieskyGSUj\nsvHoEQ==\n-----END CERTIFICATE-----"
            }
        ]
    },
    "identity-prod": {
        "certs": 
        [
            {
                "cert_name" : "multisan-www.persona.org",
                "cert_body": "-----BEGIN CERTIFICATE-----\nMIIEsjCCApoCAQEwDQYJKoZIhvcNAQEFBQAwIzEhMB8GA1UEAwwYaW50ZXJtZWRp\nYXRlLmV4YW1wbGUuY29tMB4XDTEzMDIyMjIyNDcwOVoXDTE4MDIyMTIyNDcwOVow\nGzEZMBcGA1UEAwwQdGVzdC5leGFtcGxlLmNvbTCCAiIwDQYJKoZIhvcNAQEBBQAD\nggIPADCCAgoCggIBANtN16kUaeySGXtzhF5OZ93Xp1+pA99AkWYdEDLoeEPfpc8A\nnpU0CLg74wLqC0bTTgxj7y689fw315jegFjWsG5GaBk/aFYSCp2NclnjThsGRls/\n5mE5w4lJlK7FurFKNwPYNDFRgsrEhPcFBe/u0UZBHZoefuCgyws1y1Lrds9mvVWn\nEokXPirLHokfy8CTNeASkoEXKnmKtz5DC+RHmacp+nYT8/dGfX2ETiq/Weo9y/yC\nHhFpj1+SvmN/f9ay3+l9hZmiuBHlzJgt5n7xhXMGgz2j8fKZSdz8WDMYITIKQoSN\nKLhrsswyXG12pjdY/UWqbP9YJ+JD22gPOv5/T4tezSr54G6GnBf0fX86SxdVJtiC\nQ5Fq9qk5L+n37YYc4ONixfhcw5C8p/ClAQIt80mAiiuYcNLcN8RJLZnKvvbN4puK\nEAXF2hA7cBFbPAJy9/ms/Revbw3nvU6P80aQrMfyiHlOFKov4QLNwx34XOYa3deL\nLOy6zyxG+JyHXDS59En1e6up7B+lzmcc4IFzX7VbXkpAisllXutzM0uRz/M9M395\nkenGdQDaQ6JLnt9l+tS2iPVAfmG3ZuqAAhfb1B25w7MeQdwqVVWBMexoaX5z1OT+\ngitC1h+oFj/ak4784OYMvQPMi79oztuxZYL88xDhcwWOo73DL+y/zkvI5DbrAgMB\nAAEwDQYJKoZIhvcNAQEFBQADggIBABmZbSGWE5CeLjhyKVuQI6pRZxuIGPu14tvF\nB+zq6elkkPYVs/Z6XLdZZGOORX+qHLTAbdnlAxTbNfE1edMIUvGgVDgm/rMhArF1\n7o9LzqlgMEeJJf2Lzl4p06KNLOILt6DrLEeS2tzZAMeWDQJgPe/mXt9DOtuoP+C0\nynDgn/zlXdAkqI1cUwDG3vTlsbWjjHTDp/3k90Qkgxg+cCwDdKQf59pA3cvgMZOv\nK7U/y1W6iQmekn1j+1XruicHt0yhTSMV/ufmTGBlSnufIc3UbcJqLVLOTK2j70X8\nRIS5NsWZ4Jzt+BJO90QcDFFXwpMWL81080XBtlL5D/3WFkyBnduScHZa6RQtpMIw\nGslP0Z1ECObj4CxAOAxYEQlKtIFbqV6f4NIxNT/Leihx9S5IVVUAhkeAJqoYTr5R\nXzNyhCf0pPCEwlwGzSEMy1IK0eQ2BaNBZSWVMChJW5lpJVU8AMcZ9ye33OywxkSz\n7681ZfRPFcCj0e3EcCCQJuQ69fSpiq4pqveTehwSrr7oxn/BnY0MqVNrkrNKEMwy\nQrl3Z0B8gQrDNnA1CPgWBHl4Bz2ppMYaGGbOhNuGr6mDZPJsmV0nod7UFeAlOa+2\nOQNvs1LqDdlS398Nh8bhl00gkTiUIsf3I9TTmV7QGa0dS99W1pKtm3Tka831AreH\n9PZH15Pd\n-----END CERTIFICATE-----",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----\n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\n-----END RSA PRIVATE KEY-----",
                "cert_chain": "-----BEGIN CERTIFICATE-----\nMIIEsDCCApgCAQEwDQYJKoZIhvcNAQEFBQAwGTEXMBUGA1UEAwwOY2EuZXhhbXBs\nZS5jb20wHhcNMTMwMjIyMjI0NTU1WhcNMTgwMjIxMjI0NTU1WjAjMSEwHwYDVQQD\nDBhpbnRlcm1lZGlhdGUuZXhhbXBsZS5jb20wggIiMA0GCSqGSIb3DQEBAQUAA4IC\nDwAwggIKAoICAQDEAB/+wPqHvN4IdUG9c7+2mD3SqI+BwQCMHF+rSzkcun7bYAqc\ncatDme5ErFuaMtgUPC4Q+zLCLHL1GT0lRjZV++4JrlnoZh2M7175Z9Y814UQJd7D\nxPgH+0c3H+BqgwBvW917gvNhl8vRFabXEHgzgErBiXbg9GS0eF/Z5Ywz7jf0EmQF\nlc9VcnzPAPTxW1pFKj9/50rh7OVW2BsWi/HOtN68K5hB+mKDkBgWu9fbHG6P/Arc\neVFKZraMN+OQ0nFoESzE+k0H1oQLGkkhYdES1hJJA0OK7qYAutHTMtwHxfZEvr+e\nhf4pAEMFTzqiieVAJ1C07DY8vwLqjdkNzjShkkAlI1ghLaFqeLU2Pr5PjC020qr4\n4vEHa646uBitnweQ6UMpoy/6MrqFVDAwyLazL80DC5cgWH72vYewoyOvJ5/5n7rM\nu2ZXsVyVS8YngbKm15nsZI8fVl1nbe/yO84EG3BdHKNeyRFfZQN9J2Xn6VXw8+Gb\ngButAvFnTIA1Y6hAP2k97OBggmHuCWI6NydB44fe88/k3gs/PmrampBIEPTnscnH\nvd7DkduFz5weAJOLKoyPHDihaKRz6Di9icCi4NRVzlz6slUQlwZlEOdS1q4B9dB+\nB3M1yCa3Fnye6Sn/rnelQGE39QErAN7VY4wgiRwJshSQWgyJn0H5MpzryQIDAQAB\nMA0GCSqGSIb3DQEBBQUAA4ICAQANYGNHRjDO+w+X+Ud2ait28WTPbXofvhR8mZab\n7f3lbMevXUQH5ZKw+G7vsy1ujT/tnLqc+sKaZnDS6sgw9TFG7ZPMiwmibaNiWSrz\nWYadfpPrxfN9QEHh7eJvQq9Z8ShlBaBPQHn6pBBzrO/D8IbwqYWQh9/IRfrB/+jt\nXCgGFswIBF4bKbqvFMYfp59Z/IJ6veVbjtWBSHK8GyFr65HxIsFNM36h1mZZCs6B\n4CPSG+iUke2tmEOl7sV8559ktjdlcHMARzYiF8KVgfXmw+EUtjuQ0Nr22c1pEgoB\npOSmvloWKNTEVZElKRVcIymVMw8BxlIFza7xYsnba+tOBffHp2Xjk2GaWdw7PoR8\nl6hY3vRUzYR9yYB5tQeptbOKctpdInjAylCSJxnBOabcIP6Ws28wPBQ01qMlw4NV\nS5yj3+AzzCBhUS7Fy68/3gWGXJFAcQwOP68exLPcYSQJosEv4UzQeHztgIQSVffG\nxmF/sbm57P2udKgCxWzaTiB1KkGGXgQ1RPIxU8eOQM3XswsXYr2HqR/W4Q2i5sDs\nVst92TGEHkqwI88yUF+tXu0mI198pWuh7svsM+m4YGNMQ16gbr1HR4rVruHv5760\nNqqj9fH92j1WaJ8GW4XQy0NJgKSBuJzpOJf5Y8VbHGT4W3BA7y5trtXieskyGSUj\nsvHoEQ==\n-----END CERTIFICATE-----"
            },
            {
                "cert_name" : "www.browserid.org",
                "cert_body": "-----BEGIN CERTIFICATE-----\nMIIEsjCCApoCAQEwDQYJKoZIhvcNAQEFBQAwIzEhMB8GA1UEAwwYaW50ZXJtZWRp\nYXRlLmV4YW1wbGUuY29tMB4XDTEzMDIyMjIyNDcwOVoXDTE4MDIyMTIyNDcwOVow\nGzEZMBcGA1UEAwwQdGVzdC5leGFtcGxlLmNvbTCCAiIwDQYJKoZIhvcNAQEBBQAD\nggIPADCCAgoCggIBANtN16kUaeySGXtzhF5OZ93Xp1+pA99AkWYdEDLoeEPfpc8A\nnpU0CLg74wLqC0bTTgxj7y689fw315jegFjWsG5GaBk/aFYSCp2NclnjThsGRls/\n5mE5w4lJlK7FurFKNwPYNDFRgsrEhPcFBe/u0UZBHZoefuCgyws1y1Lrds9mvVWn\nEokXPirLHokfy8CTNeASkoEXKnmKtz5DC+RHmacp+nYT8/dGfX2ETiq/Weo9y/yC\nHhFpj1+SvmN/f9ay3+l9hZmiuBHlzJgt5n7xhXMGgz2j8fKZSdz8WDMYITIKQoSN\nKLhrsswyXG12pjdY/UWqbP9YJ+JD22gPOv5/T4tezSr54G6GnBf0fX86SxdVJtiC\nQ5Fq9qk5L+n37YYc4ONixfhcw5C8p/ClAQIt80mAiiuYcNLcN8RJLZnKvvbN4puK\nEAXF2hA7cBFbPAJy9/ms/Revbw3nvU6P80aQrMfyiHlOFKov4QLNwx34XOYa3deL\nLOy6zyxG+JyHXDS59En1e6up7B+lzmcc4IFzX7VbXkpAisllXutzM0uRz/M9M395\nkenGdQDaQ6JLnt9l+tS2iPVAfmG3ZuqAAhfb1B25w7MeQdwqVVWBMexoaX5z1OT+\ngitC1h+oFj/ak4784OYMvQPMi79oztuxZYL88xDhcwWOo73DL+y/zkvI5DbrAgMB\nAAEwDQYJKoZIhvcNAQEFBQADggIBABmZbSGWE5CeLjhyKVuQI6pRZxuIGPu14tvF\nB+zq6elkkPYVs/Z6XLdZZGOORX+qHLTAbdnlAxTbNfE1edMIUvGgVDgm/rMhArF1\n7o9LzqlgMEeJJf2Lzl4p06KNLOILt6DrLEeS2tzZAMeWDQJgPe/mXt9DOtuoP+C0\nynDgn/zlXdAkqI1cUwDG3vTlsbWjjHTDp/3k90Qkgxg+cCwDdKQf59pA3cvgMZOv\nK7U/y1W6iQmekn1j+1XruicHt0yhTSMV/ufmTGBlSnufIc3UbcJqLVLOTK2j70X8\nRIS5NsWZ4Jzt+BJO90QcDFFXwpMWL81080XBtlL5D/3WFkyBnduScHZa6RQtpMIw\nGslP0Z1ECObj4CxAOAxYEQlKtIFbqV6f4NIxNT/Leihx9S5IVVUAhkeAJqoYTr5R\nXzNyhCf0pPCEwlwGzSEMy1IK0eQ2BaNBZSWVMChJW5lpJVU8AMcZ9ye33OywxkSz\n7681ZfRPFcCj0e3EcCCQJuQ69fSpiq4pqveTehwSrr7oxn/BnY0MqVNrkrNKEMwy\nQrl3Z0B8gQrDNnA1CPgWBHl4Bz2ppMYaGGbOhNuGr6mDZPJsmV0nod7UFeAlOa+2\nOQNvs1LqDdlS398Nh8bhl00gkTiUIsf3I9TTmV7QGa0dS99W1pKtm3Tka831AreH\n9PZH15Pd\n-----END CERTIFICATE-----",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIJJwIBAAKCAgEA203XqRRp7JIZe3OEXk5n3denX6kD30CRZh0QMuh4Q9+lzwCe\nlTQIuDvjAuoLRtNODGPvLrz1/DfXmN6AWNawbkZoGT9oVhIKnY1yWeNOGwZGWz/m\nYTnDiUmUrsW6sUo3A9g0MVGCysSE9wUF7+7RRkEdmh5+4KDLCzXLUut2z2a9VacS\niRc+KsseiR/LwJM14BKSgRcqeYq3PkML5EeZpyn6dhPz90Z9fYROKr9Z6j3L/IIe\nEWmPX5K+Y39/1rLf6X2FmaK4EeXMmC3mfvGFcwaDPaPx8plJ3PxYMxghMgpChI0o\nuGuyzDJcbXamN1j9Raps/1gn4kPbaA86/n9Pi17NKvngboacF/R9fzpLF1Um2IJD\nkWr2qTkv6ffthhzg42LF+FzDkLyn8KUBAi3zSYCKK5hw0tw3xEktmcq+9s3im4oQ\nBcXaEDtwEVs8AnL3+az9F69vDee9To/zRpCsx/KIeU4Uqi/hAs3DHfhc5hrd14ss\n7LrPLEb4nIdcNLn0SfV7q6nsH6XOZxzggXNftVteSkCKyWVe63MzS5HP8z0zf3mR\n6cZ1ANpDokue32X61LaI9UB+Ybdm6oACF9vUHbnDsx5B3CpVVYEx7GhpfnPU5P6C\nK0LWH6gWP9qTjvzg5gy9A8yLv2jO27FlgvzzEOFzBY6jvcMv7L/OS8jkNusCAwEA\nAQKCAgBKsSN/mc1N3qDBNCHkQM4Nd7Kw2Q7Rjds3rTRkMlsrutNtQmfAp31EyljS\nGEaI89UEUVEYWRFqutY6YaXTHCPxGxe/aaIulmx5JsDIrqtedu+lioj7mkHn02DJ\nedzRH1bHf26fUYS7bN1giJxyEKPESs87O6G4/erJwaOjdUD8+KAJuSKOAJWS26Vl\nzKeHyluyGoE9aFd2F/G7SfiV4nEJxzlf2AHiuWZqRpKc6plEN5HvSZ3WDl7fjUo8\n9yLiTAAJNVA4eHw61EqvlgqIN9hcyd4PM3RnTSAkHOopVNGRin8HSFCTJ1M5SvnB\n6oRIG43/mUEQYsUKwlPLCEzuewvq6WowGG+p8XygYGZC+hSpwDq0XfyEvZhfK059\nxdNVHNj4xPevgQiL4I8xmy7UQoFleVhZ84CWuL1EHYsmPlbsd9nGR2uVg3yFa84m\n/Pw2Zveo2a69X7IKiSlSUiHG+H3hzxlfd7tcjMm75T8WSS3Y0G5h9BW2W40EA45q\nPYOhHEHZ8YtdkrsmqlYWrz+1t83StMyZ32m1ejhxpsMfEQaWHnlFcB7xz9WXiTsC\nfyBJeXH09j57l8pAMNia5m3DmUBk7Sj3+ulDUCRReat2Dbi2BGRLq0Kp0bhyK7Tc\n93T87AvH30Gd89YPiSjt/gKxEpAP6hAh8ZhLaaINGaKLmsRqsQKCAQEA972m835N\n+YNiz3ufEi8NZiV2HobWHwfHH1E/TTjMqjbzGkfS03MV6nH4SkiI5j1rkf/240sX\n2+id0ReCZ7oACksXhzB426EB16IFgicu3eb9CkR76ai0jmJ23DfvAzve148szdTW\nQP0q8yg/Yb8kJOuwgjonVElTHuYqtPnVanmzO7fvacVC/lIrC8URMVLluld9yrkf\nLiX2uCZmr8hh93QMUg05nHEG2nY3Z/19h2N9Kpgpue0dj7/J3/p28xYGWaj6poEX\nFGv1FM9y5psYrgNKMmWE1sUEVlWDY4OKaffx/WPgD4T2TSj52jatQiK0WQU0/tlr\nMRV8WBhPivDWWQKCAQEA4p1/ECtNBrr7/QfM/95t3UrBm+QP4RwBSfx5Rw/Ysux8\ney48jtSUunsI4H2Bpg77P+RB2k/yA6t0YVz1+8AbK1Z8Hkkobx0wA2aziPHr/H5G\n+VEiZBOxhUKIwW+oIXkwEH0ykX09wY+qCRDv244UX7jwyueePgKOUIqSzromJnFy\nFsw4mLrvFFFRPBmalZKdP/vQq1C4T9vdCIa1YGYyWqmxsMCRlCsMGXDdnLs88Twf\nyx5LZABpqFCM++l2933lrH0/05gZIDzr4BW6JPSsM+rzVO76wsriFlHtH903nFFn\nFRO8+IQjQIEKvWGbdtXiUU7ttSRmb5Zx9/AYme6W4wKCAQBUB4LaMiwWhqb8Qy0I\nSOddjzVKU2fLLKMwjylOcwaQcYTxlA0BZZa4Z6HU6Fdu6MRUyCIgpDbag0MMSdIU\nhrU+yIuZcip8LFdooW8G3215HMEVO3dgILXlWaaBOYObcDI8oTaMNjXZ40UvJqag\n6+lBkKPU+A6g+yHzaBRyQA9QRykxB0lwcdUwWAR7wIL9XOXI16Y2HaZiy8OsYHIS\nC4CXI0iOiCfTVU8CyHgwkH2Eb41j5iq5AqE1QdMiYlz4RK8wuC0UTtLaPWfqgBaz\n+0VauIjxIRf2lOrMscKX/WT0XoI49ShpeyrjrxNYHZWUyhqr2yVHj81Y37XGV7Cb\nKuc5AoIBAHXV66JewbjENg/GpKRP5tTw8Ge9WTx2sXzlWbLH3Kh9K+Vpj3e9tnCZ\nVW5WFLpig+cfK9b3RyL9XpDaI9Z6eCY63GNrKylMBhFer/B/y3QJvaIavEVJsD9Y\n73+WLdjqCUIpt8fLVfd2WrZIJlEGOjXkFuGLOs+HyLS8ucXhKcFHsEmGe89/NJ5e\nAl27+pPYHwiMSl8qpAxyiSbL1TiBK6HVJ15/Y7OmBq6b78B15CSUXPvjjtQ7GrW4\n3PaI2aGrx2e/4RaHulj3FLf61EYvK/P7MfhyI9ZyZMmyZBjzkN0pvu5IyzR2kVYT\nQ6BiRtKuOPaKkjRk7xcLJcwE/uXcGH0CggEAUMW79wx2HMzQL6HNIy4lKBK5M2Iv\nCqOcpx1lAse5Md4Uot9jNKHqOFmZ2CAXSnyPga3+DRnVZ3Ea/8jrqkPXYKVOdgrR\n0QKGWMG55jvfUiwuF6Fdm9MFUXa9WAFVgf091bqcEi22xvDO4/NHde8ImuQny7K9\nPH/1/ww/cyJAbnKDr0+3yrc5eCneTqaqEUoehLeKU7gq+aI3jb/bwUfn65TpzqUb\n5jWSHNV0h9VJgbkf85HvvlB/U9VWgZ0eP1XS+bSKAElst777nXARta1hVFB9MxZK\nECGLH9Awj/Wwt82Cfqfy1oRNwD/m2X5ziTI2ZolLkl/FvsqBroL/puKssw==\n-----END RSA PRIVATE KEY-----",
                "cert_chain": "-----BEGIN CERTIFICATE-----\nMIIEsDCCApgCAQEwDQYJKoZIhvcNAQEFBQAwGTEXMBUGA1UEAwwOY2EuZXhhbXBs\nZS5jb20wHhcNMTMwMjIyMjI0NTU1WhcNMTgwMjIxMjI0NTU1WjAjMSEwHwYDVQQD\nDBhpbnRlcm1lZGlhdGUuZXhhbXBsZS5jb20wggIiMA0GCSqGSIb3DQEBAQUAA4IC\nDwAwggIKAoICAQDEAB/+wPqHvN4IdUG9c7+2mD3SqI+BwQCMHF+rSzkcun7bYAqc\ncatDme5ErFuaMtgUPC4Q+zLCLHL1GT0lRjZV++4JrlnoZh2M7175Z9Y814UQJd7D\nxPgH+0c3H+BqgwBvW917gvNhl8vRFabXEHgzgErBiXbg9GS0eF/Z5Ywz7jf0EmQF\nlc9VcnzPAPTxW1pFKj9/50rh7OVW2BsWi/HOtN68K5hB+mKDkBgWu9fbHG6P/Arc\neVFKZraMN+OQ0nFoESzE+k0H1oQLGkkhYdES1hJJA0OK7qYAutHTMtwHxfZEvr+e\nhf4pAEMFTzqiieVAJ1C07DY8vwLqjdkNzjShkkAlI1ghLaFqeLU2Pr5PjC020qr4\n4vEHa646uBitnweQ6UMpoy/6MrqFVDAwyLazL80DC5cgWH72vYewoyOvJ5/5n7rM\nu2ZXsVyVS8YngbKm15nsZI8fVl1nbe/yO84EG3BdHKNeyRFfZQN9J2Xn6VXw8+Gb\ngButAvFnTIA1Y6hAP2k97OBggmHuCWI6NydB44fe88/k3gs/PmrampBIEPTnscnH\nvd7DkduFz5weAJOLKoyPHDihaKRz6Di9icCi4NRVzlz6slUQlwZlEOdS1q4B9dB+\nB3M1yCa3Fnye6Sn/rnelQGE39QErAN7VY4wgiRwJshSQWgyJn0H5MpzryQIDAQAB\nMA0GCSqGSIb3DQEBBQUAA4ICAQANYGNHRjDO+w+X+Ud2ait28WTPbXofvhR8mZab\n7f3lbMevXUQH5ZKw+G7vsy1ujT/tnLqc+sKaZnDS6sgw9TFG7ZPMiwmibaNiWSrz\nWYadfpPrxfN9QEHh7eJvQq9Z8ShlBaBPQHn6pBBzrO/D8IbwqYWQh9/IRfrB/+jt\nXCgGFswIBF4bKbqvFMYfp59Z/IJ6veVbjtWBSHK8GyFr65HxIsFNM36h1mZZCs6B\n4CPSG+iUke2tmEOl7sV8559ktjdlcHMARzYiF8KVgfXmw+EUtjuQ0Nr22c1pEgoB\npOSmvloWKNTEVZElKRVcIymVMw8BxlIFza7xYsnba+tOBffHp2Xjk2GaWdw7PoR8\nl6hY3vRUzYR9yYB5tQeptbOKctpdInjAylCSJxnBOabcIP6Ws28wPBQ01qMlw4NV\nS5yj3+AzzCBhUS7Fy68/3gWGXJFAcQwOP68exLPcYSQJosEv4UzQeHztgIQSVffG\nxmF/sbm57P2udKgCxWzaTiB1KkGGXgQ1RPIxU8eOQM3XswsXYr2HqR/W4Q2i5sDs\nVst92TGEHkqwI88yUF+tXu0mI198pWuh7svsM+m4YGNMQ16gbr1HR4rVruHv5760\nNqqj9fH92j1WaJ8GW4XQy0NJgKSBuJzpOJf5Y8VbHGT4W3BA7y5trtXieskyGSUj\nsvHoEQ==\n-----END CERTIFICATE-----"
            },
            {
                "cert_name" : "multisan-yahoo.login.persona.org",
                "cert_body": "-----BEGIN CERTIFICATE-----\nMIIEsjCCApoCAQEwDQYJKoZIhvcNAQEFBQAwIzEhMB8GA1UEAwwYaW50ZXJtZWRp\nYXRlLmV4YW1wbGUuY29tMB4XDTEzMDIyMjIyNDcwOVoXDTE4MDIyMTIyNDcwOVow\nGzEZMBcGA1UEAwwQdGVzdC5leGFtcGxlLmNvbTCCAiIwDQYJKoZIhvcNAQEBBQAD\nggIPADCCAgoCggIBANtN16kUaeySGXtzhF5OZ93Xp1+pA99AkWYdEDLoeEPfpc8A\nnpU0CLg74wLqC0bTTgxj7y689fw315jegFjWsG5GaBk/aFYSCp2NclnjThsGRls/\n5mE5w4lJlK7FurFKNwPYNDFRgsrEhPcFBe/u0UZBHZoefuCgyws1y1Lrds9mvVWn\nEokXPirLHokfy8CTNeASkoEXKnmKtz5DC+RHmacp+nYT8/dGfX2ETiq/Weo9y/yC\nHhFpj1+SvmN/f9ay3+l9hZmiuBHlzJgt5n7xhXMGgz2j8fKZSdz8WDMYITIKQoSN\nKLhrsswyXG12pjdY/UWqbP9YJ+JD22gPOv5/T4tezSr54G6GnBf0fX86SxdVJtiC\nQ5Fq9qk5L+n37YYc4ONixfhcw5C8p/ClAQIt80mAiiuYcNLcN8RJLZnKvvbN4puK\nEAXF2hA7cBFbPAJy9/ms/Revbw3nvU6P80aQrMfyiHlOFKov4QLNwx34XOYa3deL\nLOy6zyxG+JyHXDS59En1e6up7B+lzmcc4IFzX7VbXkpAisllXutzM0uRz/M9M395\nkenGdQDaQ6JLnt9l+tS2iPVAfmG3ZuqAAhfb1B25w7MeQdwqVVWBMexoaX5z1OT+\ngitC1h+oFj/ak4784OYMvQPMi79oztuxZYL88xDhcwWOo73DL+y/zkvI5DbrAgMB\nAAEwDQYJKoZIhvcNAQEFBQADggIBABmZbSGWE5CeLjhyKVuQI6pRZxuIGPu14tvF\nB+zq6elkkPYVs/Z6XLdZZGOORX+qHLTAbdnlAxTbNfE1edMIUvGgVDgm/rMhArF1\n7o9LzqlgMEeJJf2Lzl4p06KNLOILt6DrLEeS2tzZAMeWDQJgPe/mXt9DOtuoP+C0\nynDgn/zlXdAkqI1cUwDG3vTlsbWjjHTDp/3k90Qkgxg+cCwDdKQf59pA3cvgMZOv\nK7U/y1W6iQmekn1j+1XruicHt0yhTSMV/ufmTGBlSnufIc3UbcJqLVLOTK2j70X8\nRIS5NsWZ4Jzt+BJO90QcDFFXwpMWL81080XBtlL5D/3WFkyBnduScHZa6RQtpMIw\nGslP0Z1ECObj4CxAOAxYEQlKtIFbqV6f4NIxNT/Leihx9S5IVVUAhkeAJqoYTr5R\nXzNyhCf0pPCEwlwGzSEMy1IK0eQ2BaNBZSWVMChJW5lpJVU8AMcZ9ye33OywxkSz\n7681ZfRPFcCj0e3EcCCQJuQ69fSpiq4pqveTehwSrr7oxn/BnY0MqVNrkrNKEMwy\nQrl3Z0B8gQrDNnA1CPgWBHl4Bz2ppMYaGGbOhNuGr6mDZPJsmV0nod7UFeAlOa+2\nOQNvs1LqDdlS398Nh8bhl00gkTiUIsf3I9TTmV7QGa0dS99W1pKtm3Tka831AreH\n9PZH15Pd\n-----END CERTIFICATE-----",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----\n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\n-----END RSA PRIVATE KEY-----",
                "cert_chain": "-----BEGIN CERTIFICATE-----\nMIIEsDCCApgCAQEwDQYJKoZIhvcNAQEFBQAwGTEXMBUGA1UEAwwOY2EuZXhhbXBs\nZS5jb20wHhcNMTMwMjIyMjI0NTU1WhcNMTgwMjIxMjI0NTU1WjAjMSEwHwYDVQQD\nDBhpbnRlcm1lZGlhdGUuZXhhbXBsZS5jb20wggIiMA0GCSqGSIb3DQEBAQUAA4IC\nDwAwggIKAoICAQDEAB/+wPqHvN4IdUG9c7+2mD3SqI+BwQCMHF+rSzkcun7bYAqc\ncatDme5ErFuaMtgUPC4Q+zLCLHL1GT0lRjZV++4JrlnoZh2M7175Z9Y814UQJd7D\nxPgH+0c3H+BqgwBvW917gvNhl8vRFabXEHgzgErBiXbg9GS0eF/Z5Ywz7jf0EmQF\nlc9VcnzPAPTxW1pFKj9/50rh7OVW2BsWi/HOtN68K5hB+mKDkBgWu9fbHG6P/Arc\neVFKZraMN+OQ0nFoESzE+k0H1oQLGkkhYdES1hJJA0OK7qYAutHTMtwHxfZEvr+e\nhf4pAEMFTzqiieVAJ1C07DY8vwLqjdkNzjShkkAlI1ghLaFqeLU2Pr5PjC020qr4\n4vEHa646uBitnweQ6UMpoy/6MrqFVDAwyLazL80DC5cgWH72vYewoyOvJ5/5n7rM\nu2ZXsVyVS8YngbKm15nsZI8fVl1nbe/yO84EG3BdHKNeyRFfZQN9J2Xn6VXw8+Gb\ngButAvFnTIA1Y6hAP2k97OBggmHuCWI6NydB44fe88/k3gs/PmrampBIEPTnscnH\nvd7DkduFz5weAJOLKoyPHDihaKRz6Di9icCi4NRVzlz6slUQlwZlEOdS1q4B9dB+\nB3M1yCa3Fnye6Sn/rnelQGE39QErAN7VY4wgiRwJshSQWgyJn0H5MpzryQIDAQAB\nMA0GCSqGSIb3DQEBBQUAA4ICAQANYGNHRjDO+w+X+Ud2ait28WTPbXofvhR8mZab\n7f3lbMevXUQH5ZKw+G7vsy1ujT/tnLqc+sKaZnDS6sgw9TFG7ZPMiwmibaNiWSrz\nWYadfpPrxfN9QEHh7eJvQq9Z8ShlBaBPQHn6pBBzrO/D8IbwqYWQh9/IRfrB/+jt\nXCgGFswIBF4bKbqvFMYfp59Z/IJ6veVbjtWBSHK8GyFr65HxIsFNM36h1mZZCs6B\n4CPSG+iUke2tmEOl7sV8559ktjdlcHMARzYiF8KVgfXmw+EUtjuQ0Nr22c1pEgoB\npOSmvloWKNTEVZElKRVcIymVMw8BxlIFza7xYsnba+tOBffHp2Xjk2GaWdw7PoR8\nl6hY3vRUzYR9yYB5tQeptbOKctpdInjAylCSJxnBOabcIP6Ws28wPBQ01qMlw4NV\nS5yj3+AzzCBhUS7Fy68/3gWGXJFAcQwOP68exLPcYSQJosEv4UzQeHztgIQSVffG\nxmF/sbm57P2udKgCxWzaTiB1KkGGXgQ1RPIxU8eOQM3XswsXYr2HqR/W4Q2i5sDs\nVst92TGEHkqwI88yUF+tXu0mI198pWuh7svsM+m4YGNMQ16gbr1HR4rVruHv5760\nNqqj9fH92j1WaJ8GW4XQy0NJgKSBuJzpOJf5Y8VbHGT4W3BA7y5trtXieskyGSUj\nsvHoEQ==\n-----END CERTIFICATE-----"
            }
        ]
    }
}
'''
    secrets_filename = '/home/gene/Documents/identity-secrets.json'
    try:
        with open(secrets_filename, 'rb') as secrets_file:
            logging.debug('loading secrets from %s' % secrets_filename)
            return json.load(secrets_file)
    except IOError as e:
        return json.loads(example_secrets_json)

if __name__ == '__main__':
    secrets = get_secrets()
    path = "/identity/"
    arn_prefix = "arn:aws:iam::351644144250"
    vpcs = one_time_provision(secrets, path)
