.. meta::
   :description: An overview of the OSQuery charm's architecture, modules, and reconcile flow.

.. _reference_charm_architecture:

Charm architecture
==================

The OSQuery charm is a subordinate machine charm. Rather than running a workload
in a container, it installs and manages the ``osqueryd`` daemon directly on the
principal's machine using the host's package manager and ``systemd``.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO
.. vale Canonical.500-Repeated-words = NO

Architecture overview
---------------------

The OSQuery charm is a machine charm, so it is not containerized: there is no OCI
image and no Pebble services. Both the Juju unit agent (which runs the charm code) and the
``osqueryd`` workload it manages run directly on the principal's host, sharing
the same machine as the principal unit. The charm's only moving parts are the
charm code, the ``osqueryd`` systemd service, and the files the charm writes
under ``/etc/osquery``.

.. mermaid::

    flowchart TB
        subgraph machine["Principal machine (no container)"]
            principal["Principal unit"]
            subgraph agent["Juju unit agent"]
                charm["OSQuery charm code<br/>(charm.py reconcile)"]
            end
            osqueryd["osqueryd<br/>systemd service"]
            subgraph files["/etc/osquery"]
                flagfile["osquery.flags"]
                secrets["enroll.secret<br/>TLS certificates"]
            end
            principal -.->|osquery:general-info| charm
            charm -->|installs & manages| osqueryd
            charm -->|writes| flagfile
            charm -->|writes| secrets
            osqueryd -->|reads| flagfile
            osqueryd -->|reads| secrets
        end
        controller["OSQuery Controller"]
        osqueryd -->|TLS: enroll / config / logs| controller

Workload
--------

The charm installs the Canonical SecOps fork of OSQuery from a Launchpad-hosted
PPA. Once installed, OSQuery runs as the ``osqueryd`` systemd service. The daemon
reads its command-line flags from a flagfile on disk; the charm generates this
flagfile from the Juju configuration, so changing a configuration value and
restarting the daemon is how the charm applies changes to the workload.

The agent connects outward over TLS to a centrally managed OSQuery Controller,
which supplies its configuration (query schedules, telemetry rules, and query
tasks) and collects its logs.

Reconcile pattern
-----------------

The charm follows a holistic reconcile pattern. A single handler,
``_reconcile``, is observed on every relevant lifecycle event —
``install``, ``upgrade-charm``, ``start``, ``config-changed``,
``secret-changed``, and ``update-status``. On each event the handler:

#. Ensures OSQuery is installed, installing it from the PPA if it isn't.
#. Renders the current Juju configuration into the OSQuery flagfile and writes
   the file-backed secrets (the enrollment secret and TLS material) to disk.
#. Restarts the ``osqueryd`` daemon if necessary.
#. Reports the resulting unit status.

Because the handler is idempotent, it's safe to run on every event. If a required
configuration value is missing or invalid, the charm sets a ``blocked`` status
with a descriptive message instead of failing the hook. The ``stop`` event is
handled separately to clean up the workload when the unit is removed.

.. mermaid::

    flowchart TD
        event["Lifecycle event<br/>(install, config-changed, ...)"] --> reconcile["_reconcile"]
        reconcile --> installed{"OSQuery<br/>installed?"}
        installed -->|no| install["Install from PPA"]
        installed -->|yes| render["Render flagfile<br/>+ write secrets"]
        install --> render
        render --> valid{"Config<br/>valid?"}
        valid -->|no| blocked["Set blocked status"]
        valid -->|yes| restart["Restart osqueryd<br/>if config changed"]
        restart --> active["Set active status"]

Code structure
--------------

The charm is organized into focused modules that separate the Juju-facing logic
from the host-facing logic:

.. list-table::
    :header-rows: 1

    * - Module
      - Responsibility
    * - ``src/charm.py``
      - The ``OSQueryCharm`` class. Observes Juju events, drives the reconcile
        loop, reads configuration and secrets, and sets unit status.
    * - ``src/osquery.py``
      - Host workload management: installing and removing the OSQuery package
        from the PPA and managing the ``osqueryd`` service. The module contains no Juju
        or Ops imports, so it can be reasoned about and tested in isolation.
    * - ``src/flags.py``
      - Translates Juju configuration values into the OSQuery flagfile and
        determines which required options are unset.
    * - ``src/errors.py``
      - The charm's exception hierarchy, including ``OSQueryError``,
        ``OSQueryConfigError``, and ``OSQueryInstallError``.

Juju integration
----------------

As a subordinate, the charm attaches to a principal application through the
``general-info`` relation (interface ``juju-info``, ``container`` scope). This
places one OSQuery unit on each principal machine. See :ref:`Relation endpoints
<reference_relation_endpoints>` for details.

.. vale Canonical.004-Canonical-product-names = NO

For the configuration options that drive the flagfile, see :ref:`Configurations
<reference_configurations>`. For the events the charm observes, see
:ref:`Juju events <reference_juju_events>`.

.. vale Canonical.004-Canonical-product-names = YES
