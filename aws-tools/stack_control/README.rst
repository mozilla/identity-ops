*************
Stack Control
*************

`stack_control.py`_ can be used to create, destroy and show information on Identity application stacks

This tool uses the `boto`_ library to interact with the AWS API. To authenticate to the AWS API you need either to run this tool from an EC2 instance with an IAM role granting the system access to the API, or to enter your API credentials into a boto config file ( http://boto.readthedocs.org/en/latest/boto_config_tut.html#credentials ). 

``stack_control.py`` is typically run from a ``persona-builder`` server which has the needed permissions to create new Identity stacks.

.. _boto: http://boto.readthedocs.org/
.. _stack_control.py: https://github.com/mozilla/identity-ops/blob/master/aws-tools/stack_control.py

Config Files
============

These config files exist for various environments and application tiers

* config/autoscale.prod.json : Describes the autoscale groups to create and the load balancers to bind them to. This example applies to the prod environment.
* config/elbs_public.stage.json : Describes the public internet facing ELB load balancers to create. This example applies to the stage environment.
* config/elbs_private.prod.json : Describes the private internal ELB load balancers to create. This example applies to the prod environment.
* config/webhead@login.anosrep.org.priv : Contains the GPG private key to pass to the instance which will be used to decrypt secrets. This example applies to the webhead tier in the stage environment.
* config/ami_map.json : Describes the one to many mapping of AMI revisions to per-region AMI images.

Usage
=====

::

    usage: stack_control.py [-h] [-p PATH] [-r {us-west-2,us-east-1}]
                            [-e {stage,prod}]
                            {destroy,create,show} ...

    stack_control can be used to create, destroy and show information on Identity application stacks

    positional arguments:
      {destroy,create,show}
                            sub-command help
        create              create --help
        destroy             destroy --help
        show                show --help

    optional arguments:
      -h, --help            show this help message and exit
      -p PATH, --path PATH  ARN Path prefix (default : /identity/)
      -r {us-west-2,us-east-1}, --region {us-west-2,us-east-1}
                            AWS region (default : us-west-2)
      -e {stage,prod}, --environment {stage,prod}
                            Environment (default : stage)

    usage: stack_control.py create [-h] [-g GIT] name

    positional arguments:
      name               Stack name

    optional arguments:
      -h, --help         show this help message and exit
      -g GIT, --git GIT  git branch name or commit hash to instruct instances to
                         draw from for their identity-ops chef code (default:
                         HEAD)

    usage: stack_control.py destroy [-h] name

    positional arguments:
      name        Stack name

    optional arguments:
      -h, --help  show this help message and exit

Create
======

The create function follows these steps

1. Create each load balancer define in the ``elbs_public`` config file

   a) Set the health check and ssl cipher suite on each load balancer

2. Create each load balancer defined in the ``elbs_private`` config file

   a) Set the health check on each load balancer

3. For each autoscale group defined in the ``autoscale`` config file

   a) Create the launch configuration
   b) Create the autoscale group bound to the launch configuration with a desired capacity of 0
   c) Tag the autoscale group
   d) Increase the desired capacity of the autoscale group to the target cluster size


Destroy
=======

The destroy function follows these steps

1. Delete existing cloudwatch alarms
2. Initiate instance shutdown on all autoscale groups on all instances
3. Wait, querying the API every 10 seconds for the instances to complete shutdown
4. Delete autoscale groups after all instances have shut down
5. Delete all launch configurations
6. Delete all load balancers

Currently stack_control does not call or integrate with `opsivew_control.rb`_. As a result, prior to destroying a stack it's best to destroy the monitors for the stack to avoid causing Opsview to send false positive alerts. More information on how to use opsview_control.rb can be found in the `opsview_control documentation`_ 

.. _opsivew_control.rb: https://github.com/mozilla/identity-ops/blob/master/opsview-tools/opsview_control.rb

Show
====

The show function outputs a block of text in Markdown wrapped JSON describing the load balancers of the stack

.. _opsview_control documentation: https://github.com/mozilla/identity-ops/blob/master/opsview-tools/opsview_control.rst

How to Build
============

::

    sudo yum install http://ftp.linux.ncsu.edu/pub/epel/6/i386/epel-release-6-8.noarch.rpm
    sudo yum install rubygems ruby-devel gcc python-setuptools rpm-build
    sudo easy_install pip
    sudo gem install fpm
    git clone https://github.com/mozilla/identity-ops.git
    
    cd identity-ops/aws-tools/stack_control # This is required
    fpm -s python -t rpm --workdir ../ ./setup.py
