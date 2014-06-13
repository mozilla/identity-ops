*************************
Persona application tiers
*************************

Webhead
=======

These are the frontend webservers that client browsers interact with. They can read from the database and make requests to the ``dbwrite`` and ``keysign`` tiers.

Keysign
=======

This tier holds the Persona private key and is separate from the `webhead` tier to improve security. This tier accepts connections from the `webhead` tier.

Dbwrite
=======

This tier holds the db user and password combination that is able to write to the global master database and is separate from the `webhead` tier to improve security. This tier accepts connections from the `webhead` tier.

Bridge-gmail
============

This tier is entirely decoupled from Persona and acts as a standalone gateway between Persona and Google. This applications internal name is ``sideshow``

Bridge-yahoo
============

This tier is entirely decoupled from Persona and acts as a standalone gateway between Persona and Yahoo. This applications internal name is ``bigtent``

Dbread
======

This tier consists of 3 non-autoscaled MySQL DB read-only slaves which replicate either off of their regional parent read-only slave, or off of the global master DB if they are the regional parent read-only slave. Here is a diagram of the replication topology

.. image:: https://wiki.mozilla.org/images/5/5e/Persona_MySQL_Replication_Topology.png

This tier accepts connections from the `webhead` tier.

`More information on building slaves`_ 

.. _More information on building slaves: db.rst

Db
==

This tier isn't so much a tier as just the single global db write master which is hosted on physical hardware in the ``phx1`` datacenter. It accepts connections from the ``dbwrite`` tier over standing VPN links between the Persona VPCs in each region

Proxy
=====

This tier acts as an outbound proxy server to do complex outbound internet filtering. This tier exists to improve security by constraining what internet addresses persona instances can initiate connections out to. All identity apps send all outbound internet connections through this proxy tier. Currently, the ``identity-prod-temp-internet`` and ``identity-stage-temp-internet`` security groups grant all Persona instances the ability to initiate connections out to the internet. This somewhat compromises the security that the ``proxy`` tier adds but not completely. The reason that these temporary security groups exist is to enable instances to initiate connections to the AWS API during provisioning.

.. note:: This security weakness caused by the temporary security groups could be obviated by adding rules into the proxy tier granting access to the AWS API endpoints and updating the provisioning code to utilize the proxy tier.

This tier is a manually created autoscale group. This is different than the ephemeral autoscale groups created by `stack_control`_ and different from the long lived non-autoscaled instances like the ``dbread``, ``monitor`` and ``graphite`` tiers.

The identity applications do not use the ``HTTP CONNECT`` method to fetch https pages via the proxy. They instead merely pass the URL that they're trying to reach as the path to squid (just as if it were an http page, not https) : https://github.com/mozilla/browserid/blob/fe731c56ea3604ba79566a5da796be4c25ff404f/lib/primary.js#L143

As a result of this, the proxy servers are configured to not allow ``HTTP CONNECT`` (and testing using that method wouldn't be useful anyhow since it wouldn't mirror how the identity apps behave). curl *only* uses the ``HTTP CONNECT`` method and consequently will not work when testing https URLs through the proxy. To test you'll need to use another method, for example a small python script

.. code-block:: bash

    echo "import httplib
    conn = httplib.HTTPConnection('idproxy.idweb', 8888)
    conn.request('GET', 'https://eyedee.me/.well-known/browserid?domain=eyedee.me')
    req = conn.getresponse()
    print req.status, req.reason
    for h in req.getheaders():
     print h
    print req.read()" | python

To test a KPI post you'll want to try something like : 

.. code-block:: bash

    echo "import httplib
    import urllib
    conn = httplib.HTTPConnection('idproxy.idweb', 8888)
    conn.request('POST', 'https://kpiggybank-stage.personatest.org/wsapi/interaction_data', urllib.urlencode({'foo':'bar'}))
    req = conn.getresponse()
    print req.status, req.reason
    for h in req.getheaders():
      print h
    print req.read()" | python

To get more detailed logging information from the squid servers you can add this to the ``/etc/squid/squid.conf``

::

    # Temporary troubleshooting debug logging
    #debug_options ALL,1 33,2
    debug_options ALL,1 33,2 28,9

This will output detailed logs into ``/var/log/squid/cache.log`` 

.. _stack_control: https://github.com/mozilla/identity-ops/blob/master/aws-tools/stack_control.rst

Monitor
=======

This tier runs the Opsview core monitoring software. This service is accessed directly by self-registering instances over these servers private IPs. This service is accessed from the internet via the ``graphite`` tier which hosts the Identity-gateway service, providing an additional authentication layer in front of Opsview core. This tier is a manually instantiated single instance per region and environment

`More information on Opsview`_ 

.. _More information on Opsview: monitor.rst#monitor-tier-opsview

Graphite
========

This tier runs Graphite which collects metrics from Cloudwatch and stores and visualizes them. It also hosts the Identity-gateway services which provides persona authentication in front of administrative web UIs. This tier is a manually instantiated single instance per region and environment.

`More information on Graphite`_ and `the Identity-gateway service`_ 

.. _the Identity-gateway service: monitor.rst#identity-gateway
.. _More information on Graphite: monitor.rst#graphite-tier

Metrics
=======

This tier acts as a data weigh station between the ``webhead`` tier and the metrics team. This tier exists to provide a layer of security between the two different security zones. This tier is a manually instantiated single instance per region.

`More information on Metrics`_ 

.. _More information on Metrics: pentaho_metrics.rst

Admin
=====

This tier is the bastion host tier. This tier accepts inbound ssh connections from the internet and is trusted by Persona instances to initiate ssh outbound connections to them. 

`More information on accessing the admin tier`_ 

.. _More information on accessing the admin tier: access.rst#sshing-into-hosts

Builder
=======

This tier holds the gpg private keys for all instances and is used to create new identity application stacks. This tier has permissions to create and destroy stacks. This tier is a manually instantiated single instance per region and environment.

`More information on deploying identity applications`_ 

.. _More information on deploying identity applications: deploy.rst

External services
=================

KPI
---

