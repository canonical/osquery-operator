.. meta::
   :description: An explanation of the design decisions behind the OSQuery charm.

.. _explanation_charm_design:

Charm design
============

This page explains the main design decisions behind the OSQuery charm and the
reasoning that motivates them.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO
.. vale Canonical.500-Repeated-words = NO

A subordinate machine charm
---------------------------

OSQuery is endpoint security monitoring software: its purpose is to observe the
host it runs on. That job only makes sense on the same machine as the workload
being monitored, so the charm is designed as a `subordinate charm
<https://documentation.ubuntu.com/juju/3.6/reference/charm/#subordinate-charm>`_
that attaches to a principal application over the generic ``juju-info``
interface. This lets a single OSQuery application monitor any principal machine
charm without that charm needing to know anything about OSQuery.

It's a machine charm rather than a Kubernetes charm because ``osqueryd`` runs as
a host daemon that inspects operating-system state — processes, sockets,
packages, and kernel events — which requires direct access to the host rather
than a container sandbox.

Installing from a PPA
---------------------

The charm installs the Canonical SecOps fork of OSQuery from a Launchpad-hosted
PPA using the host's package manager, and runs it as the ``osqueryd`` systemd
service. Distributing the workload as a Debian package (rather than, say, a snap
or an OCI image) keeps the agent close to the host it monitors and lets it use
the platform's native service management.

Configuration-driven reconciliation
-----------------------------------

The charm has no actions. Instead, all of its behavior is driven by
configuration, and it applies that configuration through a holistic *reconcile*
loop. Every relevant Juju event runs the same idempotent handler, which ensures
OSQuery is installed, renders the configuration into the OSQuery flagfile, writes
the file-backed secrets, restarts the daemon if needed, and reports status.

This design keeps the charm simple and predictable: there's exactly one code path
that brings the host to the desired state, so the charm behaves the same way
regardless of which event triggered it. If a required value is missing, the charm
reports a ``blocked`` status rather than failing, making misconfiguration easy to
diagnose. See :ref:`the charm architecture documentation <reference_charm_architecture>` for
the module-level breakdown.

Separating workload logic from Juju logic
-----------------------------------------

The host-facing workload logic (installing the package and managing the service)
lives in a module that deliberately imports nothing from Ops or Juju. This
separation makes the workload logic straightforward to unit test in isolation and
keeps the charm's Juju-facing concerns (events, configuration, status) cleanly
separated from its host-facing concerns.

Talking to a controller instead of Juju relations
-------------------------------------------------

An OSQuery fleet is coordinated by a central OSQuery Controller that owns the
query schedules, telemetry rules, and log storage. The charm connects each agent
to that controller directly over TLS rather than modelling the controller as a
Juju relation. This keeps the charm aligned with how OSQuery fleets are operated
in practice and avoids duplicating the controller's responsibilities in Juju.
