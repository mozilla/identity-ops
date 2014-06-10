******************************************
How to build identity application packages
******************************************

To build identity applications, start with a `Red Hat Enterprise Linux derivative`_, ideally based on a Mozilla Services Operations base AMI. We currently (June 2014) use the `RHEL 6`_ series OS.

One Time Setup
==============

Each Identity application has some one time setup to be done on the build machine

Persona one time build setup
----------------------------

This build process will install nodejs 0.10.28 or newer and npm from the mozilla-services-aws s3 yum repo. You can alternatively install them directly from the ``mozilla-identity-us-standard`` s3 bucket : https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/nodejs-svcops-0.10.28-1.el6.x86_64.rpm

.. code-block:: bash

    sudo yum install gcc-c++ gmp-devel expat-devel nodejs-svcops 
    mkdir workspace
    cd workspace
    git clone https://github.com/mozilla/persona
    #or if you're pulling from the private repo
    #git clone git@github.com:mozilla/browserid_private.git
    cd persona
    #or
    #cd browserid_private
    svn co http://svn.mozilla.org/projects/l10n-misc/trunk/browserid/locale

.. _Red Hat Enterprise Linux derivative: http://en.wikipedia.org/wiki/Red_Hat_Enterprise_Linux_derivatives
.. _RHEL 6: http://en.wikipedia.org/wiki/Red_Hat_Enterprise_Linux#RHEL_6

Identity Bridge Gmail one time build setup
------------------------------------------

.. note:: The localization content in http://svn.mozilla.org/projects/l10n-misc/trunk/browserid-bigtent applies to both Identity Bridge Gmail and Identity Bridge Yahoo

As of October 2013 identity bridge gmail is pinned to locale r118029 ( https://github.com/mozilla/browserid-sideshow-private/blob/4715643dac9e30a281e95134fdeb069e673636be/scripts/rpmbuild.sh#L29 )

.. code-block:: bash

    sudo yum install gcc-c++ gmp-devel expat-devel https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/nodejs-0.8.26-1.el6.x86_64.rpm
    mkdir workspace
    cd workspace
    git clone https://github.com/mozilla/persona-gmail-bridge.git
    #or if you're pulling from the private repo
    #git clone git@github.com:mozilla/browserid-sideshow-private.git
    cd persona-gmail-bridge
    #or
    #cd browserid-sideshow-private
    svn co http://svn.mozilla.org/projects/l10n-misc/trunk/browserid-bigtent/locale -r 118029

Identity Bridge Yahoo one time build setup
------------------------------------------

.. note:: The localization content in http://svn.mozilla.org/projects/l10n-misc/trunk/browserid-bigtent applies to both Identity Bridge Gmail and Identity Bridge Yahoo

.. code-block:: bash

    sudo yum install gcc-c++ gmp-devel expat-devel https://s3.amazonaws.com/mozilla-identity-us-standard/rpms/nodejs-0.8.26-1.el6.x86_64.rpm
    mkdir workspace
    cd workspace
    git clone https://github.com/mozilla/persona-yahoo-bridge.git
    #or if you're pulling from the private repo
    #git clone git@github.com:mozilla/browserid-bigtent_private.git
    cd persona-yahoo-bridge
    #or
    #cd browserid-bigtent_private
    svn co http://svn.mozilla.org/projects/l10n-misc/trunk/browserid-bigtent/locale


Building
========

This gets the train and localization you want to build and calls the makefile which in turn calls the rpmbuild bash script. This uses NPM to build the application and rpmbuild to package it into an RPM.

.. code-block:: bash

    # Pick your train
    train=train-2012.06.22
    repo=persona
    # repo=browserid_private
    # repo=persona-yahoo-bridge
    # repo=browserid-bigtent_private
    # repo=persona-gmail-bridge
    # repo=browserid-sideshow-private

    # downgrade=true # Set this if we're downgrading

    cd workspace/
    cd $repo/
    git pull
    git checkout $train
    svn up locale
    git log -1
    # Confirm you've got the right commit from the ticket
    make rpm
    rm -rf /tmp/.npm

Uploading the RPM
=================

To upload the RPM to the Identity S3 bucket you can use the `s3cmd`_ tool if you don't want to manually upload it through the AWS GUI. This requires a onetime setup with ``s3cmd --configure`` to enter your AWS API credentials.

.. _s3cmd: https://github.com/s3tools/s3cmd

.. code-block:: bash

    s3cmd --configure
    s3cmd --acl-public put rpmbuild/RPMS/x86_64/browserid-server-0*.x86_64.rpm s3://mozilla-identity-us-standard/rpms/

