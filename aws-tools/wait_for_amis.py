#!/usr/bin/env python
import boto.ec2
import sys
import time
region='us-west-2'
conn_ec2 = boto.ec2.connect_to_region(region)
for id in sys.argv[1:]:
  while conn_ec2.get_image(id).state != 'available':
    time.sleep(10)
  print "%s is available" % id