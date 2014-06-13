*******************************
How to build a Persona base AMI
*******************************

Here are the steps necessary to take a `Red Hat Enterprise Linux Derivative`_ and bring it to a state where it can be used as a base `AMI`_ for Persona. The overview of what's required is

1. Wait while the instance establishes internet connectivity
2. Install Chef
3. Fetch the `identity-ops`_ Chef provisioning code repository with git
4. Fetch all supporting Chef cookbooks with git
5. Install the Chef solo config file ``solo.rb``
6. Create a stub ``node.json`` node attribute file with an empty ``run_list``
7. Run Chef-solo

.. _identity-ops: https://github.com/mozilla/identity-ops/

.. _Red Hat Enterprise Linux Derivative: https://en.wikipedia.org/wiki/Red_Hat_Enterprise_Linux_derivatives
.. _AMI: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html

.. code-block:: bash

    #!/bin/bash
    count=0
    while ! curl https://www.opscode.com/chef/install.sh ; do
      # Wait until we have network connectivity
      sleep 1
      count=$((count+1))
      if [ "$count" -gt 60 ]; then
        echo "waited 60 seconds to get network access with no luck" >> /tmp/user-data.out
        exit 1
      fi
    done
    curl -L https://www.opscode.com/chef/install.sh | bash
    mkdir -p /var/chef/cache /etc/chef
    yum install -y git
    git clone https://github.com/mozilla/identity-ops.git /root/identity-ops
    git clone https://github.com/gene1wood/daemontools.git /var/chef/cookbooks/daemontools
    git clone https://github.com/gene1wood/opsview_client /var/chef/cookbooks/opsview_client
    git clone https://github.com/opscode-cookbooks/build-essential.git /var/chef/cookbooks/build-essential && pushd /var/chef/cookbooks/build-essential && git checkout tags/1.4.0 && popd
    git clone https://github.com/opscode-cookbooks/ucspi-tcp.git /var/chef/cookbooks/ucspi-tcp
    git clone https://github.com/edelight/chef-solo-search.git /var/chef/cookbooks/chef-solo-search
    git clone https://github.com/opscode-cookbooks/users.git /var/chef/cookbooks/users
    ln -s /root/identity-ops/chef/solo.rb /etc/chef/solo.rb
    cat > /etc/chef/node.json <<End-of-message
    {
      "run_list": [ ]
    }
    End-of-message
    chmod 600 /etc/chef/node.json
    chef-solo -c /etc/chef/solo.rb -j /etc/chef/node.json

