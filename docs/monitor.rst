**********
Monitoring
**********

Availability monitoring is monitoring which detects the availability of a service. This can either be done pro-actively by interrogating the service (e.g. every 5 minutes fetch a web page) or after the fact by observing logs (e.g. searching for non-200 HTTP codes in access logs). Availability monitoring frequently triggers push notifications to operations engineers.

Performance monitoring is the process of gathering metrics on a system's performance, recording them and visualizing them. Performance monitoring data is typically consumed in a pull model where operations engineers opt to view the performance monitoring system's data visualizations.

Monitor tier (Opsview)
======================

Opsview is our primary availability monitoring system. We use it to actively interrogate the Identity applications as well as provide very limited performance monitoring.

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

These URLs use the `Identity Gateway`_ service which runs on the Graphite_ servers. This means to access them you'll need
to authenticate with Persona using your email address which is on the `approved list of users`_. 

Once you've authenticated with your email address you'll be presented with the Opsview application login screen. Here, login with the shared credentials which can be found at ``svn.mozilla.org/sysadmins/gpg/services/passwords.txt.gpg``. For staging you can login as either the read-only user ``identity`` with the password ``identity`` or as the administrator with the username ``admin`` and the password ``initial``.

As the REST API is currently also behind the `Identity Gateway`_ Persona authentication some trickery is requires to use the REST API (like passing in pre-generated Persona session cookies with your API calls)

.. _approved list of users: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/identity-gateway/files/default/var/www/mod_browserid_users

Deploying the monitor tier
--------------------------

Opsview instances are not autoscaled as there is only one in each region/environment combination.

1. Create an ec2 instance either on the command line or web gui

   a) size : m1.small
   b) IAM role : identity
   c) vpc and subnet : The VPC of the environment you want to deploy in
   d) AMI ID : A persona-base AMI
   e) Security Groups : identity-dev-monitor, identity-dev-administrable, identity-dev-temp-internet

2. Inject the secrets

   a) Obtain the secrets from the secrets s3 bucket
   b) Obtain the instances gpg private key from the persona-builder instance
   c) Decrypt the secrets and write them to ``/etc/chef/node.json``

3. Fetch the current or specific desired revision of the ``identity-ops`` git repo

  .. code-block:: bash

      cd /root/identity-ops && git pull && git checkout HEAD

4. Hydrate the machine with Chef

  .. code-block:: bash

      chef-solo -c /etc/chef/solo.rb -j /etc/chef/node.json

5. Populate the now running Opsview instance with monitors and monitoring templates.

   This is best done by taking an export from an existing Opsview instance using `opsview_control.rb`_ and importing it with the same tool
   
   .. _opsview_control.rb: https://github.com/mozilla/identity-ops/blob/master/opsview-tools/opsview_control.rb


Graphite tier
=============

Graphite collects, records and visualizes performance monitoring data. This tier also hosts the `Identity Gateway`_ service.

Accessing Graphite
------------------

+-------------+-----------+--------------------------------------------------+
| environment | region    | Graphite Web UI URL                              |
+=============+===========+==================================================+
| production  | us-west-2 | https://perf.identity.us-west-2.prod.mozaws.net/ |
+-------------+-----------+--------------------------------------------------+
| production  | us-east-1 | https://perf.identity.us-east-1.prod.mozaws.net/ |
+-------------+-----------+--------------------------------------------------+
| staging     | us-west-2 | https://perf.identity.us-west-2.stage.mozaws.net/ |
+-------------+-----------+--------------------------------------------------+



Identity Gateway
================



Nimsoft AKA WatchMouse
======================

`Nimsoft`_ is a commercial service which we have monitor Persona to detect if
* fetching https://login.persona.org/include.js returns a non-200 HTTP code in less than 5 seconds
* the sha1 hash of the contents of https://login.persona.org/include.js fail to match one of two defined hashes
* fetching https://login.persona.org/.well-known/browserid returns a non-200 HTTP code code in less than 5 seconds
* the sha1 hash of the contents of https://login.persona.org/.well-known/browserid fail to match a defined hash

Nimsoft runs this check every 5 minutes from various test locations around the globe. If it detects two consecutive errors it emails infra-services@mozilla.com.

The jmx code that controls this monitor is tracked in ``svn.mozilla.org/sysadmins/svc/watchmouse/bid-content.jmx ``.

The sha1 hashes in this file need to be updated when new Persona application versions result in modified ``include.js`` code. The jmx code accommodates two sha1 hashes to enable loading in the new hash prior to deploying the new application version.

.. _Nimsoft: https://dashboard.cloudmonitor.nimsoft.com/en/








