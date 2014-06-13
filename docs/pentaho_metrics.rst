***********************
Persona Pentaho metrics
***********************

Metrics generation
==================

For BrowserID, metrics generates data based on JSON files written by the application (on the webheads).

* ``/var/browserid/log/router-metrics.json``
* ``/var/browserid/log/verifier-metrics.json``

Log Rotation
============

Code : `/etc/cron.d/logrotate`_ Instead of using anacron to call logrotate, a cron.d file instructs cron to call logrotate. This is to fix the time of day when logrotate is run very specifically. logrotate runs at 3am every day

Code : `/usr/local/bin/logrotate.cron`_ Logrotate is instantiated with this short script which runs the lograte binary, passing it the ``lograte.conf`` configuration file which includes ``/etc/logrotate.d/*``

Code : `/etc/logrotate.d/bid_metrics`_ The logrotate config file for bid_metrics :

        Rotates the 2 files ``/var/browserid/log/verifier-metrics.json`` and ``/var/browserid/log/router-metrics.json``
        gzips them
        appends a datestamp to the filename (-2013-01-23)
        moves the rotated gziped renamed file to ``/opt/bid_metrics/queue``
        appends the webhead hostname to the end of the filename
        sets the file to read only to indicate that rotation is complete

logrotate itself will keep these files for 7 days.

An example post rotation file would look like : ``/opt/bid_metrics/queue/verifier-metrics.json-2013-05-28.gz.ip-10-148-37-120.webhead.0525.prod.us-west-2.allizomaws.com``

.. _/etc/cron.d/logrotate: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-webhead/recipes/metrics.rb#L52
.. _/usr/local/bin/logrotate.cron: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-webhead/files/default/usr/local/bin/logrotate.cron
.. _/etc/logrotate.d/bid_metrics: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-webhead/files/default/etc/logrotate.d/bid_metrics

Log push from webhead to persona-metric system
==============================================

Code : `/etc/cron.d/bid_metrics-scp`_

Everyday at 04:01 AM The ``bid_metrics-scp`` cron job scps the ``/opt/bid_metrics/queue/*`` files to the region's local persona-metric server as defined in the ``node[:persona][:webhead][:metrics][:server]`` attribute on the webhead. These logs are deposited in the ``/opt/bid_metrics/incoming/`` directory on the persona-metric server.

.. _/etc/cron.d/bid_metrics-scp: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-webhead/recipes/metrics.rb#L59

Log Sanitizing (ETL/Kettle scripts)
===================================

Code : `/etc/cron.d/process_metrics`_

The ``process_metrics`` cron job on the persona-metric server calls the ``process_metrics.sh`` script every day at 04:30 AM

Code : `/opt/bid_metrics/bin/process_metrics.sh`_

The ``process_metrics.sh`` script, which is run on the persona-metric system :

        moves everything from ``/opt/bid_metrics/incoming/`` to ``/opt/bid_metrics/queue/``
        concatenates all gunziped verifier and all router metrics json files from all webheads into 2 respective aggregated json files, ``/opt/bid_metrics/etl/input/verifier-metrics.json`` and ``/opt/bid_metrics/etl/input/router-metrics.json``
        calls ``/opt/bid_metrics/etl/run.sh``

Code : `/opt/bid_metrics/etl/run.sh`_

``run.sh`` calls the `pentaho kitchen`_ script passing it the config parameter of ``/opt/bid_metrics/etl/etl/main.kjb``

Code : `/opt/bid_metrics/etl/etl/`_

``/opt/bid_metrics/etl/etl/main.kjb`` in turn includes a collection of pentaho configuration files in the ``/opt/bid_metrics/etl/etl/`` directory which sanitize the metrics json files by doing things like removing IP addresses.

All output from the ``process_metrics`` cron job is logged to the file ``/tmp/process_metrics.out``

.. _/etc/cron.d/process_metrics: https://github.com/mozilla/identity-ops/blob/master/chhttps://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-metrics/recipes/default.rb#L151
.. _/opt/bid_metrics/bin/process_metrics.sh: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-metrics/files/default/opt/bid_metrics/bin/process_metrics.sh
.. _/opt/bid_metrics/etl/run.sh: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-metrics/files/default/opt/bid_metrics/etl/run.sh
.. _pentaho kitchen: http://wiki.pentaho.com/display/EAI/Kitchen+User+Documentation
.. _/opt/bid_metrics/etl/etl/: https://github.com/mozilla/identity-ops/tree/master/chef/cookbooks/persona-metrics/files/default/opt/bid_metrics/etl/etl

Log push from persona-metric system to metrics-logger1.private.scl3.mozilla.com
===============================================================================

Code : `/opt/bid_metrics/bin/process_metrics.sh`_

The ``process_metrics.sh`` script then pushes the resulting sanitized log files located in ``/opt/bid_metrics/etl/output/`` to ``metrics-logger1.private.scl3.mozilla.com`` in the ``/data/stats/logs/bid_metrics/`` directory to be picked up by the metrics team.

This communication is enabled by a VPC VPN from each of our AWS regions to the metrics server in SCL3

.. _/opt/bid_metrics/bin/process_metrics.sh: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-metrics/files/default/opt/bid_metrics/bin/process_metrics.sh

Metrics Integration
===================

Every day at 5am, metrics picks up the ETL output ``/data/stats/logs/bid_metrics/`` from ``metrics-logger1.private.scl3.mozilla.com`` and imports into their dashboard. There is a public key installed on ``10.146.33.149`` and/or ``10.148.33.163`` and/or ``cm-metricsapp01.mozilla.org`` that allows metrics to collect files as user bid_metrics. The initial ACL request for this access may have been in `Bugzilla 711237`_ 

* Pentaho dashboard: https://metrics.mozilla.com/pentaho/content/pentaho-cdf-dd/Render?solution=metrics2&path=identity&file=identity.wcdf

.. _Bugzilla 711237: https://bugzilla.mozilla.org/show_bug.cgi?id=711237

Contacts
========

We worked mainly with :aphadke from metrics on getting this setup. It also looks like :ericz owns some of the metrics cron jobs.

Deprecated method that was used in the physical data centers
============================================================

Log Collection
--------------

Every day at 4am, adm1.scl2 runs a script to collect log files, as user bid_metrics. This user has a special ssh key on adm1.scl2 that can log in to all of the browserid webheads, as user bid_metrics.

After log files are collected, they are removed on the remote host (to prevent re-processing). Files are collected into /opt/bid_metrics/queue (initially scp'd to /opt/bid_metrics/incoming, then moved to queue).

We chose a "pull" methodology (rather than "push", webheads -> adm1) for security reasons. adm1 already has ssh access to these machines, and we don't want to open up any kind of extra access (especially involving moving files) from the bid hosts to the admin svc-ops network.

If there are problems here, a cron mail will be generated. Inspect /opt/bid_metrics/collect.log for more information.
