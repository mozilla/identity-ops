**********
Monitoring
**********

Availability monitoring is monitoring which detects the availability of a service. This can either be done pro-actively by interrogating the service (e.g. every 5 minutes fetch a web page) or after the fact by observing logs (e.g. searching for non-200 HTTP codes in access logs). Availability monitoring frequently triggers push notifications to operations engineers.

Performance monitoring is the process of gathering metrics on a system's performance, recording them and visualizing them. Performance monitoring data is typically consumed in a pull model where operations engineers opt to view the performance monitoring system's data visualizations.

Monitor tier (Opsview)
======================

* tier name : ``monitor``

`Opsview core`_ is our primary availability monitoring system. We use it to actively interrogate the Identity applications as well as provide very limited performance monitoring.

.. _Opsview core: http://www.opsview.com/solutions/core

Accessing Opsview
-----------------

Each AWS region and environment in which we host Persona has an Opsview installation to monitor that deployment.

Opsview provides both a web UI and a REST API.

+-------------+-----------+------------------------------------------------------+
| environment | region    | Opsview Web UI URL                                   |
+=============+===========+======================================================+
| staging     | us-west-2 | https://monitor.identity.us-west-2.stage.mozaws.net/ |
+-------------+-----------+------------------------------------------------------+
| production  | us-west-2 | https://monitor.identity.us-west-2.prod.mozaws.net/  |
+-------------+-----------+------------------------------------------------------+
| production  | us-east-1 | https://monitor.identity.us-east-1.prod.mozaws.net/  |
+-------------+-----------+------------------------------------------------------+

These URLs use the `Identity Gateway`_ service which runs on the Graphite_ servers. To access them you'll need
to authenticate with Persona using your email address which is on the `approved list of users`_. 

Once you've authenticated with your email address you'll be presented with the Opsview application login screen. Here, login with the shared credentials which can be found at ``svn.mozilla.org/sysadmins/gpg/services/passwords.txt.gpg``. For staging you can login as either the read-only user ``identity`` with the password ``identity`` or as the administrator with the username ``admin`` and the password ``initial``.

As the REST API is currently also behind the `Identity Gateway`_ Persona authentication some trickery is requires to use the REST API (like passing in pre-generated Persona session cookies with your API calls)

.. _approved list of users: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/identity-gateway/files/default/var/www/mod_browserid_users

Deploying the monitor tier
--------------------------

Opsview instances are not autoscaled as there is only one in each region/environment combination.

The monitor tier's Chef provisioning code can be found here : https://github.com/mozilla/identity-ops/tree/master/chef/cookbooks/persona-monitor

1. Create an ec2 instance by following the Manual Deployment instructions

   * size : ``m1.small``
   * IAM role : ``identity``
   * Security Groups : ``identity-dev-monitor``, ``identity-dev-administrable``, ``identity-dev-temp-internet``

2. Populate the now running Opsview instance with monitors and monitoring templates.

   This is best done by taking an export from an existing Opsview instance using `opsview_control.rb`_ and importing it with the same tool
   
   .. _opsview_control.rb: https://github.com/mozilla/identity-ops/blob/master/opsview-tools/opsview_control.rb


Graphite tier
=============

* tier name : ``graphite``

`Graphite`_ collects, records and visualizes performance monitoring data. This tier also hosts the `Identity Gateway`_ service.

.. _Graphite: http://graphite.wikidot.com/

Accessing Graphite
------------------

+-------------+-----------+---------------------------------------------------+
| environment | region    | Graphite Web UI URL                               |
+=============+===========+===================================================+
| production  | us-west-2 | https://perf.identity.us-west-2.prod.mozaws.net/  |
+-------------+-----------+---------------------------------------------------+
| production  | us-east-1 | https://perf.identity.us-east-1.prod.mozaws.net/  |
+-------------+-----------+---------------------------------------------------+
| staging     | us-west-2 | https://perf.identity.us-west-2.stage.mozaws.net/ |
+-------------+-----------+---------------------------------------------------+

These URLs use the `Identity Gateway`_ service. To access them you'll need
to authenticate with Persona using your email address which is on the `approved list of users`_. 

Using Graphite
--------------

Once you've logged in you can drill into the stack you're looking for in the "Tree" pane.

.. image:: https://github.com/mozilla/identity-ops/wiki/graphite_tree.png

For example to see performance graphs of the frontend load balancer for persona in stack ``0703`` go to ``Graphite/aws/elb/0730/persona-org``

Deploying the graphite tier
--------------------------

Graphite instances are not autoscaled as there is only one in each region/environment combination.

The graphite tier's Chef provisioning code can be found here : https://github.com/mozilla/identity-ops/tree/master/chef/cookbooks/persona-graphite

Create an ec2 instance by following the Manual Deployment instructions

* size : ``m1.small``
* IAM role : ``identity``
* Security Groups : ``identity-prod-temp-internet``, ``identity-prod-public-webserver``, ``identity-prod-administrable``

Identity Gateway
================

* tier name : ``graphite`` (Identity Gateway is co-hosted on the graphite tier)

The identity-gateway is an Apache HTTPD server that reverse proxies traffic in order to provide a persona-based authentication layer in front of the backing services using the `mod_auth_browserid`_  Apache module. Currently the identity-gateway protects the ``monitor`` and ``graphite`` tiers. It is co-hosted on the ``graphite`` tier.

.. _mod_auth_browserid: https://github.com/mozilla/identity-ops/tree/master/chef/cookbooks/identity-gateway

Deploying the identity gateways
-------------------------------

As the identity-gateway is hosted on the `Graphite tier`_ it will be installed along with Graphite on the servers in the Graphite tier by chef. The presence of ``recipe[identity-gateway]`` in the ``run_list`` in the ``/etc/chef/node.json`` file on the graphite servers is what indicates to Chef ot install the identity-gateway.

Nimsoft AKA WatchMouse
======================

* tier name : ``none`` (this is an external service)

`Nimsoft`_ is a commercial service which we have monitor Persona to detect if

* fetching https://login.persona.org/include.js returns a non-200 HTTP code in less than 5 seconds
* the sha1 hash of the contents of https://login.persona.org/include.js fail to match one of two defined hashes
* fetching https://login.persona.org/.well-known/browserid returns a non-200 HTTP code code in less than 5 seconds
* the sha1 hash of the contents of https://login.persona.org/.well-known/browserid fail to match a defined hash

Nimsoft runs this check every 5 minutes from various test locations around the globe. If it detects two consecutive errors it emails infra-services@mozilla.com.

The jmx code that controls this monitor is tracked in ``svn.mozilla.org/sysadmins/svc/watchmouse/bid-content.jmx``.

The sha1 hashes in this file need to be updated when new Persona application versions result in modified ``include.js`` code. The jmx code accommodates two sha1 hashes to enable loading in the new hash prior to deploying the new application version.

.. _Nimsoft: https://dashboard.cloudmonitor.nimsoft.com/en/

