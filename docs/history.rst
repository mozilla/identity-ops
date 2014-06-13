***************************
Persona operational history
***************************

This document seeks to detail the operational history of Persona in order to give context to the current design as well as highlight lessons learned from previous designs.

V1
==

The first incarnation of Persona, then called BrowserID was a design by `Pete Fritchman`_ from October 2011. It consisted of

* Physical servers
* Dual datacenter deployment: ``phx1``, ``scl2``
* `Zeus software load balancers`_ doing layer 3 load balancing in front of the clusters of physical servers
* MySQL database backend with a single global master DB and clusters of read-only slaves in each datacenter
* `RSBAC`_ providing kernel level security
* Puppet provisioning using a fork of the old infra team puppet repository (code located in ``svn.mozilla.org/sysadmins/puppet/weave/modules/browserid`` )
* Manual physical deployment of servers and manual installation and configuration of Puppet
* Monitoring

  - Logstash parsing logs on servers and emitting them via `statsd`_ to a RabbitMQ bus
  - `Graphite`_ consuming this statsd data from the bus for performance monitoring and data visualization
  - `Pencil`_ rendering dashboards containing the graphite graphs
  - `Cepmon`_ also consuming the statsd data off the RabbitMQ bus which applied `esper`_ processing and `complex event processing`_ to the statsd data
  - `Nagios cepmon plugin`_ which interrogated `Cepmon`_ to trigger `Nagios`_ to send alerts
  - `Nagios`_ which also executed various active checks against servers
  
  .. _Nagios: http://www.nagios.org/
  .. _complex event processing: http://en.wikipedia.org/wiki/Complex_event_processing
  .. _Nagios cepmon plugin: https://github.com/fetep/cepmon-nagios
  .. _esper: http://esper.codehaus.org/
  .. _Cepmon: https://github.com/fetep/cepmon
  .. _Pencil: .. _statsd: https://github.com/etsy/statsd/
  .. _statsd: https://github.com/etsy/statsd/
  .. _Graphite: https://github.com/graphite-project/graphite-web

.. _RSBAC: http://www.rsbac.org/
.. _Pete Fritchman: https://github.com/fetep
.. _Zeus software load balancers: http://www.riverbed.com/us/products/stingray/

V2
==

The second incarnation of Persona was a design by `Gene Wood`_ and `Jared Hirsch`_  from January 2013. The new AWS installation of Persona was completed and cutover to around April 2013. It consists of

* `AWS`_ virtual servers
* Dual region deployment: ``us-west-2``, ``us-east-1``
* `AWS`_ load balancers in front of clusters of autoscaled ec2 instances
* MySQL database backend with a single global master DB and clusters of read-only slaves in each datacenter. The single global master DB is the only physical server in the design and resides in the ``phx1`` datacenter
* VPN links between AWS regions and the ``phx1`` datacenter to enable writing to the master DB
* Chef provisioning using `greenfield`_ provisioning code specific to Persona (code located at https://github.com/mozilla/identity-ops/ )
* Python boto driven creation of AWS resources and enabling of Chef provisioning on instances using `stack_control`_ 
* Monitoring

  - EC2 instances self-registering themselves with the `Opsview core`_ server upon creation
  - `Opsview core`_ actively monitoring the service and instances
  - Graphite consuming data from `cloudwatch2graphite`_ which in turn fetches cloudwatch metrics on the ELB load balancers
  - Graphite visualizing this cloudwatch data
  - No traditional CPU memory monitoring beyond what Cloudwatch provides
  
  .. _cloudwatch2graphite: cloudwatch_graphite_connector.rst
  .. _Opsview core: http://www.opsview.com/solutions/core

.. _stack_control: https://github.com/mozilla/identity-ops/blob/master/aws-tools/stack_control.rst
.. _greenfield: http://en.wikipedia.org/wiki/Greenfield_project
.. _AWS: http://aws.amazon.com/
.. _Jared Hirsch: https://github.com/6a68
.. _Gene Wood: https://mozillians.org/en-US/u/gene/
