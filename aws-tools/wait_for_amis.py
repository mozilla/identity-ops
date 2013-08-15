#!/usr/bin/env python
import boto.ec2
import sys
import time
region='us-west-2'
conn_ec2 = boto.ec2.connect_to_region(region)
images = conn_ec2.get_all_images()
if sys.argv[1][0:3] != 'ami':
  print "searching for hash %s" % sys.argv[1]
  ids = [x.id for x in images if sys.argv[1] in str(x.name)]
else:
  ids = sys.argv[1:]

print "ids are '%s'" % ids

for id in ids:
  while conn_ec2.get_image(id).state != 'available':
    print "waiting on %s" % id
    time.sleep(10)
  print "%s is available" % id
