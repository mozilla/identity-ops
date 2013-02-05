These shabby scripts are supposed to hold us over for Q1 2013 while we spin up persona in AWS. 
During that time this should enable jrgm to do his own staging deploys.

# build.sh

This tool pulls a specific revision of code from the git repo and a specific revision of locale from the svn repo and builds them into an RPM

This tool should be run from the r6.build.mtv1.svc.mozilla.com build machine

## Usage

    ./build.sh browserid train-2013.02.01 # this builds from HEAD
    ./build.sh browserid train-2013.02.01 7a2f1e479a279246316a1ed5d23fe1c507c35b8e # this builds a specific revision
    ./build.sh browserid train-2013.02.01 7a2f1e479a279246316a1ed5d23fe1c507c35b8e 112741 # this builds a specific code and locale revision
    ./build.sh browserid-bigtent train-2013.02.01 # this builds bigtent

# distribute_and_install.sh

This tool fetches the previously built RPM from r6.build.mtv1.svc.mozilla.com, distributes it out to staging and load test machines, and installs it on each.
The tool uses a script living locally on each staging and load test machine to do the installation. This local script allows QA to install via sudoers as root.
The local tool is managed by puppet and stored in svn.mozilla.org/sysadmins/puppet/weave/modules/browserid/files/usr/local/bin/install_browserid.sh
The tool neglects to distribute the rpm to mrepo due to access restrictions. This shouldn't be a problem.

## Usage

    ./distribute_and_install.sh browserid train-2013.02.01
    ./distribute_and_install.sh browserid-bigtent train-2013.02.01
