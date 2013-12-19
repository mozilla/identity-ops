#!/usr/bin/env python
"""Bind a DNS name to a CloudFormation stack output variable

usage: bind_dns.py [-h] [-d] FQDN REGION [STACKNAME] [VARIABLE]

Bind a DNS name to a CloudFormation stack output variable

positional arguments:
  FQDN         Fully qualified DNS Name to CNAME to the stack output variable
  REGION       AWS region containing CloudFormation stack
  STACKNAME    Name of the CloudFormation stack
  VARIABLE     The CloudFormation stack output variable name

optional arguments:
  -h, --help   show this help message and exit
  -d, --debug  Output debug information

Examples :

Show all CloudFormation stacks in us-east-1 :
  ./bind_dns.py foo.example.com us-east-1

Show all CloudFormation output variables in stack foostack :
  ./bind_dns.py foo.example.com us-east-1 foostack

Bind the DNS name foo.example.com to the CloudFormation output variable 
called ELBName for the stack foostack :
  ./bind_dns.py foo.example.com us-east-1 foostack ELBName


"""

import argparse
import boto
import boto.ec2
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

Show all CloudFormation stacks in us-east-1 :
  %(name)s foo.example.com us-east-1

Show all CloudFormation output variables in stack foostack :
  %(name)s foo.example.com us-east-1 foostack

Bind the DNS name foo.example.com to the CloudFormation output variable 
called ELBName for the stack foostack :
  %(name)s foo.example.com us-east-1 foostack ELBName

""" % {'name': sys.argv[0]}

parser = argparse.ArgumentParser(
                 description=('Bind a DNS name to a '
                              'CloudFormation stack output '
                              'variable'),
                 formatter_class=argparse.RawDescriptionHelpFormatter,
                 epilog=epilog)
parser.add_argument('fqdn', metavar="FQDN",
                    help='Fully qualified DNS Name to CNAME to the stack '
                    'output variable')
parser.add_argument('region', metavar="REGION", choices=all_regions, 
                    help='AWS region containing CloudFormation stack')
parser.add_argument('stackname', metavar='STACKNAME', nargs="?", default=None,
                    help='Name of the CloudFormation stack')
parser.add_argument('variable', metavar='VARIABLE', nargs="?", default=None,
                    help='The CloudFormation stack output variable name')
parser.add_argument('-d', '--debug', action="store_true",
                    help="Output debug information")
args = parser.parse_args()

if args.fqdn[-1] != '.':
    args.fqdn += '.'

if args.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# Check arguments
conn_cfn = boto.cloudformation.connect_to_region(args.region)
stacks = [x for x in conn_cfn.describe_stacks()
          if x.stack_name == args.stackname]
if len(stacks) == 0:
    parser.error("argument STACKNAME: invalid choice: %s (choose from %s)" 
        % (args.stackname, 
           ', '.join([x.stack_name for x in conn_cfn.describe_stacks()])))

# This assumes we don't get multiple stack results from our search
output = [x for x in stacks[0].outputs if x.key == args.variable]
if len(output) == 0:
    parser.error("argument VARIABLE: invalid choice: %s (choose from %s)" 
        % (args.variable, 
           ', '.join([x.key for x in stacks[0].outputs])))

# This assumes there aren't multiple outputs with the same name

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
    parser.error("argument FQDN: invalid choice: %s (fqdn must exist in of "
                 "these zones : %s)" 
                 % (args.fqdn, [x['Name'] for x in all_zones]))

# Adding/Updating record
changes = boto.route53.record.ResourceRecordSets(conn_route53, 
                 zone_id, 
                 "Adding/Updating %s to %s in zone %s for stack %s "
                 % (args.fqdn, output[0].value, zone_name, args.stackname))
matching_rrsets = [x for x in conn_route53.get_all_rrsets(zone_id) 
                   if x.type == 'CNAME' and x.name == args.fqdn]

ttl = 30
if len(matching_rrsets) == 1:
    logging.debug("Target DNS name %s exists already, deleting" 
                  % matching_rrsets[0].name)
    ttl = matching_rrsets[0].ttl
    record = changes.add_change("DELETE", 
                                matching_rrsets[0].name, 
                                matching_rrsets[0].type,
                                ttl=matching_rrsets[0].ttl)
    record.add_value(matching_rrsets[0].resource_records[0])
record = changes.add_change("CREATE", args.fqdn, 'CNAME', ttl)
record.add_value(output[0].value)

commit = changes.commit()
logging.debug('Commiting DNS change %s' % commit)

change = conn_route53.get_change(get_change_id(commit
                                   ['ChangeResourceRecordSetsResponse']))
logging.debug('%s' % change)

while get_change_status(change['GetChangeResponse']) == 'PENDING':
    time.sleep(5)
    change = conn_route53.get_change(get_change_id(change
                                           ['GetChangeResponse']))
    logging.info('Waiting for DNS change to sync across AWS')
if get_change_status(change['GetChangeResponse']) == 'INSYNC':
    logging.info('DNS Change completed.')
else:
    logging.warning('Unknown status for the change: %s' % change)
    logging.debug('%s' % change)
