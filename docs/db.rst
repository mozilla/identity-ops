****************
Persona Database
****************

Replication Topology
====================

.. image:: https://wiki.mozilla.org/images/5/5e/Persona_MySQL_Replication_Topology.png

How to build a DB
=================

Create an instance
------------------

* type : ``m1.large``
* IAM Role : ``identity``
* ami : any base AMI
* EBS optimized : enabled

Acquire a data volume or create one
-----------------------------------

* Size : 50GB
* IOPS : 500

Mount the volume
----------------

* create mount point 

  .. code-block:: bash

    mkdir /data

* edit /etc/fstab (in this example the volume is identified as /dev/xvdj1)

  ::

    /dev/xvdj1 /data ext3 defaults 0 2

* mount /data

Provisiong the host
-------------------

* install chef
* populate ``/etc/chef/node.json``

Update slaves
-------------

If it's a master, update the slaves /etc/chef/node.json to reflect the new master IP

.. code-block:: sql

    CHANGE MASTER TO MASTER_HOST = '1.2.3.4', MASTER_USER = 'replication-user-name', MASTER_PASSWORD = 'replication-password';
