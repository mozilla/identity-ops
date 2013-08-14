#!/usr/bin/env python

# https://mana.mozilla.org/wiki/pages/viewpage.action?pageId=35069456

import boto.ec2.elb
import sys

if len(sys.argv) < 2:
  print "usage : %s REGION ELB-NAME" % sys.argv[0]
  print ""
  print "Example : %s us-west-2 persona-org-0810" % sys.argv[0]
  sys.exit(1)

region = sys.argv[1]
load_balancer_name = sys.argv[2]
conn_elb = boto.ec2.elb.connect_to_region(region)

#import logging
#logging.basicConfig(level=logging.DEBUG)

policy_attributes = {"ADH-AES128-SHA": False,
                    "ADH-AES256-SHA": False,
                    "ADH-CAMELLIA128-SHA": False,
                    "ADH-CAMELLIA256-SHA": False,
                    "ADH-DES-CBC3-SHA": False,
                    "ADH-DES-CBC-SHA": False,
                    "ADH-RC4-MD5": False,
                    "ADH-SEED-SHA": False,
                    "AES128-SHA": True,
                    "AES256-SHA": True,
                    "CAMELLIA128-SHA": True,
                    "CAMELLIA256-SHA": True,
                    "DES-CBC3-MD5": False,
                    "DES-CBC3-SHA": False,
                    "DES-CBC-MD5": False,
                    "DES-CBC-SHA": False,
                    "DHE-DSS-AES128-SHA": True,
                    "DHE-DSS-AES256-SHA": True,
                    "DHE-DSS-CAMELLIA128-SHA": False,
                    "DHE-DSS-CAMELLIA256-SHA": False,
                    "DHE-DSS-SEED-SHA": False,
                    "DHE-RSA-AES128-SHA": False,
                    "DHE-RSA-AES256-SHA": False,
                    "DHE-RSA-CAMELLIA128-SHA": False,
                    "DHE-RSA-CAMELLIA256-SHA": False,
                    "DHE-RSA-SEED-SHA": False,
                    "EDH-DSS-DES-CBC3-SHA": False,
                    "EDH-DSS-DES-CBC-SHA": False,
                    "EDH-RSA-DES-CBC3-SHA": False,
                    "EDH-RSA-DES-CBC-SHA": False,
                    "EXP-ADH-DES-CBC-SHA": False,
                    "EXP-ADH-RC4-MD5": False,
                    "EXP-DES-CBC-SHA": False,
                    "EXP-EDH-DSS-DES-CBC-SHA": False,
                    "EXP-EDH-RSA-DES-CBC-SHA": False,
                    "EXP-KRB5-DES-CBC-MD5": False,
                    "EXP-KRB5-DES-CBC-SHA": False,
                    "EXP-KRB5-RC2-CBC-MD5": False,
                    "EXP-KRB5-RC2-CBC-SHA": False,
                    "EXP-KRB5-RC4-MD5": False,
                    "EXP-KRB5-RC4-SHA": False,
                    "EXP-RC2-CBC-MD5": False,
                    "EXP-RC4-MD5": False,
                    "IDEA-CBC-SHA": False,
                    "KRB5-DES-CBC3-MD5": False,
                    "KRB5-DES-CBC3-SHA": False,
                    "KRB5-DES-CBC-MD5": False,
                    "KRB5-DES-CBC-SHA": False,
                    "KRB5-RC4-MD5": False,
                    "KRB5-RC4-SHA": False,
                    "Protocol-SSLv2": False,
                    "Protocol-SSLv3": True,
                    "Protocol-TLSv1": True,
                    "PSK-3DES-EDE-CBC-SHA": False,
                    "PSK-AES128-CBC-SHA": False,
                    "PSK-AES256-CBC-SHA": False,
                    "PSK-RC4-SHA": False,
                    "RC2-CBC-MD5": False,
                    "RC4-MD5": False,
                    "RC4-SHA": True,
                    "SEED-SHA": False}

policy_name = 'Mozilla-Security-Assurance-Ciphersuite-Policy-v-1-2'

# Create the Ciphersuite Policy
params = {'LoadBalancerName': load_balancer_name,
          'PolicyName': policy_name,
          'PolicyTypeName': 'SSLNegotiationPolicyType'}
conn_elb.build_complex_list_params(params, 
                                   [(x, policy_attributes[x]) for x in policy_attributes.keys()],
                                   'PolicyAttributes.member',
                                   ('AttributeName', 'AttributeValue'))
policy = conn_elb.get_list('CreateLoadBalancerPolicy', params, None)

# Apply the Ciphersuite Policy to your ELB
params = {'LoadBalancerName': load_balancer_name,
          'LoadBalancerPort': 443,
          'PolicyNames.member.1': policy_name}

result = conn_elb.get_list('SetLoadBalancerPoliciesOfListener', params, None)
print "New Policy '%s' created and applied to load balancer %s in %s" % (policy_name, load_balancer_name, region)