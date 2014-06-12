****************************
Accessing hosts and services
****************************

SSHing into hosts
=================

Bastion hosts
-------------

Hosts are accessed by first sshing to a `bastion host`_ and then sshing to the target machine from the bastion host. The recommended way to accomplish this is to use `ssh-agent`_ combined with ssh's authentication agent forwarding. Many unix flavored operating systems have ssh-agent functionality built in. If yours does not you'll want to load your private key into ssh-agent manually ( http://kb.iu.edu/data/aeww.html )

.. _bastion host: http://en.wikipedia.org/wiki/Bastion_host
.. _ssh-agent: http://en.wikipedia.org/wiki/Ssh-agent

Once your key is loaded into ssh-agent you can ssh to the target bastion host and forward your authentication agent along with a command like ``ssh -A root@admin.example.com``

Staging
^^^^^^^

The staging hosts have most identity developer's and qa personnel's keys loaded for the ``root`` user. If your key is missing from the `list of authorized_keys`_ open a github issue requesting access.

.. _list of authorized_keys: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/access/files/default/root/.ssh/authorized_keys

Bastion host name
"""""""""""""""""

``root@admin.identity.us-west-2.stage.mozaws.net``

Production
^^^^^^^^^^

The production hosts are only accessible by Services Operations personnel.

Bastion host names
""""""""""""""""""

* `us-west-2 Oregon`_ : ``root@admin.identity.us-west-2.prod.mozaws.net``
* `us-east-1 Virginia`_ : ``root@admin.identity.us-east-1.prod.mozaws.net``

.. _us-west-2 Oregon: http://aws.amazon.com/about-aws/globalinfrastructure/
.. _us-east-1 Virginia: http://aws.amazon.com/about-aws/globalinfrastructure/


Identifying a target host
-------------------------

To find the ip of a target host in a stack use the built in ``get_hosts`` tool. For example to see the ips of the ``webheads`` in stack ``0703`` run 

.. code-block:: bash

    get_hosts 0703 webhead

To query the version of browserid on each host run

.. code-block:: bash

    for host in `get_hosts 0703 webhead`; do ssh ec2-user@$host "rpm -q browserid-server"; done

Or to, in parallel, get the uptime of each webhead

.. code-block:: bash

    pssh --user ec2-user --host "`get_hosts 0703 webhead`" --inline "uptime"

Or run chef-solo

.. code-block:: bash

    pssh --user ec2-user -H "`get_hosts 0730`" --timeout=0 --inline --par=10 --extra-args='-t -t -o StrictHostKeyChecking=no' 'sudo chef-solo -c /etc/chef/solo.rb -j /etc/chef/node.json --force-formatter'

To get a list of existing stacks run ``get_hosts`` or ``get_hosts -o table``

Determining configuration
=========================

To find out how a given instance is configured look at the node attributes for the instance in ``/etc/chef/node.json``. In the node json file you'll see all the node's custom attributes as well as the ``run_list``. The ``run_list`` lists the cookbooks that the node runs when provisioning itself. Our cookbooks can be found in ``/root/identity-ops/chef/cookbooks`` and third-party cookbooks are in ``/var/chef/cookbooks``.

For example, if the ``run_list`` in the ``node.json`` file shows ``"run_list": [ "recipe[persona-webhead]" ]``, then the associated cookbook can be found at ``/root/identity-ops/chef/cookbooks/persona-webhead``.

You can examine the cookbook on the host or in github : https://github.com/mozilla/identity-ops/tree/master/chef/cookbooks

The provisioning steps for a cookbook are contained in its default recipe. For a webhead this would be in ``/root/identity-ops/chef/cookbooks/persona-webhead/recipes/default.rb``

In this recipe you'll see resources defined as well as other recipes included. In the `persona-webhead coobook's default recipe`_ you can see that a few other recipes are included with statements like ``include_recipe "persona-common::default"``. You'll also see resources defined like ``package`` which install a package, or ``file`` which create a file on disk.

.. _persona-webhead coobook's default recipe: https://github.com/mozilla/identity-ops/blob/master/chef/cookbooks/persona-webhead/recipes/default.rb

Determining which stack is live
===============================

The easiest way to find out what stack is currently receiving traffic is to resolve the DNS name for the site you're wondering about. For example to determine the stack running in production, you could 

.. code-block:: bash

    dig login.persona.org

which would show you the CNAME. If the CNAME was ``persona-org-0625-599714699.us-west-2.elb.amazonaws.com.`` then the stack would be ``0625``. You can simplify the output with 

.. code-block:: bash

    dig login.persona.org CNAME +short

Determining ELB Load Balancer Information
=========================================

To query for ELB DNS CNAMEs for a given stack run 

.. code-block:: bash

    get_hosts -e 0703

or to get the name of a specific ELB

.. code-block:: bash

    get_hosts -e 0703 person-org
