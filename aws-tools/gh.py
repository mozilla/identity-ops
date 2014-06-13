#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
try:
    # If this is python2.6 you need to install argparse with "pip install argparse"
    import argparse
except ImportError:
    print("The module argparse doesn't appear to be installed. Try running 'sudo pip install argparse'")
    sys.exit(1)
import boto.ec2
import boto.cloudformation
import boto.ec2.autoscale
import logging
import textwrap
import json

my_metadata = boto.utils.get_instance_metadata()
default_region = my_metadata['placement']['availability-zone'][0:-1]
#default_region='us-east-1'

try:
    all_regions = [x.name for x in 
                   boto.ec2.connect_to_region('us-east-1').get_all_regions()]
except (boto.exception.EC2ResponseError, boto.exception.NoAuthHandlerFound):
    print("Insufficient AWS privileges. Confirm your ~/.boto file is setup with your AWS API keys. http://boto.readthedocs.org/en/latest/boto_config_tut.html#details")
    sys.exit(1)

conn_ec2 = boto.ec2.connect_to_region(default_region)

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=textwrap.dedent('''\
Examples:
  Show all stacks
    gh
  Show instances in stack foo
    gh foo
  Show instances in stack foo in a table
    gh foo -o table
  Show instances in stack foo in a table
    gh foo -o table
  Show instances in stack foo in json
    gh foo -o json'''))

parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-r", "--region", help="region to query in (default: %s)" % default_region,
                    default=default_region, choices=all_regions)
parser.add_argument("-o", "--output", help="set the output format",
                    choices=["list","json","table"], default="list")
parser.add_argument("stackname", nargs='?', help="The name of the CloudFormation stack")
parser.add_argument("asgroup", nargs='?', help="The logical ID of the AutoScale Group")
args = parser.parse_args()

if default_region != args.region:
  conn_ec2 = boto.ec2.connect_to_region(args.region)

if args.verbose:
  logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

conn_cfn = boto.cloudformation.connect_to_region(args.region)
all_stacks = conn_cfn.describe_stacks()

if not args.stackname:
    if args.output == "list" or args.output == "table":
        for i in [x.stack_name for x in all_stacks]:
            print(i)
    elif args.output == "json":
        print(json.dumps([x.stack_name for x in all_stacks], 
                         sort_keys=True, 
                         indent=4, 
                         separators=(',', ': ')))
    sys.exit(0)
elif args.stackname not in [x.stack_name for x in all_stacks]:
    parser.error("argument STACKNAME: invalid choice: %s (choose from %s)" 
        % (args.stackname, 
           ', '.join([x.stack_name for x in all_stacks])))

stack=[x for x in all_stacks if x.stack_name == args.stackname][0]

cfn_autoscale_groups = [x for x in stack.describe_resources()
                         if x.resource_type == 'AWS::AutoScaling::AutoScalingGroup']

conn_autoscale = boto.ec2.autoscale.connect_to_region(args.region)

autoscale_groups = conn_autoscale.get_all_groups(
             names=[x.physical_resource_id for x in 
                    cfn_autoscale_groups])

all_instance_ids=[]
for autoscale_group in autoscale_groups:
    all_instance_ids.extend([x.instance_id for x in autoscale_group.instances])

all_instances = conn_ec2.get_only_instances(instance_ids=all_instance_ids)

output=[]
for cfn_autoscale_group in cfn_autoscale_groups:
    autoscale_group_name = cfn_autoscale_group.logical_resource_id
    instances = [x.instances for x in 
               autoscale_groups 
               if x.name == cfn_autoscale_group.physical_resource_id][0]
    for instance in instances:
        id = instance.instance_id
        ip = [x.ip_address for x in all_instances if x.id == id][0]
        dns = [x.public_dns_name for x in all_instances if x.id == id][0]
        output.append({'autoscale_group': autoscale_group_name, 
                       'id': id,
                       'ip': ip,
                       'dns': dns})

if args.output == "list":
  for i in output:
      print(i['dns'])
elif args.output == "json":
  print(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))
elif args.output == "table":
  for i in output:
    print("{0: >5} {1: >5} {2}".format(i['autoscale_group'], i['dns'], i['id']))
