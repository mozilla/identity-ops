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
  while len(available_amis) < len(amis):
    pending_amis = [x for x in amis if x not in available_amis]
    logging.info("Waiting on AMIs to become available : %s" % pending_amis)
    if len(pending_amis) == 0:
      raise Exception('Not sure how we got here. we should never pass get_all_images an empty list')
    images = conn_ec2.get_all_images(image_ids=pending_amis)
    for ami in images:
      if ami.state == 'available':
        available_amis.append(ami.id)
      logging.info("AMI %s is in state %s" % (ami.id, ami.state))
    if len(available_amis) < len(amis):
      time.sleep(10)

parser = argparse.ArgumentParser(description='Create AMIs from instances')
parser.add_argument('hash',
                    help='git hash of identity-ops that the instances were created from')
parser.add_argument('ips', nargs='*',
                   help='IP addresses of the instances to snapshot')
parser.add_argument('--amimap', default='/home/gene/Documents/coderepo/github.com/mozilla/identity-ops/aws-tools/config/ami_map.json',
                   help='AMI map json filename (default: /home/gene/Documents/coderepo/github.com/mozilla/identity-ops/aws-tools/config/ami_map.json)')
parser.add_argument('--region', default='us-west-2',
                   help='AWS region containing intances (default: us-west-2)')
parser.add_argument('--copy', metavar='REGION',
                   help='Region to copy resulting AMIs to')
parser.add_argument('--wait', action="store_true",
                    help="wait for AMIs to be available before exiting")
parser.add_argument('--dryrun', action="store_true",
                    help="don't actually change anything")

args = parser.parse_args()

with open(args.amimap, 'r') as f:
  amimap = json.load(f)
created_amis = []

today = time.strftime('%m/%d/%Y %H:%M')
conn_ec2 = boto.ec2.connect_to_region(args.region)

if len(args.ips) > 0:
  reservations = conn_ec2.get_all_instances()
  instances = []
  for reservation in reservations:
    for instance in reservation.instances:
      if instance.private_ip_address in args.ips:
        logging.debug("instance : %s %s" % (instance.id, instance.tags['Tier']))
        instances.append({'id': instance.id,
                          'tier': instance.tags['Tier']})

  logging.debug("Instances : %s" % instances)

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
  if len(created_amis) > 0:
    to_copy_amis = created_amis
  else:
    to_copy_amis = [amimap[x][args.region] for x in amimap.keys() if x.endswith('-%s' % args.hash)]

  logging.info("Waiting on AMIs to become available : %s" % to_copy_amis)
  wait_for_amis(conn_ec2, to_copy_amis)

  conn_ec2_destination = boto.ec2.connect_to_region(args.copy)
  copied_amis = []
  while len(copied_amis) < len(to_copy_amis):
    pending_amis = [x for x in to_copy_amis if x not in copied_amis]
    if len(copied_amis) != 0:
      time.sleep(10)
    if len(pending_amis) == 0:
      raise Exception('Not sure how we got here. we should never pass get_all_images an empty list')
    try:
        images = conn_ec2.get_all_images(image_ids=pending_amis)
    except boto.exception.EC2ResponseError:
        # recently created amis don't yet show up in API
        logging.info("Recently copied AMIs don't yet show up in the API. Waiting 10 seconds")
        time.sleep(10)
        continue
    for ami in images:
      if ami.state == 'available':
        destination_ami = conn_ec2_destination.get_all_images(filters={'name': ami.name})
        if len(destination_ami) > 0:
          logging.info("AMI %s with name %s already exists in region %s. Skipping" % (destination_ami[0].id, destination_ami[0].name, args.copy))
          created_amis.append(destination_ami[0].id)
          copied_amis.append(ami.id)
          continue
        if args.dryrun:
          logging.info("Would have copied ami %s with name %s from %s to %s" % (ami.id, ami.name, args.region, args.copy))
          new_ami = 'ami-copy-example'
        else:
          ami_id = conn_ec2_destination.copy_image(source_region = args.region, 
                                                   source_image_id = ami.id, 
                                                   name = ami.name, 
                                                   description = ami.name)
          # TODO : tag the ami
          logging.info("Copied ami %s with name %s from %s to %s resulting the in the new ami %s" % (ami.id, ami.name, args.region, args.copy, ami_id.image_id))
          created_amis.append(ami_id.image_id)
        if not ami.name in amimap:
          amimap[ami.name] = {}
        amimap[ami.name][args.copy] = ami_id.image_id
        amimap[ami.name]['date'] = today
        copied_amis.append(ami.id)
  write_amimap(amimap, args.amimap, args.dryrun)
  if args.wait:
    wait_for_amis(conn_ec2_destination, created_amis)
else:
  if args.wait:
    wait_for_amis(conn_ec2, created_amis)