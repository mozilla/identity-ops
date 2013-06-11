#!/usr/bin/env python
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
