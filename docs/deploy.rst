**********
Deployment
**********

Stacks
======

Identity applications are organized into ``stacks``. Each stack contains a collection of services which, together, form a cohesive grouping. For example, stack ``1120`` would contain autoscale groups of the following server types, each with an ELB in front

* Persona webhead servers
* Persona keysign servers
* Persona dbwrite servers
* Identity Bridge Gmail servers
* Identity Bridge Yahoo servers

A stack exists in a single AWS region. Stacks with the same name may be present in different regions but they are distinct separate stacks.

Stacks are ephemeral and live only as long as a given application version or provision code version needs to exist. When deploying new application code or provisioning code, a new stack is created with the new code. It exists in addition to the current live stack. Traffic is then moved from the live stack running the old code to the new stack running the new code. Finally, the old stack is destroyed.

A stack is identified by a four or less character name. By convention we use the month and day that the stack was built as it's unique name, for example ``0630``. 

The ``univ`` stack in each region is special. This "universal" stack is not ephemeral, it is long lived. It contains services which

* contain persistent data (databases)
* rarely changes and doesn't need to be in the application stacks (proxy, admin)
* needs to exist above and outside of the applications stacks (monitor, graphite, builder)

Most of the services in these ``univ`` stacks in each region are not autoscaled, and are built manually. This is mainly due to the fact that they are long lived and don't need to be destroyed and rebuilt often.

Updating to a new Identity application version
==============================================

In order to bind a version of Chef provisioning code to a set of identity application versions, we set the application version in the cookbook default attributes. This enables linking a new application version to infrastructural changes (like new config file settings).

Here's an example of the process to update to a new version of Persona. Let's say you've built the new Persona rpm ``browserid-server-0.2014.11.27-1.el6_149046.x86_64.rpm``.

1. Checkout a copy of the `identity-ops`_ repo if you don't have one.
2. Edit the ``default.rb`` attributes file for the three tiers that install the Persona app

   a) The ``webhead``, ``keysign``, and ``dbwrite`` tiers all install the same RPM. This stems from the fact that in dev these are all hosted on the same system. This means that a change to any one tier results in a need to update all three tiers.
   b) The location of the default attributes file in each cookbook is at ``attributes/default.rb``

      i. `identity-ops/chef/cookbooks/persona-dbwrite/attributes/default.rb`_ 
      ii. `identity-ops/chef/cookbooks/persona-keysign/attributes/default.rb`_
      iii. `identity-ops/chef/cookbooks/persona-webhead/attributes/default.rb`_ 
      
      .. _identity-ops/chef/cookbooks/persona-dbwrite/attributes/default.rb: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-dbwrite/attributes/default.rb
      .. _identity-ops/chef/cookbooks/persona-keysign/attributes/default.rb: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-keysign/attributes/default.rb
      .. _identity-ops/chef/cookbooks/persona-webhead/attributes/default.rb: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-webhead/attributes/default.rb
3. Modify the appropriate attribute to reflect the new RPM version. For example, the ``persona-dbwrite`` cookbook would require editing the ``default["persona"]["dbwrite"]["rpms"]["browserid-server"]`` attribute
4. Edit any configuration files that have new or deleted config settings. For example if the dbwrite tier has a new configuration value, edit the `templates/default/opt/browserid/config/production.json.erb`_ file
5. Commit your changes to git

   a) Either note the commit hash so you can later build a stack at that hash
   b) or commit your changes to a branch to reference later. Using a branch would enable you to only keep production ready code in ``master``.

.. _templates/default/opt/browserid/config/production.json.erb: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-dbwrite/templates/default/opt/browserid/config/production.json.erb

.. _identity-ops: https://github.com/mozilla/identity-ops/

An alternative, less desirable, method to assert the rpm version is in the secrets json file hosted in S3. This results in the Chef provisioning code not being bound to the application version.

Automatic deployment
====================

1. If the new stack is to have a new application version of an identity application, then that new code needs to be built and packaged. Details on that can be found in the documentation on `building identity applications and uploading the resulting packages`_.
2. The new stack will either require new Chef provisioning code or new identity application code or both. The version of the identity applications to run in a stack are defined in the provisioning code. More detail on that can be found above in the `Updating to a new Identity application version`_ section.
3. If the ``include.js`` content has changed with this new release

   a) Determine the new sha1 hash of ``include.js``
   b) If this is prod, and stage currently matches the application code being deployed, the new hash can be determined with:

   .. code-block:: bash

        curl -k https://login.anosrep.org/include.js | sed 's/anosrep/persona/g' | sha1sum
   c) If this is prod, and stage doesn't currently match, then deploy a stage stack that does, find the ``w-anosrep-org`` elb (with ``get_hosts``) and determine the new hash like this:

   .. code-block:: bash

        # replace 9999 with the stack number
        # replace 123456789 with the resource id you retrieved via: get_hosts -e 9999
        curl -k https://w-anosrep-org-9999-123456789.us-west-2.elb.amazonaws.com/include.js | sed 's/anosrep/persona/g' | sha1sum
   d) If this is stage, then execute step 4, come back and use step 3.c to get the hash
   e) Add this to the ``/etc/allowed-hashes.txt`` file on the monitoring server for that environment and region.
   f) If this is prod, update the Nimsoft monitor to reflect this new hash as well
   g) More information on these monitoring changes can be found in the `monitoring documentation`_

4. SSH into the persona-builder instance in the desired environment and region (via the bastion host) and run ``stack_control.py`` passing in the git hash or branch name that came out of `Updating to a new Identity application version`_. More information on running ``stack_control.py`` can be found in the `stack_control.py documentation`_
5. Observe the Opsview monitors of the new stack, confirming that all the instances have hydrated and are green on all monitors.

   You can also track the progress of the instances by watching the chef logs

   .. code-block:: bash

        stack=0803
        for host in `get_hosts $stack`; do echo $host;while ! ssh -o ConnectTimeout=2 -o StrictHostKeyChecking=no $host 'a="`tail -1 /var/log/chef.log`"; echo "$host `date` $a";echo "$a" | grep "`date +%Y-%m-%d`.*Report handlers complete"'; do sleep 2; done; done
6. Communicate the stack name of the new stack to QA. Have QA test the new stack before it gets live traffic. Services QA has scripts that make it easy to fake DNS into using the new stack.
7. Once QA signs off on the stack, update DNS to point to it. More info on how to do this can be found in the `Updating DNS`_ section.
8. Notify QA that the new stack is live so they can test public relying parties with the new code.
9. The following day, or at a point later than that when you feel comfortable with the stability of the new production stack, tear down the old stack. You want to wait a day so that Pentaho metrics get sent from the old stack for the final day that the stack received traffic.

.. note:: Opsview has a bug which causes a potential race condition when creating "Host Groups". This can be worked around by either creating the empty host group in opsview prior to spinning up a new stack or by hoping that the bug doesn't surface and if it does, deleting the duplicate empty host group, then re-running chef-solo across the stack. If the bug does surface it will cause the slower instances in the stack to fail to self-register themselves with the Opsview server. You can see this manifest by the number of instances in a stack in Opsview showing up as fewer than you'd expect.

.. note:: Updating monitoring with the new include.js sha1 hash *after* deploying a new stack is the wrong way to go about things. The better way would be to either require dev to convey any include.js changes and the new sha1 hash in a deployment ticket or to somehow determine the new hash before deploying the stack.

Manual deployment
=================

Some tiers are not autoscaled and consequently are manually deployed. This process could be scripted but as it is done infrequently it hasn't been yet. These manually deployed instances are part of the ``univ`` stack. These instructions are generic and apply to any non autoscaled tier such as

* ``graphite``
* ``admin``
* ``monitor``
* ``dbread``
* ``builder``

1. Create an ec2 instance either on the command line or web gui

   a) size : check the tiers documentation
   b) IAM role : check the tiers documentation
   c) vpc and subnet : The VPC of the environment you want to deploy in
   d) AMI ID : A persona-base AMI
   e) Security Groups : check the tiers documentation

2. Create ec2 instance tags (``get_hosts`` won't find your instance without these)

   a) App : ``identity``
   b) Env : ``stage`` or ``prod``
   c) Stack : ``univ``
   d) Tier : ``admin``, ``builder``, ``monitor``, etc.

3. Inject the secrets

   a) Obtain the secrets from the secrets s3 bucket
   b) Obtain the instances gpg private key from the persona-builder instance
   c) Decrypt the secrets and write them to ``/etc/chef/node.json``

4. Fetch the current or specific desired revision of the ``identity-ops`` git repo (this is where the chef configs will be taken from).

   .. code-block:: bash

      cd /root/identity-ops && git pull && git checkout HEAD

5. Hydrate the machine with Chef

   .. code-block:: bash

      chef-solo -c /etc/chef/solo.rb -j /etc/chef/node.json

6. Once the machine is up and healthy, set the DNS records in the ``stage.mozaws.net`` or ``prod.mozaws.net`` zones to reference the new instance. These zones are hosted in AWS Route 53 in the ``mozilla`` AWS Account.

7. This only applies to the ``builder`` tier: copy gpg private key files to ``/etc/stack_control``

   a) make sure you have one key for each tier deployed by ``stack_control``

Updating DNS
============

DNS is hosted with `Dynect`_. Records can be updated through the web UI or their API. Unsurfaced code exists in ``stack_control.py`` in the ``point_dns_to_stack`` method which uses the Dynect API to update the DNS for a staging deploy. The code to do the same for production doesn't yet exist. That code would require interacting with the "Traffic Management" portion of the Dynect API.

Since we have a single staging environment (in ``us-west-2``), staging DNS records are simple CNAMEs. Production is hosted in two regions (``us-west-2`` and ``us-east-1``) and is DNS load balanced using Dynect's "Traffic Management" service. This results in two AWS ELB load balancers being associated with each Dynect DNS name, one for each region.

Our Dynect DNS records have 30 second TTLs. Browsers do not typically re-resolve DNS names at the rate the TTL requires therefore additional steps need to be taken to force users to follow the updated DNS. We remove the listeners from our old ELB load balancers to force browsers to fail to connect to the old stack and do a DNS lookup to get the new IPs. We remove listeners (as opposed to destroying the ELBs) in order to retain control of the IP addresses of the old stack's ELBs. This is to prevent the IPs being re-used by a different AWS customer resulting in clients going to other customer sites and getting certificate errors when they're served some other company's SSL cert.

Typically, each loosely coupled identity service (persona, bridge-gmail, bridge-yahoo) is switched from an old stack to a new stack serially to reduce user impact. This is done in contrast to switching all services simultaneously. This is the process that we execute for each service, serially.

1. Identify the names of the load balancers of the new stack that you'd like to point DNS names at

   This is most easily done with the ``get_hosts`` script available on all bastion hosts. For example to determine the load balancers of the new production stack ``1120`` in ``us-east-1`` you could either, from the production bastion host in ``us-east-1``, run

   .. code-block:: bash
   
       get_hosts --elb 1120

   or from any bastion host

   .. code-block:: bash
   
       get_hosts --elb --region us-east-1 --env prod 1120

2. Log into `Dynect`_ with your user account.
3. Navigate to the zone containing either the DNS records (stage) or the "Traffic Management" groups (production).
4. Update the record or records to CNAMEs pointing to the new load balancers and publish the change. 

   .. note:: This could be improved by making these changes using the Dynect API. See the ``point_dns_to_stack`` method in ``stack_control.py`` to see how to do it in staging.
5. Browse to the AWS web UI and locate the ELBs for the old stack
   You can determine the existing ELBs by running the same command as above and point to the old stack name
6. Once 30 seconds has elapsed since you updated the DNS (30 seconds is the DNS TTL) modify the listener for the tier that you've just changed DNS for.
   
   Change any https listeners from port ``443`` to ``10443``. Change any http listeners from port ``80`` to ``10080``.
   This will force any clients still communicating with the old stack to be forced to query DNS and connect to the new stack.

   .. note:: This process could be improved by handling these listener changes with AWS API calls.

.. _Dynect: http://manage.dynect.net/

.. _monitoring documentation: monitor.rst

.. _stack_control.py documentation: https://github.com/mozilla/identity-ops/blob/master/aws-tools/stack_control.rst

.. _building identity applications and uploading the resulting packages: build.rst
