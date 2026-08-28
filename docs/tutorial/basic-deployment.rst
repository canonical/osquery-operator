.. meta::
   :description: Deploy the OSQuery charm for the first time and relate it to a principal application.

.. _tutorial_basic_deployment:

Deploy the OSQuery charm for the first time
===========================================

The OSQuery charm installs and runs the ``osqueryd`` endpoint security
monitoring agent on a machine. Because it's a `subordinate charm
<https://documentation.ubuntu.com/juju/3.6/reference/charm/#subordinate-charm>`_,
it doesn't run on its own: it attaches to a *principal* application that occupies
the machine. In this tutorial you'll deploy a simple principal application, add
the OSQuery charm as a subordinate, and confirm that the agent is running.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO
.. vale Canonical.500-Repeated-words = NO

What you'll need
----------------

You will need a working station, e.g., a laptop, with AMD64 architecture. Your working station
should have at least 2 CPU cores, 4 GB of RAM, and 20 GB of disk space.

.. tip::

    You can use Multipass to create an isolated environment by running:

    .. code-block::

        multipass launch 24.04 --name charm-tutorial-vm --cpus 4 --memory 8G --disk 50G

What you'll do
--------------

- Set up an isolated environment.
- Deploy a principal application.
- Deploy the OSQuery charm as a subordinate.
- Integrate the two charms.
- Verify the deployment.
- Clean up the environment.

Set up an isolated environment
------------------------------

For this tutorial, use a clean Juju model inside a local LXD cloud. This keeps
your environment isolated and easy to remove afterwards.

The fastest way to bootstrap Juju on LXD is with `concierge
<https://github.com/canonical/concierge>`_:

.. code-block:: bash

    sudo snap install --classic concierge
    sudo concierge prepare -p machine

Alternatively, if you already have Juju (3.6 or newer) and LXD (5.21 or newer) installed, bootstrap a controller
manually:

.. code-block:: bash

    juju bootstrap localhost lxd tutorial-controller

Then, regardless of how you bootstrapped, create a dedicated model for this
tutorial:

.. code-block:: bash

    juju add-model osquery-tutorial

Deploy a principal application
------------------------------

Because the OSQuery charm is a subordinate, it needs a principal to attach to. The ``ubuntu`` charm is a
minimal principal application that provisions a bare Ubuntu machine, which is ideal for this
tutorial. Let's deploy it now:

.. code-block:: bash

    juju deploy ubuntu --base ubuntu@24.04

The ``--base`` flag pins the machine to Ubuntu 24.04, ensuring it matches a base
the OSQuery subordinate supports.

Deploy the OSQuery charm
------------------------

Deploy the OSQuery charm:

.. code-block:: bash

    juju deploy osquery

Because it's a subordinate, it stays in a ``waiting``
state until it's integrated with a principal.

Integrate the charms
--------------------

Integrate the OSQuery charm with the principal application over the
``general-info`` endpoint:

.. code-block:: bash

    juju integrate ubuntu osquery

This command tells Juju to place the OSQuery agent on the same
machine as the ``ubuntu`` unit.

Verify the deployment
---------------------

Watch the deployment settle with:

.. code-block:: bash

    juju status --watch 2s

Wait until the ``ubuntu`` application is ``active`` and the ``osquery``
subordinate reaches a settled state. The OSQuery charm blocks until it's told
which OSQuery Controller to enroll with, so it's expected to report a blocked
status such as ``controller-env-uuid is required`` at this stage. Connecting the
agent to a controller is covered in the :ref:`advanced tutorial
<tutorial_advanced_deployment>`.

To confirm the subordinate is attached to the principal, view the relation
with:

.. code-block:: bash

    juju status --relations

You should see the ``osquery`` unit nested under ``ubuntu/0`` and the
``general-info`` relation listed at the bottom:

.. code-block:: text

    Model             Controller           Cloud/Region         Version  SLA          Timestamp
    osquery-tutorial  tutorial-controller  localhost/localhost  3.6.0    unsupported  12:00:00Z

    App      Version  Status   Scale  Charm    Channel        Rev  Exposed  Message
    osquery           blocked      1  osquery  latest/stable   12  no       controller-env-uuid is required
    ubuntu   24.04    active       1  ubuntu   latest/stable   26  no

    Unit          Workload  Agent  Machine  Public address  Ports  Message
    ubuntu/0*     active    idle   0        10.1.0.10
      osquery/0*  blocked   idle            10.1.0.10               controller-env-uuid is required

    Machine  State    Address    Inst id        Base          AZ  Message
    0        started  10.1.0.10  juju-abc123-0  ubuntu@24.04       Running

    Integration provider  Requirer              Interface  Type         Message
    ubuntu:juju-info       osquery:general-info  juju-info  subordinate

You can confirm that the ``osqueryd`` binary was installed on the machine by
running a command inside the unit:

.. code-block:: bash

    juju ssh ubuntu/0 osqueryd --version

If the binary is installed, it prints its version:

.. code-block:: text

    osqueryd version 5.21.0

The same package ships the ``osqueryi`` interactive shell, which lets you query
the host's state with SQL. For example, let's list a few of the machine's running
processes to see it in action:

.. code-block:: bash

    juju ssh ubuntu/0 osqueryi "SELECT pid, name FROM processes ORDER BY pid LIMIT 5;"

osquery answers straight from the live system (your exact output will vary):

.. code-block:: text

    +-----+---------+
    | pid | name    |
    +-----+---------+
    | 1   | systemd |
    | ... | ...     |
    +-----+---------+

Note that the ``osqueryi`` shell is just a convenience for testing. Typically the agent
runs in the background as a daemon and is controlled by the OSQuery Controller.
See the :ref:`advanced tutorial <tutorial_advanced_deployment>` for instructions on enrolling the agent with a controller.

Clean up the environment
------------------------

Once you're done, you can remove the model and everything in it:

.. code-block:: bash

    juju destroy-model osquery-tutorial --destroy-storage

If you used ``concierge``, you can tear down the whole environment with:

.. code-block:: bash

    concierge restore

Next steps
----------

Now that you have a basic deployment, continue to the :ref:`advanced tutorial
<tutorial_advanced_deployment>` to connect the agent to an OSQuery Controller.
