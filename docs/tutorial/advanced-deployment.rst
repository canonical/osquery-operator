.. meta::
   :description: Connect the OSQuery agent to an OSQuery Controller using Juju configuration and secrets.

.. _tutorial_advanced_deployment:

Connect the OSQuery agent to a controller
=========================================

In the :ref:`basic tutorial <tutorial_basic_deployment>` you deployed the
OSQuery charm and confirmed that the ``osqueryd`` daemon was installed. In this
tutorial you'll finish the deployment by connecting the agent to an OSQuery
Controller, which supplies the agent's configuration (query schedules, telemetry
rules, and query tasks) and collects its logs.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO
.. vale Canonical.500-Repeated-words = NO

What you'll need
----------------

- The deployment from the :ref:`basic tutorial <tutorial_basic_deployment>`.
- The connection details for an OSQuery Controller:

  - The controller's hostname or URI.
  - The environment UUID assigned to your fleet.
  - An enrollment secret.
  - The TLS certificates used to authenticate to the controller.

.. TODO: Link to the OSQuery Controller documentation once it's published, so
   readers know how to obtain these values.

What you'll do
--------------

- Point the agent at a controller.
- Provide the enrollment secret through a Juju secret.
- Provide the TLS certificates.
- Verify that the agent enrolls.

Point the agent at a controller
-------------------------------

The agent needs to know the controller's address and the environment UUID for
your fleet. Set both with ``juju config``:

.. code-block:: bash

    juju config osquery \
      controller-uri=controller.example.com \
      controller-env-uuid=00000000-0000-0000-0000-000000000000

The ``controller-uri`` sets the TLS hostname the agent connects to, and the
``controller-env-uuid`` is expanded into the per-environment enrollment,
configuration, logging, and distributed-query endpoints.

Provide the enrollment secret
-----------------------------

The enrollment secret authenticates the agent to the controller during
enrollment. Because it's sensitive, it's delivered through a `Juju secret
<https://canonical.com/juju/docs/juju-cli/3.6/reference/secret/>`_ rather than a
plain configuration value.

Create the secret and grant the charm access to it:

.. code-block:: bash

    secret_id=$(juju add-secret osquery-enroll-secret token=<your-enrollment-secret>)
    juju grant-secret "$secret_id" osquery
    juju config osquery enroll-secret="$secret_id"

Provide the TLS certificates
----------------------------

The agent authenticates to the controller with mutual TLS. Provide the server
CA, the client certificate, and the client key as file-backed configuration
options:

.. code-block:: bash

    juju config osquery \
      tls-server-certs="$(cat server-ca.pem)" \
      tls-client-cert="$(cat client.pem)" \
      tls-client-key="$(cat client-key.pem)"

Verify that the agent enrolls
-----------------------------

Watch the status until the charm settles into ``active``:

.. code-block:: bash

    juju status --watch 2s

Once the configuration is complete and valid, the charm renders the OSQuery
flagfile, restarts ``osqueryd``, and the agent enrolls with the controller. You
can confirm the daemon is running on the host with:

.. code-block:: bash

    juju ssh ubuntu/0 systemctl status osqueryd

Next steps
----------

To learn how to keep your deployment healthy, see the :ref:`how-to guides
<how_to_index>`, in particular :ref:`how to troubleshoot <how_to_troubleshoot>`.
