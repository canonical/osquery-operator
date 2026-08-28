.. meta::
   :description: Learn why the OSQuery charm needs no data backup, and how to back up and restore its configuration.

.. _how_to_back_up_restore:

How to back up and restore
==========================

The OSQuery charm is stateless. All of its meaningful state lives elsewhere:

- The agent's configuration (query schedules, telemetry rules, and query tasks)
  is owned by the OSQuery Controller and fetched over TLS at runtime.
- The agent's logs are shipped to the controller rather than retained locally.
- The charm's own settings (the Juju configuration and secrets) are stored in
  the Juju controller as part of the model.

As a result, there's no charm-specific data to back up or restore. To recover an
OSQuery deployment, redeploy the charm and reapply its configuration.

Back up configurations
----------------------

The only OSQuery-specific state you need to preserve is the charm's
configuration. Capture it from the model so you can reapply it later:

.. code-block:: bash

    juju config osquery > osquery-config-backup.yaml

Because sensitive values (such as the enrollment secret and TLS keys) are held
in Juju secrets and file-backed configuration, back those source materials up
through your normal secret-management process rather than relying on the model.

To protect the model itself — including its configuration and secrets — back up
the Juju controller. See the
:ref:`Juju backup documentation <juju:manage-controllers>`.

Restore
-------

To restore the deployment, :ref:`redeploy the charm <how_to_redeploy>` and
reapply the configuration you captured above.

You can reapply all of the captured settings at once by passing the backup file
to ``juju config``:

.. code-block:: bash

    juju config osquery --file osquery-config-backup.yaml

Sensitive values held in Juju secrets and file-backed configuration aren't
included in this file, so restore those from your secret-management process as
described above.
