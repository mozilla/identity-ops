#!/usr/bin/env python
import json
import argparse
import logging
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(description='Update the autoscale json with a new set of AMIs')
parser.add_argument('hash', 
                    help='git hash of identity-ops that the instances were created from')
parser.add_argument('filename', 
                    help="Autoscale json file to update")
parser.add_argument('--tiers', nargs='+', default=['webhead', 'keysign', 'dbwrite'],
                   help='tiers to update (default: webhead, keysign, dbwrite)')
parser.add_argument('--dryrun', action="store_true",
                    help="don't actually change anything")

args = parser.parse_args()

with open(args.filename, 'r') as f:
  autoscale = json.load(f)

new_autoscale = []
for item in autoscale:
  for tier in args.tiers:
    if item['launch_configuration']['tier'] == tier:
      item['launch_configuration']['image_id'] = "persona-%s-%s" % (tier, args.hash)
  new_autoscale.append(item)

if args.dryrun:
  logging.info("Would have written %s" % args.filename)
  print json.dumps(new_autoscale, sort_keys=True, indent=4, separators=(',', ': '))
else:
  with open(args.filename, 'w') as f:
    json.dump(new_autoscale, f, sort_keys=True, indent=4, separators=(',', ': '))
  logging.info("Updated %s" % args.filename)
