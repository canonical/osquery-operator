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
  - Optionally, the TLS certificates used to authenticate to the controller, if
    your controller is configured to require them.

.. TODO: Link to the OSQuery Controller documentation once it's published, so
   readers know how to obtain these values.

What you'll do
--------------

- Point the agent at a controller.
- Provide the enrollment secret through a Juju secret.
- Optionally, provide the TLS certificates.
- Verify that the agent enrolls.

Point the agent at a controller
-------------------------------

The agent needs to know the controller's address and the environment UUID for
your fleet. Set both with ``juju config``:

.. code-block:: bash

    juju config osquery \
      controller-uri=<controller-uri> \
      controller-env-uuid=<controller-env-uuid>

The ``controller-uri`` sets the TLS hostname the agent connects to, and the
``controller-env-uuid`` is expanded into the per-environment enrollment,
configuration, logging, and distributed-query endpoints. Like the charm's other
options, these map directly to the underlying ``osqueryd`` flags; see the
:ref:`Configurations reference <reference_configurations>` for the full mapping.

Provide the enrollment secret
-----------------------------

The enrollment secret authenticates the agent to the controller during
enrollment. Because it's sensitive, it's delivered through a
:ref:`Juju secret <juju:secret>` rather than a
plain configuration value.

The enrollment secret is optional, but without it a controller that requires
one will reject the agent.

Create the secret and grant the charm access to it:

.. code-block:: bash

    secret_id=$(juju add-secret osquery-enroll-secret token=<your-enrollment-secret>)
    juju grant-secret "$secret_id" osquery
    juju config osquery enroll-secret="$secret_id"

Provide the TLS certificates (optional)
---------------------------------------

Mutual TLS is optional and most deployments don't use it: the enrollment secret
above is the common way to authenticate the agent. Only provide certificates if
your controller is configured to require them.

If your controller presents a publicly trusted certificate, you don't need to
set ``tls-server-certs`` at all; the agent already verifies the controller
against its bundle of publicly trusted certificate authorities. Provide it only
to pin a private or self-signed certificate authority.

When they're needed, the ``.pem`` files must be generated beforehand and
registered with the OSQuery Controller. Generating and registering them is
out of scope for this tutorial. Once you have them, provide the server CA, the
client certificate, and the client key as file-backed configuration options:

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

You should see the service reported as ``active (running)``:

.. code-block:: text

    ● osqueryd.service - The osquery daemon
         Loaded: loaded (/lib/systemd/system/osqueryd.service; enabled; vendor preset: enabled)
         Active: active (running) since Mon 2026-08-25 10:00:00 UTC; 1min ago
       Main PID: 12345 (osqueryd)
          Tasks: 8 (limit: 4915)
         Memory: 20.0M
            CPU: 250ms
         CGroup: /system.slice/osqueryd.service
                 ├─12345 /usr/bin/osqueryd --flagfile /etc/osquery/osquery.flags
                 └─12346 /usr/bin/osqueryd --flagfile /etc/osquery/osquery.flags

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

To learn how to keep your deployment healthy, see the :ref:`how-to guides
<how_to_index>`, in particular :ref:`how to troubleshoot <how_to_troubleshoot>`.

To understand the concepts behind what you just configured, see the
:ref:`charm design <explanation_charm_design>` and :ref:`security
<explanation_security>` explanations, and the :ref:`cryptographic overview
<reference_cryptographic_overview>`.
