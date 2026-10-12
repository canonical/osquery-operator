.. meta::
   :description: Provision an environment on an osquery Controller and enroll the agent, including obtaining and rotating enrollment secrets and TLS certificates.

.. _how_to_enroll_with_controller:

How to enroll the agent with a controller
=========================================

The osquery charm runs the ``osqueryd`` agent, but an agent is only useful once
it's enrolled with an :ref:`osquery Controller <reference_osquery_controller>`,
which supplies its configuration and collects its logs. This guide covers the
end-to-end flow: provisioning an environment on the controller, obtaining the
credentials the agent needs, applying them to the charm, and rotating them later.

Deploying and operating the controller itself is out of scope for this guide.
This charm targets `osctrl <https://osctrl.net/>`_, and the guide assumes you
already have a running osctrl deployment and can run ``osctrl-cli`` against it
(either directly against its database or through the osctrl API).

.. vale Canonical.013-Spell-out-numbers-below-10 = NO
.. vale Canonical.500-Repeated-words = NO

Prerequisites
-------------

- A deployed osquery charm. See the :ref:`tutorial <tutorial_basic_deployment>`.
- Access to a running osctrl deployment, with ``osctrl-cli`` configured to reach
  it and permission to manage environments.

Provision an environment on the controller
------------------------------------------

An *environment* in osctrl is a TLS endpoint that groups a set of nodes and holds
their enrollment secret, certificate, and configuration. From it you need two
values:

- the controller's hostname, for ``controller-uri``, and
- the environment UUID, for ``controller-env-uuid``.

Create an environment with ``osctrl-cli``, then read back its UUID:

.. code-block:: bash

    osctrl-cli environment add --name corp --hostname <controller-uri> --config --logger --query
    osctrl-cli environment show --name corp

``environment show`` prints the environment's details, including the UUID you pass
to ``controller-env-uuid``. See the `osctrl environment commands
<https://docs.osctrl.net/usage/osctrl-cli/environment/>`_ for the full set of
options.

For background on how the agent uses these values — the TLS hostname and the
per-environment enrollment, configuration, logging, and distributed-query
endpoints — see the upstream `osquery remote server (TLS) API
<https://osquery.readthedocs.io/en/stable/deployment/remote/>`_ documentation and
the :ref:`Configurations reference <reference_configurations>`.

Obtain an enrollment secret
---------------------------

The *enrollment secret* is a shared secret the agent presents to the controller's
enroll endpoint. The agent uses it once to negotiate a per-node key, which it
then uses to authenticate subsequent requests. osctrl generates a secret for each
environment; print it with ``osctrl-cli``:

.. code-block:: bash

    osctrl-cli environment node-actions secret --name corp

See `Simple shared secret enrollment
<https://osquery.readthedocs.io/en/stable/deployment/remote/#simple-shared-secret-enrollment>`_
upstream for how the secret is used during enrollment.

Apply the configuration to the charm
------------------------------------

Point the agent at the controller and environment:

.. code-block:: bash

    juju config osquery \
      controller-uri=<controller-uri> \
      controller-env-uuid=<controller-env-uuid>

Provide the enrollment secret through a :ref:`Juju secret <juju:secret>` so it
isn't stored in plain-text configuration:

.. code-block:: bash

    secret_id=$(juju add-secret osquery-enroll enroll-secret=<enrollment-secret>)
    juju grant-secret osquery-enroll osquery
    juju config osquery enroll-secret="$secret_id"

If your controller requires mutual TLS, also provide the certificates:

.. code-block:: bash

    juju config osquery \
      tls-server-certs="$(cat server-ca.pem)" \
      tls-client-cert="$(cat client.pem)" \
      tls-client-key="$(cat client-key.pem)"

See :ref:`Providing secrets <configurations_secrets>` for more on the
secret-backed options.

Verify enrollment
-----------------

Watch the deployment until it settles into ``active``:

.. code-block:: bash

    juju status --watch 2s

If a required option is missing, the unit reports ``blocked`` with a message
naming it. For deeper checks, see :ref:`how to troubleshoot <how_to_troubleshoot>`.

Rotate credentials
------------------

Rotate the enrollment secret and TLS credentials periodically, and immediately if
you suspect they're compromised. Rotation has two sides: issue new credentials on
osctrl, then update the charm's configuration to match.

On osctrl, rotate the environment's enrollment URL and read back the new secret:

.. code-block:: bash

    osctrl-cli environment node-actions rotate-enroll --name corp
    osctrl-cli environment node-actions secret --name corp

Then update the Juju secret so the charm reconciles the agent on its next
configuration change:

.. code-block:: bash

    juju update-secret osquery-enroll enroll-secret=<new-enrollment-secret>

If you also pin the controller's certificate, re-apply ``tls-server-certs`` with
the new PEM after rotating it on osctrl. The charm re-renders the flagfile and
restarts the agent on the next reconcile. See `how to manage secrets
<https://documentation.ubuntu.com/juju/3.6/howto/manage-secrets/>`_ for working
with Juju secrets.
