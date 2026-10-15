.. meta::
   :description: Reference for the osquery controller and how it relates to the osquery charm.

.. _reference_osquery_controller:

The osquery controller
======================

.. vale Canonical.013-Spell-out-numbers-below-10 = NO
.. vale Canonical.500-Repeated-words = NO

The *osquery controller* is the central service that an osquery fleet enrolls
with. It's a separate component from this charm: the charm manages the
``osqueryd`` agent on each host, while the controller owns the fleet's query
schedules, telemetry rules, and log storage. A working deployment needs both —
the charm to run and configure the agents, and the controller to coordinate them.

This charm targets `osctrl <https://osctrl.net/>`_, an open-source osquery fleet
manager that implements the osquery remote API as a TLS endpoint. Deploying and
operating osctrl is out of scope for this documentation; see the `osctrl
documentation <https://docs.osctrl.net/>`_ for that. This charm is concerned only
with the agent side.

Relationship between the charm and the controller
-------------------------------------------------

The charm and the controller are deployed and operated independently:

- The **charm** is a Juju subordinate that installs the ``c-osquery`` snap, runs
  the ``osqueryd`` daemon, and renders Juju configuration into the osquery
  flagfile. See :ref:`the charm architecture <reference_charm_architecture>`.
- The **controller** is deployed outside of Juju. Deploying and operating the
  controller is out of scope for this documentation.

Each agent connects *outward* to the controller over TLS; the controller never
connects back into the Juju model. See :ref:`the high-level deployment overview
<reference_high_level_deployment>` for the topology.

The charm doesn't model the controller as a Juju relation. Instead, you give the
charm the controller's connection details through configuration, and the agent
enrolls directly. See :ref:`How to enroll the agent with a controller
<how_to_enroll_with_controller>`.

How the agent talks to the controller
-------------------------------------

The controller implements the upstream `osquery remote server (TLS) API
<https://osquery.readthedocs.io/en/stable/deployment/remote/>`_. The charm
configures the agent's TLS plugin by translating a small number of Juju options
into the corresponding ``osqueryd`` flags in the flagfile:

- ``controller-uri`` sets ``--tls_hostname``, the host the agent connects to.
- ``controller-env-uuid`` is the UUID of an osctrl *environment*; it expands into
  that environment's enrollment, configuration, logging, and distributed-query
  TLS endpoints (``/<uuid>/enroll``, ``/<uuid>/config``, ``/<uuid>/log``, and so
  on).
- ``enroll-secret`` provides the environment's enrollment secret, which the agent
  presents to the controller's enroll endpoint.
- ``tls-server-certs`` pins the environment's TLS certificate when the controller
  presents a private or self-signed certificate. ``tls-client-cert`` and
  ``tls-client-key`` add mutual TLS for the uncommon case where the controller is
  fronted by a proxy that requires it.

See the :ref:`Configurations reference <reference_configurations>` for the full
option-to-flag mapping, and :ref:`the cryptographic overview
<reference_cryptographic_overview>` for how the TLS material is handled.

The flagfile
------------

The charm's single source of truth for the agent is the osquery *flagfile*. The
controller-related options above are rendered into this file alongside the
agent's other flags; the agent reads it on start-up and reload. The charm
re-renders the flagfile and restarts ``osqueryd`` whenever the relevant
configuration changes. See the :ref:`Configurations reference
<reference_configurations>` for the file's location and contents.

Data held by the controller
---------------------------

The controller is the system of record for the data an
osquery fleet produces: scheduled query results, status logs, and
distributed-query responses. Because this data is shipped directly to the
controller over TLS, the charm doesn't expose it as Juju or Prometheus metrics.
See :ref:`Metrics <reference_metrics>`.

For the shape of this data and the endpoints it flows through, see the upstream
`osquery remote server (TLS) API
<https://osquery.readthedocs.io/en/stable/deployment/remote/>`_ documentation. For
how osctrl stores and exposes it — nodes, scheduled query results, status logs,
and distributed-query results — see the `osctrl documentation
<https://docs.osctrl.net/>`_.

Further reading
---------------

- :ref:`How to enroll the agent with a controller <how_to_enroll_with_controller>`
- :ref:`Connect the osquery agent to a controller <tutorial_advanced_deployment>`
