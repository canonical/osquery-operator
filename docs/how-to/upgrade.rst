.. meta::
   :description: Learn how to upgrade the osquery charm.

.. _how_to_upgrade:

How to upgrade
==============

Upgrading the osquery charm refreshes the charm code. The osquery agent itself
is the ``c-osquery`` snap, which snapd refreshes automatically within the
channel set in the ``snap-channel`` option. Because the charm is stateless, upgrades
don't require any data migration.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO

Before you upgrade
------------------

- Review the :ref:`release notes <release_notes_index>` for the target revision
  to check for any behavioral changes or new required configuration.
- Capture your current configuration so you can compare or reapply it if needed:

  .. code-block:: bash

      juju config osquery > osquery-config-backup.yaml

Refresh the charm
-----------------

Upgrade the charm to the latest revision in its channel with ``juju refresh``:

.. code-block:: bash

    juju refresh osquery

To upgrade to a specific channel or revision, pass ``--channel`` or
``--revision``:

.. code-block:: bash

    juju refresh osquery --channel latest/stable

After the refresh, the charm reconciles the agent: it re-renders the osquery
flagfile and restarts ``osqueryd`` if anything changed.

Change the osquery snap channel
-------------------------------

To move the agent to a different snap channel, set ``snap-channel``. The charm
refreshes the snap onto the new channel on its next reconcile:

.. code-block:: bash

    juju config osquery snap-channel=latest/stable

Verify the upgrade
------------------

Watch the deployment until it settles back into an ``active`` state:

.. code-block:: bash

    juju status --watch 2s

Confirm the osquery version and snap channel on the host if the upgrade
included a new agent release:

.. code-block:: bash

    juju ssh <principal>/0 snap list c-osquery
