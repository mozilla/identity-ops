#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Apply recommendation from https://wiki.mozilla.org/Security/Server_Side_TLS

import boto.ec2.elb
import sys
import json
import operator
from boto.resultset import ResultSet

class PolicyDescription(object):
    # Data type to extend boto in order to support DescribeLoadBalancerPolicies
    # http://docs.aws.amazon.com/ElasticLoadBalancing/latest/APIReference/API_PolicyDescription.html
    def __init__(self, connection=None):
        self.policy_attribute_descriptions = None
        self.policy_name = None
        self.policy_type_name = None

    def __repr__(self):
        return 'PolicyDescription(%s, %s)' % (self.policy_name,
                                                self.policy_type_name)

    def startElement(self, name, attrs, connection):
        if name == 'PolicyAttributeDescriptions':
            rs = ResultSet([('member', PolicyAttributeDescription)])
            self.policy_attribute_descriptions = rs
            return self.policy_attribute_descriptions

    def endElement(self, name, value, connection):
        if name == 'PolicyName':
            self.policy_name = value
        elif name == 'PolicyTypeName':
            self.policy_type_name = value


class PolicyAttributeDescription(object):
    # Data type to extend boto in order to support DescribeLoadBalancerPolicies
    # http://docs.aws.amazon.com/ElasticLoadBalancing/latest/APIReference/API_PolicyAttributeDescription.html
    def __init__(self, connection=None):
        self.attribute_name = None
        self.attribute_value = None

    def __repr__(self):
        return 'PolicyAttributeDescription(%s, %s)' % (self.attribute_name,
                                                self.attribute_value)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'AttributeName':
            self.attribute_name = value
        elif name == 'AttributeValue':
            self.attribute_value = value

class CipherSuite:
    def __init__(self, region, load_balancer_name):
        self.load_balancer_name = load_balancer_name
        self.region = region
        self.policy_name = 'Mozilla-Security-Assurance-Ciphersuite-Policy-v-2-0'
        self.policy_attributes = {"ADH-AES128-GCM-SHA256": False,
            "ADH-AES256-GCM-SHA384": False,
            "ADH-AES128-SHA": False,
            "ADH-AES128-SHA256": False,
            "ADH-AES256-SHA": False,
            "ADH-AES256-SHA256": False,
            "ADH-CAMELLIA128-SHA": False,
            "ADH-CAMELLIA256-SHA": False,
            "ADH-DES-CBC3-SHA": False,
            "ADH-DES-CBC-SHA": False,
            "ADH-RC4-MD5": False,
            "ADH-SEED-SHA": False,
            "AES128-GCM-SHA256": True,
            "AES256-GCM-SHA384": True,
            "AES128-SHA": True,
            "AES128-SHA256": True,
            "AES256-SHA": True,
            "AES256-SHA256": True,
            "CAMELLIA128-SHA": True,
            "CAMELLIA256-SHA": True,
            "DES-CBC3-MD5": False,
            "DES-CBC3-SHA": False,
            "DES-CBC-MD5": False,
            "DES-CBC-SHA": False,
            "DHE-DSS-AES128-GCM-SHA256": True,
            "DHE-DSS-AES256-GCM-SHA384": True,
            "DHE-DSS-AES128-SHA": True,
            "DHE-DSS-AES128-SHA256": True,
            "DHE-DSS-AES256-SHA": True,
            "DHE-DSS-AES256-SHA256": True,
            "DHE-DSS-CAMELLIA128-SHA": False,
            "DHE-DSS-CAMELLIA256-SHA": False,
            "DHE-DSS-SEED-SHA": False,
            "DHE-RSA-AES128-GCM-SHA256": True,
            "DHE-RSA-AES256-GCM-SHA384": True,
            "DHE-RSA-AES128-SHA": True,
            "DHE-RSA-AES128-SHA256": True,
            "DHE-RSA-AES256-SHA": True,
            "DHE-RSA-AES256-SHA256": True,
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
            "Protocol-TLSv1.1": True,
            "Protocol-TLSv1.2": True,
            "PSK-3DES-EDE-CBC-SHA": False,
            "PSK-AES128-CBC-SHA": False,
            "PSK-AES256-CBC-SHA": False,
            "PSK-RC4-SHA": False,
            "RC2-CBC-MD5": False,
            "RC4-MD5": False,
            "RC4-SHA": True,
            "SEED-SHA": False}
        self.conn_elb = boto.ec2.elb.connect_to_region(region)


    def create_policy(self):
        params = {'LoadBalancerName': self.load_balancer_name,
                  'PolicyName': self.policy_name,
                  'PolicyTypeName': 'SSLNegotiationPolicyType'}
        self.conn_elb.build_complex_list_params(params, 
                                           [(x, policy_attributes[x]) for x in policy_attributes.keys()],
                                           'PolicyAttributes.member',
                                           ('AttributeName', 'AttributeValue'))
        self.policy = conn_elb.get_list('CreateLoadBalancerPolicy', params, None, verb='POST')
        
    def apply_policy(self):
        # Apply the Ciphersuite Policy to your ELB
        params = {'LoadBalancerName': self.load_balancer_name,
                  'LoadBalancerPort': 443,
                  'PolicyNames.member.1': self.policy_name}
        
        result = self.conn_elb.get_list('SetLoadBalancerPoliciesOfListener', params, None)
        print "New Policy '%s' created and applied to load balancer %s in %s" % (self.policy_name, self.load_balancer_name, self.region)

    def show_policy(self):
        load_balancer = self.conn_elb.get_all_load_balancers([self.load_balancer_name])[0]
        if len(load_balancer.policies.other_policies) == 0:
            print("%s has no policies of type 'SSLNegotiationPolicyType'" % self.load_balancer_name)
            return False
        policy_name = load_balancer.policies.other_policies[0].policy_name
        params={'LoadBalancerName': load_balancer.name}
        self.conn_elb.build_list_params(params, [policy_name], 'PolicyNames.member.%d')
    
        all_policies = self.conn_elb.get_list('DescribeLoadBalancerPolicies', 
                                          params, 
                                          [('member', PolicyDescription)])
        ssl_policies = [x for x in all_policies if x.policy_type_name == 'SSLNegotiationPolicyType']

        if len(ssl_policies) == 0:
            print("%s has no policies of type 'SSLNegotiationPolicyType'" % self.load_balancer_name)
            return False

        print("load_balancer : %s" % self.load_balancer_name)
        print("policy_name : %s" % ssl_policies[0].policy_name)
        
        policy_attributes = ssl_policies[0].policy_attribute_descriptions
        result = {}
        for policy_element in policy_attributes:
            result[policy_element.attribute_name] = policy_element.attribute_value
        for cipher in sorted(result.iteritems(), key=operator.itemgetter(0)):
            print("%s\t%s" % (cipher[0], cipher[1]))

    def show_all_policies(self):
        all_load_balancers = self.conn_elb.get_all_load_balancers()
        load_balancers = [x for x in all_load_balancers if len(x.policies.other_policies) > 0]
        if len(load_balancers) == 0:
            # There are no ELBs in this region that have SSLNegotiation policies
            return False
    
        example_load_balancer = load_balancers[0]
        example_policy_name = example_load_balancer.policies.other_policies[0].policy_name
    
        params={'LoadBalancerName': example_load_balancer.name}
        self.conn_elb.build_list_params(params, [example_policy_name], 'PolicyNames.member.%d')
    
        policies = self.conn_elb.get_list('DescribeLoadBalancerPolicies', 
                                          params, 
                                          [('member', PolicyDescription)])
        example_policies = [x for x in policies if x.policy_type_name == 'SSLNegotiationPolicyType']

        print("load_balancer : %s" % example_load_balancer.name)
        print("policy_name : %s" % example_policy_name)

        policy_attributes = example_policies[0].policy_attribute_descriptions
        result = {}
        for policy_element in policy_attributes:
            result[policy_element.attribute_name] = policy_element.attribute_value
        for cipher in sorted(result.iteritems(), key=operator.itemgetter(0)):
            print("%s\t%s" % (cipher[0], cipher[1]))

def main():
    if len(sys.argv) < 2:
        print "usage : %s REGION ELB-NAME" % sys.argv[0]
        print ""
        print "Example : %s us-west-2 persona-org-0810" % sys.argv[0]
        sys.exit(1)
    
    cipher_suite = CipherSuite(region=sys.argv[1],
                               load_balancer_name=sys.argv[2])
    #cipher_suite.create_policy()
    #cipher_suite.apply_policy()
    cipher_suite.show_policy()
    #cipher_suite.show_all_policies()

if __name__ == "__main__":
    main()
