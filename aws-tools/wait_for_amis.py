#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import boto.ec2
import sys
import time
region='us-east-1'
conn_ec2 = boto.ec2.connect_to_region(region)
images = conn_ec2.get_all_images()
if sys.argv[1][0:3] != 'ami':
  print "searching for hash %s" % sys.argv[1]
  ids = [x.id for x in images if sys.argv[1] in str(x.name)]
else:
  ids = sys.argv[1:]

print "ids are '%s'" % ids

for id in ids:
  state=False
  while state != 'available':
    if state:
      print "waiting on %s which is %s" % (id, state) 
      time.sleep(10)
    state = conn_ec2.get_image(id).state
  print "%s is available" % id
