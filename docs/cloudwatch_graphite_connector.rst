*****************************
Cloudwatch Graphite Connector
*****************************

Cookbook : https://github.com/mozilla/identity-ops/tree/master/chef/cookbooks/persona-graphite

RPM : https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/cloudwatch2graphite-1-1.x86_64.rpm

RPM Build logic : https://github.com/6a68/cloudwatch2graphite/pull/1

.. code-block:: bash

    node /opt/cloudwatch2graphite/cw2graphite.js

Example output :
::

    aws.elb.bt-login-anosrep-org.healthyhostcount.sum.count 2.0 1369182990528
    aws.elb.dbwrite.healthyhostcount.sum.count 2.0 1369182990580
    aws.elb.diresworb-org.healthyhostcount.sum.count 2.0 1369182990612
    aws.elb.keysign.healthyhostcount.sum.count 2.0 1369182990646
    aws.elb.proxy.healthyhostcount.sum.count 2.0 1369182990700
    aws.elb.w-anosrep-org.healthyhostcount.sum.count 2.0 1369182990739
    aws.elb.w-login-anosrep-org.healthyhostcount.sum.count 2.0 1369182990765
