#!/usr/bin/env python

import argparse
import boto.ec2
import json
import time
import logging
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

def write_amimap(amimap, filename, dryrun=False):
  if dryrun:
    logging.info("Would have written ami_map.json")
    print json.dumps(amimap, sort_keys=True, indent=4, separators=(',', ': '))
  else:
    with open(filename, 'w') as f:
      json.dump(amimap, f, sort_keys=True, indent=4, separators=(',', ': '))
    logging.debug("wrote ami_map to disk")
  
def wait_for_amis(conn_ec2, amis):
  available_amis = []
  while len(available_amis) < amis:
    pending_amis = [x for x in amis if x not in available_amis]
    logging.info("Waiting on AMIs to become available : %s" % pending_amis)
    images = conn_ec2.get_all_images(image_ids=pending_amis)
    for ami in pending_amis:
      if ami.state == 'available':
        available_amis.append(ami_id)
    if len(available_amis) < amis:
      time.sleep(10)

parser = argparse.ArgumentParser(description='Create AMIs from instances')
parser.add_argument('hash',
                    help='git hash of identity-ops that the instances were created from')
parser.add_argument('ips', nargs='+',
                   help='IP addresses of the instances to snapshot')
parser.add_argument('--amimap', default='/home/gene/Documents/coderepo/github.com/mozilla/identity-ops/aws-tools/config/ami_map.json',
                   help='AMI map json filename (default: /home/gene/Documents/coderepo/github.com/mozilla/identity-ops/aws-tools/config/ami_map.json)')
parser.add_argument('--region', default='us-west-2',
                   help='AWS region containing intances (default: us-west-2)')
parser.add_argument('--copy', 
                   help='Region to copy resulting AMIs to')
parser.add_argument('--wait', action="store_true",
                    help="wait for AMIs to be available before exiting")
parser.add_argument('--dryrun', action="store_true",
                    help="don't actually change anything")

args = parser.parse_args()

today = time.strftime('%m/%d/%Y %H:%M')
conn_ec2 = boto.ec2.connect_to_region(args.region)
reservations = conn_ec2.get_all_instances()
instances = []
for reservation in reservations:
  for instance in reservation.instances:
    if instance.private_ip_address in args.ips:
      logging.debug("instance : %s %s" % (instance.id, instance.tags['Tier']))
      instances.append({'id': instance.id,
                        'tier': instance.tags['Tier']})

with open(args.amimap, 'r') as f:
  amimap = json.load(f)

created_amis = []
for instance in instances:
  name = "persona-%s-%s" % (instance['tier'], args.hash)
  if not name in amimap:
    amimap[name] = {}
  if args.dryrun:
    logging.info("Would have created AMI from instance %s with name %s" % (instance['id'], name))
    ami_id = 'ami-example'
  else:
    ami_id = conn_ec2.create_image(instance_id = instance['id'],
                                   name = name,
                                   description = name)
    # TODO : tag the ami
    logging.info("Created AMI %s from instance %s with name %s" % (ami_id, instance['id'], name))
  amimap[name][args.region] = ami_id
  amimap[name]['date'] = today
  created_amis.append(ami_id)

write_amimap(amimap, args.amimap, args.dryrun)

if args.copy:
  conn_ec2 = boto.ec2.connect_to_region(args.copy)
  created_amis = []
  copied_amis = []
  while len(copied_amis) < created_amis:
    pending_amis = [x for x in created_amis if x not in copied_amis]
    logging.info("Waiting on AMIs to become available : %s" % pending_amis)
    images = conn_ec2.get_all_images(image_ids=pending_amis)
    for ami in pending_amis:
      if ami.state == 'available':
        if args.dryrun:
          logging.info("Would have copied ami %s with name %s from %s to %s" % (ami.id, name, args.region, args.copy))
          ami_id = 'ami-copy-example'
        else:
          ami_id = conn_ec2.copy_image(source_region = args.region, 
                                       source_image_id = ami.id, 
                                       name = ami.name, 
                                       description = ami.name)
          # TODO : tag the ami
          logging.info("Copied ami %s with name %s from %s to %s resulting the in the new ami %s" % (ami.id, name, args.region, args.copy, ami_id))
          created_amis.append(ami_id)
        if not ami.name in amimap:
          amimap[ami.name] = {}
        amimap[ami.name][args.copy] = ami_id
        amimap[ami.name][date] = today
        copied_amis.append(ami.id)
    if len([x for x in pending_amis if x.state != 'available']) > 0:
      time.sleep(10)
  write_amimap(amimap, args.amimap, args.dryrun)
if args.wait:
  wait_for_amis(conn_ec2, created_amis)