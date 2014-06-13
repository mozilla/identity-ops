***************
Opsview Control
***************

``opsview_control.rb`` can be used to export the state of a running Opsview installation, import a stored state into a new Opsview instance, and recursively delete hosts in a hostgroup.

Usage
=====

::

    OpsView Control

    Usage:
           ./opsview_control.rb import --help
           ./opsview_control.rb export --help
           ./opsview_control.rb destroystack --help
      --help, -h:   Show this message

    OpsView Control : Export

    Usage:
           ./opsview_control.rb export --url http://localhost:10000/rest [options]

    Options:
                 --sections, -s <s+>:   Config sections you would like to export (default: keyword, timeperiod, attribute, servicegroup, notificationmethod, hostcheckcommand, hostgroup, role, contact,
                                        servicecheck, hosttemplate)
                  --username, -u <s>:   OpsView API User Name (default: admin)
                  --password, -p <s>:   OpsView API User Password (default: initial)
                       --url, -r <s>:   OpsView API URL (default: http://localhost/rest)
                  --loglevel, -l <s>:   Logging verbosity (default: INFO)
       --session-cookie-name, -e <s>:   Name of a cookie to pass to Opsview or an authentication gateway in front of it
      --session-cookie-value, -i <s>:   Session cookie value
                        --dryrun, -d:   Don't actually do anything
                          --help, -h:   Show this message

    OpsView Control : Import

    Usage:
           ./opsview_control.rb import --sections attribute role [options]

    Options:
                 --sections, -s <s+>:   Config sections you would like to import (default: keyword, timeperiod, attribute, servicegroup, notificationmethod, hostcheckcommand, hostgroup, role, contact,
                                        servicecheck, hosttemplate)
                  --include, -i <s+>:   Specific items you would like include (default: false)
                  --exclude, -e <s+>:   Specific items you would like to exclude (default: false)
          --keyword-include, -k <s+>:   Include items associated with these keywords (default: false)
          --keyword-exclude, -y <s+>:   Exclude items associated with these keywords (default: false)
                  --username, -u <s>:   OpsView API User Name (default: admin)
                  --password, -p <s>:   OpsView API User Password (default: initial)
                       --url, -r <s>:   OpsView API URL (default: http://localhost/rest)
                  --loglevel, -l <s>:   Logging verbosity (default: INFO)
       --session-cookie-name, -o <s>:   Name of a cookie to pass to Opsview or an authentication gateway in front of it
      --session-cookie-value, -n <s>:   Session cookie value
                        --dryrun, -d:   Don't actually do anything
                          --help, -h:   Show this message

    OpsView Control : Destroy Stack

    Usage:
           ./opsview_control.rb destroystack --hostgroup "identity-dev Stack 0514" [options]
           ./opsview_control.rb destroystack --hostgroup "identity-dev Stack 0514" --session-cookie-name myauthcookie --session-cookie-value user@example.com|ZgtjMZuFnsaopw6IDt3twGr9aDU= [options]

    Options:
                 --hostgroup, -h <s>:   Name of the hostgroup to destroy
                  --username, -u <s>:   OpsView API User Name (default: admin)
                  --password, -p <s>:   OpsView API User Password (default: initial)
                       --url, -r <s>:   OpsView API URL (default: http://localhost/rest)
                  --loglevel, -l <s>:   Logging verbosity (default: INFO)
       --session-cookie-name, -s <s>:   Name of a cookie to pass to Opsview or an authentication gateway in front of it
      --session-cookie-value, -e <s>:   Session cookie value
                        --dryrun, -d:   Don't actually do anything
                              --help:   Show this message

The ``--session-cookie-name`` and ``--session-cookie-value`` options are used to pass arbitrary cookies through to Opsview. We use this to authenticate to a `mod_browserid`_ Apache reverse proxy sitting in front of Opsview.

.. _mod_browserid: https://github.com/mozilla/mod_browserid

Export
======

By default, the exporter exports the following sections

* keyword
* timeperiod
* attribute
* servicegroup
* notificationmethod
* hostcheckcommand
* hostgroup
* role
* contact
* servicecheck
* hosttemplate

This intentionally excludes hosts and hostgroups as the intent of this export tool is to capture everything permanent and nothing ephemeral (like hosts and hostgroups).

Pass the tool the URL, username and password to your Opsview installation and it will generate one json export file for each section. These are written to the current working directory

Import
======

The importer looks for files created by the exporter in the current working directory, one for each section you're importing. The import follows a strict order so as to build the new instance, resolving dependencies between objects.

Destroy stack
=============

This will determine the hosts in the hostgroup passed on the command line and delete each host from Opsview
