#!/usr/bin/env python
"""Copy an AMI to a set of target regions and/or share that AMI to another Amazon user.

usage: publish_amis.py [-h] [-a {copy,share,copyandshare}] [-s REGION]
                      [-r REGION,REGION...] [-u USERID,USERID...] [-d]
                      AMIID [AMIID ...]

Publish and share AMI across regions and IAMs

positional arguments:
  AMIID                 AMI IDs of the AMIs to publish and share

optional arguments:
  -h, --help            show this help message and exit
  -a {copy,share,copyandshare}, --action {copy,share,copyandshare}
                        Action to take (default: copyandshare)
  -s REGION, --source-region REGION
                        AWS region that the source AMI is in (default: us-
                        east-1)
  -r REGION,REGION..., --regions REGION,REGION...
                        AWS regions where you want images shared or copied to
                        (default: eu-west-1,sa-east-1,us-east-1,ap-northeast-1
                        ,us-west-2,us-west-1,ap-southeast-1,ap-southeast-2)
  -u USERID,USERID..., --userids USERID,USERID...
                        Amazon User IDs to share the AMIs with (default:
                        142069644989,351644144250)
  -d, --dryrun          don't actually do anything

action : copy
  This tool will first copy the AMIs (passed in as the AMIID argument) to all
  regions (passed in as the --regions option).

action : share
  The tool will confirm that all AMIs are in an "available" state in their
  source region. The tool will then modify each AMIs attributes to share
  them with the Amazon users or IAMs passed in as the --userids argument.

action :copyandshare
  This tool will first copy the AMIs (passed in as the AMIID argument) to all
  regions (passed in as the --regions option). The tool will then wait for 
  the copying process to complete and for the AMIs to enter an "available" 
  state at each of their destination regions. Once they are all available the
  tool will modify each AMIs attributes to share them with the Amazon users 
  or IAMs passed in as the --userids argument.

Upon completion the tool will output the map of new AMIs to regions in json

"""

import argparse
import boto.ec2
import boto.iam
import json
import logging
import time

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

all_userids = ['142069644989', '351644144250','361527076523','613808223628']
all_regions = [x.name for x in 
               boto.ec2.connect_to_region('us-east-1').get_all_regions()]

def type_comma_delimited_string(string):
  return string.split(',')

parser = argparse.ArgumentParser(description=('Publish and share AMI across '
                                              'regions and IAMs'))
parser.add_argument('amiids', nargs='+', metavar='AMIID',
                    help='AMI IDs of the AMIs to publish and share')
parser.add_argument('-a', '--action', default='copyandshare',
                    choices=['copy', 'share', 'copyandshare'],
                    help='Action to take (default: copyandshare)')
parser.add_argument('-s', '--source-region', default='us-east-1', 
                    choices=all_regions, metavar='REGION',
                    help=('AWS region that the source AMI is in '
                          '(default: us-east-1)'))
parser.add_argument('-r', '--regions', default=','.join(all_regions), 
                    metavar='REGION,REGION...', type=type_comma_delimited_string,
                    help=('AWS regions where you want images shared or copied '
                         'to (default: %s)' % ','.join(all_regions)))
parser.add_argument('-u', '--userids', default=','.join(all_userids), 
                    metavar='USERID,USERID...', 
                    type=type_comma_delimited_string,
                    help=('Amazon User IDs to share the AMIs with '
                         '(default: %s)' % ','.join(all_userids)))
parser.add_argument('-d', '--dryrun', action="store_true",
                    help="don't actually do anything")

args = parser.parse_args()

def wait_for_ami(conn_ec2, region, amiid):
  """Loop, waiting for a given AMI to become available.
  
  Check a given AMI with ID amiid to see if it's available.
  If not, loop, sleeping interval seconds and then checking again
  
  """

  interval=15
  ami_unavailable = True
  while ami_unavailable:
    try:
      images = conn_ec2.get_all_images(image_ids=[amiid])
    except boto.exception.EC2ResponseError:
      logging.debug("AMI %s doesn't yet exist in %s" % (amiid, region))
      time.sleep(interval)
      continue
    if images[0].state == 'available':
      logging.info('AMI %s in %s is available for use' % (amiid, region))
      ami_unavailable = False
    else:
      logging.info('Waiting for AMI %s to become available in %s' 
                    % (amiid, region))
      time.sleep(interval)

if len(set(args.userids).difference(set(all_userids))) > 0:
  parser.error("argument -u/--userids: invalid choice: %s (choose from %s)" 
                % (list(set(args.userids).difference(set(all_userids))), 
                   list(set(all_userids))))
if len(set(args.regions).difference(set(all_regions))) > 0:
  parser.error("argument -r/--regions: invalid choice: %s (choose from %s)" 
                % (list(set(args.regions).difference(set(all_regions))), 
                   list(set(all_regions))))

conn_iam = boto.iam.connect_to_region('universal')
current_user = (conn_iam.get_user()['get_user_response']['get_user_result']
                ['user']['arn'].split(':')[4])
if current_user in args.userids:
  args.userids.remove(current_user)
if args.source_region in args.regions:
  args.regions.remove(args.source_region)

conn_ec2_destination = {}
for region in args.regions + [args.source_region]:
  conn_ec2_destination[region] = boto.ec2.connect_to_region(region)

results={}
for i in args.amiids:
  results[i] = {'map': {
                        args.source_region : i
                        }
               }

conn_ec2 = boto.ec2.connect_to_region(args.source_region)
try:
  images = conn_ec2.get_all_images(image_ids=args.amiids)
except boto.exception.EC2ResponseError:
  parser.error("Unable to locate the source AMI(s) %s in region %s." 
               % (args.amiids, args.source_region))

if len(images) < len(args.amiids):
  parser.error("Unable to find all AMIs. Requested : %s. Found : %s" 
               % (args.amiids, images))

# Copy
for source_ami in images:
  if args.action in ['copy', 'copyandshare']:
    for region in args.regions:
      if args.dryrun:
        logging.info('Dryrun : Would have just copied AMI %s from %s to %s' 
                     % (source_ami, args.source_region, region))
      else:
        ami_id = conn_ec2_destination[region].copy_image(
                                         source_region = args.source_region, 
                                         source_image_id = source_ami.id, 
                                         name = source_ami.name, 
                                         description = source_ami.description)
        results[source_ami.id]['map'][region] = ami_id.image_id
        results[source_ami.id]['name'] = source_ami.name
        logging.info('AMI %s copied from %s to %s as AMI %s' 
                     % (source_ami, args.source_region, region, 
                        results[source_ami.id]['map'][region]))

# Share
if args.action in ['share', 'copyandshare']:
  for source_ami in results.keys():
    for region in results[source_ami]['map'].keys():
      wait_for_ami(conn_ec2_destination[region], 
                   region, 
                   results[source_ami]['map'][region])
      attributes = conn_ec2_destination[region].get_image_attribute(
                                image_id = results[source_ami]['map'][region])
      user_ids = (set() if 'user_ids' not in attributes.attrs 
                  else set(attributes.attrs['user_ids']))
      user_ids.update(args.userids)
      user_ids = list(user_ids)
      if args.dryrun:
        logging.info('Dryrun : Would have just shared AMI %s in region %s '
                     'with user_ids %s' 
                     % (results[source_ami]['map'][region], region, user_ids))
      else:
        if conn_ec2_destination[region].modify_image_attribute(
                               image_id = results[source_ami]['map'][region], 
                               user_ids = user_ids) is True:
          logging.info('AMI %s in region %s shared with user_ids %s' 
                       % (results[source_ami]['map'][region], 
                          region, user_ids))
        else:
          logging.error('Failed to share AMI %s in region %s shared with '
                        'user_ids %s : %s' 
                        % (results[source_ami]['map'][region], 
                           region, user_ids, result))

print(json.dumps(results.values(), indent=4))
