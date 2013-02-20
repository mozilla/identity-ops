from netaddr import * # sudo pip install netaddr

def one_time_provision(secrets):
    # 1 region
    # 2 VPCs, prod and nonprod
    # 3 AZs in each VPC
    # 6 subnets per AZ
    # 6*3 = 18 subnets
    # 32 /26 subnets in the VPC's /21
    region = 'us-west-2'
    availability_zones = ['a','b','c']
    subnet_size = 24
    path = "/identity/"
    desired_security_groups_json = '''
[
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
        "identity-middleware",
        [
            {
                "ip_protocol": "tcp",
                "from_port": 80,
                "to_port": 80,
                "src_group": "identity-private-loadbalancer"
            }
        ]
    ],
    [
        "identity-dbwriter",
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
                "src_group": "identity-dbwriter"
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

    output={}

    import boto.vpc
    import boto.ec2
    conn_vpc = boto.vpc.connect_to_region(region)

    desired_vpcs = {'dev' : '10.148.24.0/21',
                    'prod' : '10.148.32.0/21'}
    vpcs = {}
    for environment in desired_vpcs.keys():
        vpcs[region] = {}
        vpcs[region][environment] = {}

        # Create VPCs
        new_vpc = conn_vpc.create_vpc(desired_vpcs[environment])
        # TODO : boto.ec2.ec2object.add_tag('prod')
        output[new_vpc.id] = {'cidr_block':new_vpc.cidr_block}
        vpcs[region][environment]['vpc'] = new_vpc

        ip = IPNetwork(vpc.cidr_block)
        available_subnets = ip.subnet(subnet_size)

        vpcs[region][environment]['availability_zones'] = {}
        # Create subnets
        for availability_zone in [region + x for x in availability_zones]:
            vpcs[region][environment]['availability_zones'][availability_zone] = {}
            subnet = conn_vpc.create_subnet(vpc.id, available_subnets.next(), availability_zone=availability_zone)
            vpcs[region][environment]['availability_zones'][availability_zone]['public-subnet']=subnet
            subnet = conn_vpc.create_subnet(vpc.id, available_subnets.next(), availability_zone=availability_zone)
            vpcs[region][environment]['availability_zones'][availability_zone]['private-subnet']=subnet

        # Create all security groups
        conn_ec2 = boto.ec2.connect_to_region(region)
        vpcs[region][environment]['security-groups'] = {}
        for security_group_definition in desired_security_groups:
            security_group_name = environment + '-' + security_group_definition[0]
            vpcs[region][environment]['security-groups'][security_group_name] = conn_ec2.create_security(security_group_name, security_group_name, vpc.id)
            for rule in security_group_definition[1]:
                if not vpcs[region][environment]['security-groups'][security_group_name].authorize(rule):
                    print 'failed to add rule to security group'

        # Upload certificates
        import boto.iam
        conn_iam = boto.iam.connect_to_region(region)

        # These describes the json format for the secrets.json file that contains the certs
        example_certs_json = '''
{
    "dev": {
        "certs": {
            "wildcard.anosrep.org" : {
                "key": "-----BEGIN RSA PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nDEK-Info: DES-EDE3-CBC,D77824D9665B009A\n\nAYT/Cf0mKbF+saGt4LYzWPARrfhGDWsPOwcTVNREPU7kfKzBqKEgj1zmdF51Ayz7\njqBqvGGF5S9dEawJOReRizl+A2gmf9PerRwd0WE3lvXqQ8kNhrNQXJ9OqgbTsmHU\n1RFDoAXuoQm4F8oDTRCtbiFwWd2n1tAat6EQYb6SS5C8pUSvDZdzovjrv5sXgOtK\nDo2XA/azIlv5/XAaTi+ufDFP4D83ztQYdcPuyfGNneS9KVhNvKzPt9keuFF42aRA\nPP6YhjDiYgVdiqfdYO0zGXv/DUH3UsdKljw0XZ9QczCQ1PFoqYKbfOEm3dpRci62\nhbQVTLUf8oZVNNeFRKbDn32dgLlwzMu5Bkt1Qo7xouemE3NOPQKMg5l1EQ84yKpB\nmsA/al37rHhtCQoqlcibOCSQQNPiHx7Q70OicwOvfkma1OVhEisodgXSlGhUa4wD\nIAOWuKfkRkhbSIVLlv4gDyslgTjdP/2UG1sIA4lHCYONww8++EL0nhYDM3AvTgas\nw3S/UvT8umNwwA/1Fb8dOuui8afgd06/h2tTaUu98j13GL0dwF/SIwVeb848MX02\nENRXiVrJWHZScTgjJCxJzcbBa1lGZcPEwgbbF8D2O1Tdytgal2qajqY6jBuw7cPf\nu9OP4PolR/K0S93UqR+iFK4pEh1f6i8TJiEYncn/xYMOFtYMANa/qW2ES+gIBweP\n8fmFH/l5AE/ap+W3/dOQ5gG2u5GAoyaQxKr/QAOR99VfWdSRTBqWwf+QIeqUsczo\nTOhwrnOGnG5gPE66AiQssgbM2M98rcY+mcmHW1IxHfIqb9nDTEpY8Q==\n-----END RSA PRIVATE KEY-----",
                "cert": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----",
                "intermediate": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----"
            },
            "wildcard.login.anosrep.org" : {
                "key": "-----BEGIN RSA PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nDEK-Info: DES-EDE3-CBC,D77824D9665B009A\n\nAYT/Cf0mKbF+saGt4LYzWPARrfhGDWsPOwcTVNREPU7kfKzBqKEgj1zmdF51Ayz7\njqBqvGGF5S9dEawJOReRizl+A2gmf9PerRwd0WE3lvXqQ8kNhrNQXJ9OqgbTsmHU\n1RFDoAXuoQm4F8oDTRCtbiFwWd2n1tAat6EQYb6SS5C8pUSvDZdzovjrv5sXgOtK\nDo2XA/azIlv5/XAaTi+ufDFP4D83ztQYdcPuyfGNneS9KVhNvKzPt9keuFF42aRA\nPP6YhjDiYgVdiqfdYO0zGXv/DUH3UsdKljw0XZ9QczCQ1PFoqYKbfOEm3dpRci62\nhbQVTLUf8oZVNNeFRKbDn32dgLlwzMu5Bkt1Qo7xouemE3NOPQKMg5l1EQ84yKpB\nmsA/al37rHhtCQoqlcibOCSQQNPiHx7Q70OicwOvfkma1OVhEisodgXSlGhUa4wD\nIAOWuKfkRkhbSIVLlv4gDyslgTjdP/2UG1sIA4lHCYONww8++EL0nhYDM3AvTgas\nw3S/UvT8umNwwA/1Fb8dOuui8afgd06/h2tTaUu98j13GL0dwF/SIwVeb848MX02\nENRXiVrJWHZScTgjJCxJzcbBa1lGZcPEwgbbF8D2O1Tdytgal2qajqY6jBuw7cPf\nu9OP4PolR/K0S93UqR+iFK4pEh1f6i8TJiEYncn/xYMOFtYMANa/qW2ES+gIBweP\n8fmFH/l5AE/ap+W3/dOQ5gG2u5GAoyaQxKr/QAOR99VfWdSRTBqWwf+QIeqUsczo\nTOhwrnOGnG5gPE66AiQssgbM2M98rcY+mcmHW1IxHfIqb9nDTEpY8Q==\n-----END RSA PRIVATE KEY-----",
                "cert": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----",
                "intermediate": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----"
            },
            "wildcard.diresworb.org" : {
                "key": "-----BEGIN RSA PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nDEK-Info: DES-EDE3-CBC,D77824D9665B009A\n\nAYT/Cf0mKbF+saGt4LYzWPARrfhGDWsPOwcTVNREPU7kfKzBqKEgj1zmdF51Ayz7\njqBqvGGF5S9dEawJOReRizl+A2gmf9PerRwd0WE3lvXqQ8kNhrNQXJ9OqgbTsmHU\n1RFDoAXuoQm4F8oDTRCtbiFwWd2n1tAat6EQYb6SS5C8pUSvDZdzovjrv5sXgOtK\nDo2XA/azIlv5/XAaTi+ufDFP4D83ztQYdcPuyfGNneS9KVhNvKzPt9keuFF42aRA\nPP6YhjDiYgVdiqfdYO0zGXv/DUH3UsdKljw0XZ9QczCQ1PFoqYKbfOEm3dpRci62\nhbQVTLUf8oZVNNeFRKbDn32dgLlwzMu5Bkt1Qo7xouemE3NOPQKMg5l1EQ84yKpB\nmsA/al37rHhtCQoqlcibOCSQQNPiHx7Q70OicwOvfkma1OVhEisodgXSlGhUa4wD\nIAOWuKfkRkhbSIVLlv4gDyslgTjdP/2UG1sIA4lHCYONww8++EL0nhYDM3AvTgas\nw3S/UvT8umNwwA/1Fb8dOuui8afgd06/h2tTaUu98j13GL0dwF/SIwVeb848MX02\nENRXiVrJWHZScTgjJCxJzcbBa1lGZcPEwgbbF8D2O1Tdytgal2qajqY6jBuw7cPf\nu9OP4PolR/K0S93UqR+iFK4pEh1f6i8TJiEYncn/xYMOFtYMANa/qW2ES+gIBweP\n8fmFH/l5AE/ap+W3/dOQ5gG2u5GAoyaQxKr/QAOR99VfWdSRTBqWwf+QIeqUsczo\nTOhwrnOGnG5gPE66AiQssgbM2M98rcY+mcmHW1IxHfIqb9nDTEpY8Q==\n-----END RSA PRIVATE KEY-----",
                "cert": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----",
                "intermediate": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----"
            }
        }
    },
    "prod": {
        "certs": {
            "multisan-www.persona.org" : {
                "key": "-----BEGIN RSA PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nDEK-Info: DES-EDE3-CBC,D77824D9665B009A\n\nAYT/Cf0mKbF+saGt4LYzWPARrfhGDWsPOwcTVNREPU7kfKzBqKEgj1zmdF51Ayz7\njqBqvGGF5S9dEawJOReRizl+A2gmf9PerRwd0WE3lvXqQ8kNhrNQXJ9OqgbTsmHU\n1RFDoAXuoQm4F8oDTRCtbiFwWd2n1tAat6EQYb6SS5C8pUSvDZdzovjrv5sXgOtK\nDo2XA/azIlv5/XAaTi+ufDFP4D83ztQYdcPuyfGNneS9KVhNvKzPt9keuFF42aRA\nPP6YhjDiYgVdiqfdYO0zGXv/DUH3UsdKljw0XZ9QczCQ1PFoqYKbfOEm3dpRci62\nhbQVTLUf8oZVNNeFRKbDn32dgLlwzMu5Bkt1Qo7xouemE3NOPQKMg5l1EQ84yKpB\nmsA/al37rHhtCQoqlcibOCSQQNPiHx7Q70OicwOvfkma1OVhEisodgXSlGhUa4wD\nIAOWuKfkRkhbSIVLlv4gDyslgTjdP/2UG1sIA4lHCYONww8++EL0nhYDM3AvTgas\nw3S/UvT8umNwwA/1Fb8dOuui8afgd06/h2tTaUu98j13GL0dwF/SIwVeb848MX02\nENRXiVrJWHZScTgjJCxJzcbBa1lGZcPEwgbbF8D2O1Tdytgal2qajqY6jBuw7cPf\nu9OP4PolR/K0S93UqR+iFK4pEh1f6i8TJiEYncn/xYMOFtYMANa/qW2ES+gIBweP\n8fmFH/l5AE/ap+W3/dOQ5gG2u5GAoyaQxKr/QAOR99VfWdSRTBqWwf+QIeqUsczo\nTOhwrnOGnG5gPE66AiQssgbM2M98rcY+mcmHW1IxHfIqb9nDTEpY8Q==\n-----END RSA PRIVATE KEY-----",
                "cert": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----",
                "intermediate": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----"
            },
            "www.browserid.org" : {
                "key": "-----BEGIN RSA PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nDEK-Info: DES-EDE3-CBC,D77824D9665B009A\n\nAYT/Cf0mKbF+saGt4LYzWPARrfhGDWsPOwcTVNREPU7kfKzBqKEgj1zmdF51Ayz7\njqBqvGGF5S9dEawJOReRizl+A2gmf9PerRwd0WE3lvXqQ8kNhrNQXJ9OqgbTsmHU\n1RFDoAXuoQm4F8oDTRCtbiFwWd2n1tAat6EQYb6SS5C8pUSvDZdzovjrv5sXgOtK\nDo2XA/azIlv5/XAaTi+ufDFP4D83ztQYdcPuyfGNneS9KVhNvKzPt9keuFF42aRA\nPP6YhjDiYgVdiqfdYO0zGXv/DUH3UsdKljw0XZ9QczCQ1PFoqYKbfOEm3dpRci62\nhbQVTLUf8oZVNNeFRKbDn32dgLlwzMu5Bkt1Qo7xouemE3NOPQKMg5l1EQ84yKpB\nmsA/al37rHhtCQoqlcibOCSQQNPiHx7Q70OicwOvfkma1OVhEisodgXSlGhUa4wD\nIAOWuKfkRkhbSIVLlv4gDyslgTjdP/2UG1sIA4lHCYONww8++EL0nhYDM3AvTgas\nw3S/UvT8umNwwA/1Fb8dOuui8afgd06/h2tTaUu98j13GL0dwF/SIwVeb848MX02\nENRXiVrJWHZScTgjJCxJzcbBa1lGZcPEwgbbF8D2O1Tdytgal2qajqY6jBuw7cPf\nu9OP4PolR/K0S93UqR+iFK4pEh1f6i8TJiEYncn/xYMOFtYMANa/qW2ES+gIBweP\n8fmFH/l5AE/ap+W3/dOQ5gG2u5GAoyaQxKr/QAOR99VfWdSRTBqWwf+QIeqUsczo\nTOhwrnOGnG5gPE66AiQssgbM2M98rcY+mcmHW1IxHfIqb9nDTEpY8Q==\n-----END RSA PRIVATE KEY-----",
                "cert": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----",
                "intermediate": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----"
            },
            "multisan-yahoo.login.persona.org" : {
                "key": "-----BEGIN RSA PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nDEK-Info: DES-EDE3-CBC,D77824D9665B009A\n\nAYT/Cf0mKbF+saGt4LYzWPARrfhGDWsPOwcTVNREPU7kfKzBqKEgj1zmdF51Ayz7\njqBqvGGF5S9dEawJOReRizl+A2gmf9PerRwd0WE3lvXqQ8kNhrNQXJ9OqgbTsmHU\n1RFDoAXuoQm4F8oDTRCtbiFwWd2n1tAat6EQYb6SS5C8pUSvDZdzovjrv5sXgOtK\nDo2XA/azIlv5/XAaTi+ufDFP4D83ztQYdcPuyfGNneS9KVhNvKzPt9keuFF42aRA\nPP6YhjDiYgVdiqfdYO0zGXv/DUH3UsdKljw0XZ9QczCQ1PFoqYKbfOEm3dpRci62\nhbQVTLUf8oZVNNeFRKbDn32dgLlwzMu5Bkt1Qo7xouemE3NOPQKMg5l1EQ84yKpB\nmsA/al37rHhtCQoqlcibOCSQQNPiHx7Q70OicwOvfkma1OVhEisodgXSlGhUa4wD\nIAOWuKfkRkhbSIVLlv4gDyslgTjdP/2UG1sIA4lHCYONww8++EL0nhYDM3AvTgas\nw3S/UvT8umNwwA/1Fb8dOuui8afgd06/h2tTaUu98j13GL0dwF/SIwVeb848MX02\nENRXiVrJWHZScTgjJCxJzcbBa1lGZcPEwgbbF8D2O1Tdytgal2qajqY6jBuw7cPf\nu9OP4PolR/K0S93UqR+iFK4pEh1f6i8TJiEYncn/xYMOFtYMANa/qW2ES+gIBweP\n8fmFH/l5AE/ap+W3/dOQ5gG2u5GAoyaQxKr/QAOR99VfWdSRTBqWwf+QIeqUsczo\nTOhwrnOGnG5gPE66AiQssgbM2M98rcY+mcmHW1IxHfIqb9nDTEpY8Q==\n-----END RSA PRIVATE KEY-----",
                "cert": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----",
                "intermediate": "-----BEGIN CERTIFICATE-----\nMIIC9TCCAl6gAwIBAgIJAKO2X3cPYJUgMA0GCSqGSIb3DQEBBQUAMFsxCzAJBgNV\nBAYTAlVTMREwDwYDVQQIEwhOZXcgWW9yazERMA8GA1UEBxMITmV3IFlvcmsxEDAO\nBgNVBAoTB0V4YW1wbGUxFDASBgNVBAMTC2V4YW1wbGUuY29tMB4XDTEzMDIwMjIy\nNDgzOFoXDTE2MDIwMjIyNDgzOFowWzELMAkGA1UEBhMCVVMxETAPBgNVBAgTCE5l\ndyBZb3JrMREwDwYDVQQHEwhOZXcgWW9yazEQMA4GA1UEChMHRXhhbXBsZTEUMBIG\nA1UEAxMLZXhhbXBsZS5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKcY\nu8ZzC40dWBnr3AtUR/TGFWVQnW9Mf/teSW4EhzhdESNw4YdLQs5h4U6GzMktBvwP\nnAxrTNmcqHJDt6+yDuVka0VQ2Sb6HoAtZtWzE1BsgeFH6qnYhBAAPqcnBPfdij/N\nhVKNXpFjjeW06YQaxnhhXYT1nTgasY/RIWrk7u+nAgMBAAGjgcAwgb0wHQYDVR0O\nBBYEFJ9B+d8Mf2QwzrnIrbFte7hsf+iYMIGNBgNVHSMEgYUwgYKAFJ9B+d8Mf2Qw\nzrnIrbFte7hsf+iYoV+kXTBbMQswCQYDVQQGEwJVUzERMA8GA1UECBMITmV3IFlv\ncmsxETAPBgNVBAcTCE5ldyBZb3JrMRAwDgYDVQQKEwdFeGFtcGxlMRQwEgYDVQQD\nEwtleGFtcGxlLmNvbYIJAKO2X3cPYJUgMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcN\nAQEFBQADgYEAfYfXWLkA/t8UdgNcq89D1pnrm85P0Xkd/kgtAOIerUTXkJzJn67G\nzeOUy2My4trstADjUW88iTaUb9Zd9fD84Mg8jlfST1+OfZNcdNTX7NPtyocQY0Lf\nhBKyua5OSszDEPlgAuVlzwYSUgUqTy6cQvHrpLl7tY0xuPw6dRqzdBE=\n-----END CERTIFICATE-----"
            }
        }
    }
}
'''
        vpcs[region][environment]['certs'] = {}
        for cert_name in secrets[environment]['certs'].keys():
            cert = conn_iam.upload_server_cert(cert_name, 
                                               secrets[environment]['certs']['cert'], 
                                               secrets[environment]['certs']['key'], 
                                               secrets[environment]['certs']['intermediate'], 
                                               path)
            vpcs[region][environment]['certs'][cert_name] = cert
            # cert.ServerCertificateId
            # http://docs.aws.amazon.com/IAM/latest/APIReference/API_ServerCertificateMetadata.html

    return vpcs

def create_stack(region, environment, vpc):
    desired_elbs_json = '''
[
    {
        "name": "public-persona",
        "listeners" : 
        [
            {
                "LoadBalancerPortNumber": 443,
                "InstancePortNumber": 80,
                "Protocol": "HTTPS",
                "CertName" : "multisan-www.persona.org"
            },
            {
                "LoadBalancerPortNumber": 80,
                "InstancePortNumber": 80,
                "Protocol": "HTTP"
            },
        ]
    }
]
'''
    import boto.ec2
    availability_zones = vpc[region][environment]['availability_zones'].keys()
    conn_elb = boto.ec2.elb.connect_to_region(region)
    lb = conn.create_load_balancer('my-lb', availability_zones, ports)            

if __name__ == '__main__':
    secrets = json.load('secrets.json')
    vpcs = one_time_provision(secrets)
