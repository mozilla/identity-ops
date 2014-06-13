#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Bind a DNS name to a CloudFormation generated ELB

usage: bind_dns.py [-h] [-d] FQDN [REGION] [STACKNAME] [ELBNAME]

Bind a DNS name to a CloudFormation generated ELB

positional arguments:
  FQDN         Fully qualified DNS Name to alias to the ELB
  REGION       AWS region containing CloudFormation stack
  STACKNAME    Name of the CloudFormation stack
  ELBNAME      The CloudFormation resource logical ID for the ELB as defined
               in the CloudFormation template

optional arguments:
  -h, --help   show this help message and exit
  -d, --debug  Output debug information

Examples :

Show the alias of an existing Route53 DNS name
  ./bind_dns.py foo.example.com

Show the alias of an existing Route53 DNS name and the CloudFormation stack
that generated it :
  ./bind_dns.py foo.example.com us-east-1

Show all CloudFormation stacks in us-east-1 :
  ./bind_dns.py foo.example.com us-east-1

Show all CloudFormation ELBs in stack foostack :
  ./bind_dns.py foo.example.com us-east-1 foostack

Bind the DNS name foo.example.com to the CloudFormation ELB 
called ExampleELB for the stack foostack :
  ./bind_dns.py foo.example.com us-east-1 foostack ExampleELB

Note : The ELBNAME value is the CloudFormation resource Logical ID
(e.g. ExampleELB) not the Physical ID (e.g. mystack-ExampleE-PACIV6OTHJA1)

"""

import argparse
import boto
import boto.ec2
import boto.ec2.elb
import boto.cloudformation
import boto.route53.record
import logging
import time
import sys

all_regions = [x.name for x in 
               boto.ec2.connect_to_region('us-east-1').get_all_regions()]

get_change_id = lambda response: response['ChangeInfo']['Id'].split('/')[-1]
get_change_status = lambda response: response['ChangeInfo']['Status']

epilog="""Examples :

Show the alias of an existing Route53 DNS name
  %(name)s foo.example.com

Show the alias of an existing Route53 DNS name and the CloudFormation stack
that generated it :
  %(name)s foo.example.com us-east-1

Show all CloudFormation stacks in us-east-1 :
  %(name)s foo.example.com us-east-1

Show all CloudFormation ELBs in stack foostack :
  %(name)s foo.example.com us-east-1 foostack

Bind the DNS name foo.example.com to the CloudFormation ELB 
called ExampleELB for the stack foostack :
  %(name)s foo.example.com us-east-1 foostack ExampleELB

Note : The ELBNAME value is the CloudFormation resource Logical ID
(e.g. ExampleELB) not the Physical ID (e.g. mystack-ExampleE-PACIV6OTHJA1)

""" % {'name': sys.argv[0]}

parser = argparse.ArgumentParser(
                 description=('Bind a DNS name to a '
                              'CloudFormation generated ELB'),
                 formatter_class=argparse.RawDescriptionHelpFormatter,
                 epilog=epilog)
parser.add_argument('fqdn', metavar="FQDN",
                    help='Fully qualified DNS Name to alias to the ELB')
parser.add_argument('region', metavar="REGION", nargs="?",
                    help='AWS region containing CloudFormation stack')
parser.add_argument('stackname', metavar='STACKNAME', nargs="?", default=None,
                    help='Name of the CloudFormation stack')
parser.add_argument('elbname', metavar='ELBNAME', nargs="?", default=None,
                    help='The CloudFormation resource logical ID for the ELB '
                    'as defined in the CloudFormation template')
parser.add_argument('-d', '--debug', action="store_true",
                    help="Output debug information")
args = parser.parse_args()

if args.fqdn[-1] != '.':
    args.fqdn += '.'

if args.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# Validate that the zone of the fqdn is hosted in route53
conn_route53 = boto.connect_route53()
all_zones = (conn_route53.get_all_hosted_zones()['ListHostedZonesResponse']
             ['HostedZones'])
zone_id = False
for zone in all_zones:
    if args.fqdn.endswith(zone['Name']):
        # This assumes we won't match multiple zones
        zone_id = zone['Id'].split('/')[-1]
        zone_name = zone['Name']

if not zone_id:
    parser.error("argument FQDN: invalid choice: %s (fqdn must exist in one of "
                 "these zones : %s)" 
                 % (args.fqdn, [x['Name'] for x in all_zones]))

# Determine if the fqdn is an alias
matching_rrsets = [x for x in conn_route53.get_all_rrsets(zone_id) 
                   if x.type == 'A' and x.name == args.fqdn]
if len(matching_rrsets) == 1:
    alias=matching_rrsets[0].alias_dns_name
else:
    alias=False

# If region is empty and fqdn exists show its alias
if not args.region:
    if alias:
        print(alias)
        sys.exit(0)

# Validate the region
if args.region not in all_regions:
    parser.error("argument REGION: invalid choice: %s (region must be one of "
                 " : %s)" 
                 % (args.region, ', '.join(all_regions)))

conn_cfn = boto.cloudformation.connect_to_region(args.region)
all_stacks = conn_cfn.describe_stacks()

# If no stackname argument is given and there's an alias
# Look through all stack outputs to see if any contain the alias
# We're using stack outputs instead of resources because there is no way to
# do a case-insensitive search through stack resources in the AWS API
if (not args.stackname) and alias:
    matching_stack = False
    for stack in all_stacks:
        for output in stack.outputs:
            # Trim the trailing "." for comparison
            if alias[0:-1].lower() in output.value.lower():
                matching_stack = stack.stack_name
                break
        if matching_stack:
            break
    print("%s %s" % (alias, matching_stack if matching_stack else ''))

# Validate that stackname exists
stacks = [x for x in all_stacks
          if x.stack_name == args.stackname]
if len(stacks) == 0:
    parser.error("argument STACKNAME: invalid choice: %s (choose from %s)" 
        % (args.stackname, 
           ', '.join([x.stack_name for x in conn_cfn.describe_stacks()])))

# This assumes we don't get multiple stack results from our search
# Validate that the resource exists
stack_resources = conn_cfn.describe_stack_resources(stacks[0].stack_name)
stack_elbs = [x for x in stack_resources 
        if x.resource_type == 'AWS::ElasticLoadBalancing::LoadBalancer' 
        and x.logical_resource_id == args.elbname]
if len(stack_elbs) == 0:
    parser.error("argument ELBNAME: invalid choice: %s (choose from %s)" 
        % (args.elbname, 
           ', '.join([x.logical_resource_id for x in stack_resources
                      if x.resource_type == 'AWS::ElasticLoadBalancing::LoadBalancer'])))

# This assumes there aren't multiple outputs with the same name

conn_elb = boto.ec2.elb.connect_to_region(args.region)
elb = conn_elb.get_all_load_balancers([stack_elbs[0].physical_resource_id])
canonical_hosted_zone_elb_id = elb[0].canonical_hosted_zone_name_id
canonical_hosted_zone_name = elb[0].canonical_hosted_zone_name

# Adding/Updating record
changes = boto.route53.record.ResourceRecordSets(conn_route53, 
                 zone_id, 
                 "Adding/Updating %s to %s in zone %s for stack %s "
                 % (args.fqdn, canonical_hosted_zone_name, zone_name, args.stackname))
matching_rrsets = [x for x in conn_route53.get_all_rrsets(zone_id) 
                   if x.type == 'A' and x.name == args.fqdn]


ttl = 30
if len(matching_rrsets) == 1:
    logging.debug("Target DNS name %s exists already, deleting" 
                  % matching_rrsets[0].name)
    ttl = matching_rrsets[0].ttl
    record = changes.add_change(action="DELETE", 
                                name=matching_rrsets[0].name, 
                                type=matching_rrsets[0].type,
                                ttl=matching_rrsets[0].ttl,
                                alias_dns_name=matching_rrsets[0].alias_dns_name,
                                alias_hosted_zone_id=matching_rrsets[0].alias_hosted_zone_id,
                                alias_evaluate_target_health=False)

record = changes.add_change(action="CREATE", 
                            name=args.fqdn, 
                            type='A', 
                            ttl=ttl,
                            alias_dns_name=canonical_hosted_zone_name,
                            alias_hosted_zone_id=canonical_hosted_zone_elb_id,
                            alias_evaluate_target_health=False)

commit = changes.commit()
logging.debug('Committing DNS change %s' % commit)

change = conn_route53.get_change(get_change_id(commit
                                   ['ChangeResourceRecordSetsResponse']))
logging.debug('%s' % change)

while get_change_status(change['GetChangeResponse']) == 'PENDING':
    time.sleep(10)
    change = conn_route53.get_change(get_change_id(change
                                           ['GetChangeResponse']))
    logging.info('Waiting for DNS change to sync across AWS')
if get_change_status(change['GetChangeResponse']) == 'INSYNC':
    logging.info('DNS Change completed.')
else:
    logging.warning('Unknown status for the change: %s' % change)
    logging.debug('%s' % change)
