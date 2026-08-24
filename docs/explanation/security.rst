.. meta::
   :description: A security overview of the OSQuery charm, including its threat model and best practices.

.. _explanation_security:

Security
========

This page provides an overview of the security posture of the OSQuery charm: how
it handles sensitive material, what to be aware of when operating it, and the
best practices that keep a deployment secure.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO
.. vale Canonical.500-Repeated-words = NO

Handling of sensitive material
------------------------------

The charm handles several pieces of sensitive material: the OSQuery enrollment
secret, and the TLS client certificate and key used to authenticate to the
controller.

The enrollment secret is provided as a `Juju secret
<https://documentation.ubuntu.com/juju/3.6/reference/secret/>`_ rather than a
plain configuration value, so it isn't stored in plain text in the model
configuration. The TLS certificates and key are supplied as file-backed
configuration options and written to disk on the host so ``osqueryd`` can read
them. Files that contain secret material are written with owner-only permissions
in a directory that isn't traversable by other users, so only the ``root`` user
that runs the daemon can read them.

Transport security
------------------

All communication between the OSQuery agent and its controller is protected by
mutual TLS. The agent authenticates the controller with a CA certificate and
authenticates itself with a client certificate and key. See :ref:`the
cryptographic overview <reference_cryptographic_overview>` for details.

Threat considerations
---------------------

- **Host access:** ``osqueryd`` runs as ``root`` and inspects sensitive
  operating-system state. Anyone with root access to a monitored host already has
  broad control of that host. The charm doesn't widen that boundary, but operators
  should apply the usual host-hardening practices.
- **Secret exposure:** Because the enrollment secret and TLS key grant the agent
  its identity with the controller, treat them as high-value credentials. Rotate
  them if you suspect compromise.
- **Controller trust:** The agent trusts the controller identified by its
  configuration. Ensure the ``controller-uri`` and TLS CA are correct so the
  agent only enrolls with a controller you control.

Best practices
--------------

- Provide the enrollment secret through a Juju secret and grant the charm access
  to it explicitly, rather than embedding credentials in plain configuration.
- Restrict who can access the Juju model, since model access implies control over
  the charm's configuration and secrets.
- Keep the charm up to date so the deployment benefits from security fixes in
  both the charm and the OSQuery package. See :ref:`how to upgrade
  <how_to_upgrade>`.

.. TODO: Link to the project's security policy and vulnerability-reporting
   process (SECURITY.md) once a public disclosure address is confirmed.
