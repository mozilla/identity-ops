#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import boto
import boto.s3.key
import os.path
import sys

if len(sys.argv) <= 1:
  print "Pass the rpm you want to upload as an argument"
  sys.exit(1)
if not os.path.isfile(sys.argv[1]):
  print "Can't find file %s" % sys.argv[1]
  sys.exit(1)

conn_s3 = boto.connect_s3()
bucket = conn_s3.get_bucket('mozilla-identity-us-standard')
k = boto.s3.key.Key(bucket)
k.key = 'rpms/%s' % os.path.basename(sys.argv[1])
k.set_contents_from_filename(sys.argv[1])
k.set_acl('public-read')
