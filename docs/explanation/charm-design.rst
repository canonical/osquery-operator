.. meta::
   :description: An explanation of the design decisions behind the osquery charm.

.. _explanation_charm_design:

Charm design
============

Osquery is endpoint security monitoring software: its purpose is to observe the
host it runs on. That job only makes sense on the same machine as the workload
being monitored, so the charm is designed as a
:ref:`subordinate charm <juju:subordinate-charm>`
that attaches to a principal application over the generic ``juju-info``
interface. This lets a single osquery application monitor any principal machine
charm without that charm needing to know anything about osquery.

It's a machine charm rather than a Kubernetes charm because ``osqueryd`` runs as
a host daemon that inspects operating-system state — processes, sockets,
packages, and kernel events — which requires direct access to the host rather
than a container sandbox.

Installing from a snap
----------------------

The charm installs the Canonical SecOps fork of osquery from the
`c-osquery snap <https://snapcraft.io/c-osquery>`_, on the channel set in
``snap-channel``, and runs the ``osqueryd`` daemon as the snap's
``snap.c-osquery.osqueryd`` systemd service. A single snap build serves every
supported Ubuntu base and is the artifact the fork tests before each release.
The snap uses classic confinement because osquery's eBPF backend needs
host-wide tracing privileges that no strict-confinement interface grants.

Configuration-driven reconciliation
-----------------------------------

The charm has no actions. Instead, all of its behavior is driven by
configuration, and it applies that configuration through a holistic *reconcile*
loop. Every relevant Juju event runs the same idempotent handler, which ensures
osquery is installed, renders the configuration into the osquery flagfile, writes
the file-backed secrets, restarts the daemon if needed, and reports status.

This design keeps the charm simple and predictable: there's exactly one code path
that brings the host to the desired state, so the charm behaves the same way
regardless of which event triggered it. If a required value is missing, the charm
reports a ``blocked`` status rather than failing, making misconfiguration easy to
diagnose. See :ref:`the charm architecture documentation <reference_charm_architecture>` for
the module-level breakdown.

Separating workload logic from Juju logic
-----------------------------------------

The host-facing workload logic (installing the snap and managing the service)
lives in a module that deliberately imports nothing from Ops or Juju. This
separation makes the workload logic straightforward to unit test in isolation and
keeps the charm's Juju-facing concerns (events, configuration, status) cleanly
separated from its host-facing concerns.

Talking to a controller instead of Juju relations
-------------------------------------------------

An osquery fleet is coordinated by a central osquery Controller that owns the
query schedules, telemetry rules, and log storage. The charm connects each agent
to that controller directly over TLS rather than modelling the controller as a
Juju relation. This keeps the charm aligned with how osquery fleets are operated
in practice and avoids duplicating the controller's responsibilities in Juju.
