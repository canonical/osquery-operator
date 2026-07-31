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

- A working station, e.g., a laptop, with amd64 architecture.
- Juju 3 installed and bootstrapped to a machine controller. If you don't have
  one yet, the quickest option is to use a local `LXD
  <https://canonical.com/lxd>`_ cloud.
- At least 4 GB of RAM and 2 CPU cores available for the LXD container.

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

The fastest way to set up a machine cloud is with `concierge
<https://github.com/canonical/concierge>`_, which bootstraps Juju on LXD for
you:

.. code-block:: bash

    sudo snap install --classic concierge
    concierge prepare -p machine

Alternatively, if you already have Juju and LXD installed, bootstrap a controller
and add a model manually:

.. code-block:: bash

    juju bootstrap localhost lxd
    juju add-model osquery-tutorial

Deploy a principal application
------------------------------

A subordinate charm needs a principal to attach to. The ``ubuntu`` charm is a
minimal principal that provisions a bare Ubuntu machine, which is ideal for this
tutorial:

.. code-block:: bash

    juju deploy ubuntu --base ubuntu@24.04

Deploy the OSQuery charm
------------------------

Deploy the OSQuery charm. Because it's a subordinate, it stays in a ``waiting``
state until it's integrated with a principal:

.. code-block:: bash

    juju deploy osquery

Integrate the charms
--------------------

Integrate the OSQuery charm with the principal application over the
``general-info`` endpoint. This tells Juju to place the OSQuery agent on the same
machine as the ``ubuntu`` unit:

.. code-block:: bash

    juju integrate ubuntu osquery

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

You can confirm that the ``osqueryd`` binary was installed on the machine by
running a command inside the unit:

.. code-block:: bash

    juju ssh ubuntu/0 osqueryd --version

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
