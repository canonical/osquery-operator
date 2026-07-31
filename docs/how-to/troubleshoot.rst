.. meta::
   :description: Troubleshoot common issues with the OSQuery charm.

.. _how_to_troubleshoot:

How to troubleshoot
===================

This guide covers common issues you might encounter when operating the OSQuery
charm, and how to diagnose them.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO
.. vale Canonical.500-Repeated-words = NO

Inspect the charm status
------------------------

Start with the Juju status, which reports the charm's current state and any
blocking condition:

.. code-block:: bash

    juju status

The charm sets a descriptive status message when it can't proceed, for example
when a required configuration value is missing.

The charm is blocked
--------------------

The charm blocks until it has everything it needs to configure the agent. The
most common cause is a missing required configuration value, such as
``controller-env-uuid``. The status message names the missing value; set it with
``juju config`` as described in the :ref:`advanced tutorial
<tutorial_advanced_deployment>`.

Read the charm logs
-------------------

Use ``juju debug-log`` to see what the charm did during its most recent
reconcile:

.. code-block:: bash

    juju debug-log --include osquery --replay

The daemon isn't running
------------------------

If the charm reports ``active`` but OSQuery doesn't appear to be working, check
the ``osqueryd`` service on the unit's machine:

.. code-block:: bash

    juju ssh <principal>/0 systemctl status osqueryd
    juju ssh <principal>/0 journalctl -u osqueryd --no-pager

The charm renders an OSQuery flagfile from the Juju configuration and restarts
the daemon whenever the configuration changes. If the daemon fails to start,
these logs usually explain why — for example, an invalid flag value or an
unreadable certificate.

The agent won't enroll
----------------------

If the daemon is running but the agent doesn't enroll with the controller,
verify the controller-related configuration:

- ``controller-uri`` points at the correct hostname.
- ``controller-env-uuid`` matches the environment assigned to your fleet.
- ``enroll-secret`` references a Juju secret that the charm has been granted
  access to.
- ``tls-server-certs``, ``tls-client-cert``, and ``tls-client-key`` contain the
  correct certificates and key.

Enrollment failures are typically logged by ``osqueryd`` and visible in the
``journalctl`` output shown above.
