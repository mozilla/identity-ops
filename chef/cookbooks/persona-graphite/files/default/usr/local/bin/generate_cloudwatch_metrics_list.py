#!/usr/bin/env python
import boto.ec2.elb
import boto.utils
import json
import copy
import logging

# logging.basicConfig(level=logging.DEBUG)

metadata=boto.utils.get_instance_metadata()
region=metadata['placement']['availability-zone'][:-1] if metadata != None else 'us-west-2'
conn_elb = boto.ec2.elb.connect_to_region(region)
load_balancers = conn_elb.get_all_load_balancers()
persona_load_balancer_names = ['persona-org', 
                               'w-anosrep-org', 
                               'w-login-anosrep-org',
                               'dbwrite', 
                               'dbread-univ', 
                               'keysign', 
                               'proxy-univ',
                               'yahoo-login-persona-org', 
                               'yahoo-login-anosrep-org', 
                               'gmail-login-anosrep-org',
                               'gmail-login-persona-org']
base_metrics=[
  {
  "Namespace": "AWS/ELB",
  "MetricName": "HealthyHostCount",
  "Statistics.member.1": "Sum",
  "Unit": "Count",
  "Dimensions.member.1.Name":"LoadBalancerName",
  "Dimensions.member.1.Value":""
  },
  {
  "Namespace": "AWS/ELB",
  "MetricName": "HTTPCode_Backend_2XX",
  "Statistics.member.1": "Sum",
  "Unit": "Count",
  "Dimensions.member.1.Name":"LoadBalancerName",
  "Dimensions.member.1.Value":""
  },
  {
  "Namespace": "AWS/ELB",
  "MetricName": "HTTPCode_Backend_3XX",
  "Statistics.member.1": "Sum",
  "Unit": "Count",
  "Dimensions.member.1.Name":"LoadBalancerName",
  "Dimensions.member.1.Value":""
  },
  {
  "Namespace": "AWS/ELB",
  "MetricName": "HTTPCode_Backend_4XX",
  "Statistics.member.1": "Sum",
  "Unit": "Count",
  "Dimensions.member.1.Name":"LoadBalancerName",
  "Dimensions.member.1.Value":""
  },
  {
  "Namespace": "AWS/ELB",
  "MetricName": "HTTPCode_Backend_5XX",
  "Statistics.member.1": "Sum",
  "Unit": "Count",
  "Dimensions.member.1.Name":"LoadBalancerName",
  "Dimensions.member.1.Value":""
  },
  {
  "Namespace": "AWS/ELB",
  "MetricName": "RequestCount",
  "Statistics.member.1": "Sum",
  "Unit": "Count",
  "Dimensions.member.1.Name":"LoadBalancerName",
  "Dimensions.member.1.Value":""
  },
  {
  "Namespace": "AWS/ELB",
  "MetricName": "Latency",
  "Statistics.member.1": "Average",
  "Unit": "Seconds",
  "Dimensions.member.1.Name":"LoadBalancerName",
  "Dimensions.member.1.Value":""
  },
  {
  "Namespace": "AWS/ELB",
  "MetricName": "Latency",
  "Statistics.member.1": "Maximum",
  "Unit": "Seconds",
  "Dimensions.member.1.Name":"LoadBalancerName",
  "Dimensions.member.1.Value":""
  }
]
metrics = {"metrics": [],
           "region": region,
           "interval_minutes": 1}
names = []

for load_balancer in load_balancers:
  logging.debug("Processing %s as %s" % (load_balancer.name, '-'.join(load_balancer.name.split('-')[:-1])))
  if '-'.join(load_balancer.name.split('-')[:-1]) in persona_load_balancer_names:
    lb_metrics = copy.deepcopy(base_metrics)
    for x in lb_metrics:
      x['Dimensions.member.1.Value'] = load_balancer.name
    metrics['metrics'].extend(lb_metrics)
    stack = load_balancer.name.split('-')[-2:][0] if load_balancer.name.split('-')[-1:][0] in ['stage','prod'] else load_balancer.name.split('-')[-1:][0]
    name =  '-'.join(load_balancer.name.split('-')[:-2]) + '.' + load_balancer.name.split('-')[-1:][0] if load_balancer.name.split('-')[-1:][0] in ['stage','prod'] else '-'.join(load_balancer.name.split('-')[:-1])
    names.append({"aws_name": load_balancer.name,
                  "graphite_name": "%s.%s" % (stack, name)})

with open('/opt/cloudwatch2graphite/conf/metrics.json', 'w') as f:
  f.write(json.dumps(metrics, sort_keys=True, indent=4, separators=(',', ': ')))

with open('/opt/cloudwatch2graphite/conf/names.json', 'w') as f:
  f.write(json.dumps(names, sort_keys=True, indent=4, separators=(',', ': ')))
