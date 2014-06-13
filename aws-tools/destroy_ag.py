#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
logging.basicConfig(level=logging.INFO)
import time

def destroy_autoscale_group(name):
  import boto.ec2
  import boto.ec2.elb
  import boto.ec2.autoscale
  region = 'us-west-2'

  conn_autoscale = boto.ec2.autoscale.connect_to_region(region)
  conn_elb = boto.ec2.elb.connect_to_region(region)
  conn_ec2 = boto.ec2.connect_to_region(region)

  autoscale_group = conn_autoscale.get_all_groups([name])[0]
  launch_configuration = conn_autoscale.get_all_launch_configurations(names=[name])[0]
  load_balancers = autoscale_group.load_balancers
  existing_load_balancers = conn_elb.get_all_load_balancers()
  existing_addresses = conn_ec2.get_all_addresses()

  for address in [x for x in existing_addresses if x.instance_id in [y.instance_id for y in autoscale_group.instances]]:
      if not conn_ec2.disassociate_address(association_id=address.association_id):
          logging.error('failed to disassociate eip %s from instance %s' % (address.public_ip, address.instance_id))
      if not conn_ec2.release_address(allocation_id=address.allocation_id):
          logging.error('failed to release eip %s' % address.public_ip)

  autoscale_group.shutdown_instances()

  attempts=0
  while True:
      try:
          attempts += 1
          autoscale_group.delete()
          break
      except boto.exception.BotoServerError:
          logging.info('waiting 10 seconds for instances to finish shutting down')
          time.sleep(10)
          if attempts > 30:
              logging.error('unable to delete autoscale group %s after 5 minutes' % autoscale_group.name)
              autoscale_group.get_activities()
              raise
  launch_configuration.delete()
  for load_balancer in [x for x in existing_load_balancers if x.name in load_balancers]:
    load_balancer.delete()
  logging.info('ag %s destroyed' % name)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='destroy autoscale group')
  parser.add_argument('names', metavar='N', type=str, nargs="+", 
                     help='name of the autoscale group')

  args = parser.parse_args()
  for name in args.names:
      destroy_autoscale_group(name)