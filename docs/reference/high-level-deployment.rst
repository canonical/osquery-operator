.. meta::
   :description: A high-level overview of a typical OSQuery charm deployment.

.. _reference_high_level_deployment:

High-level deployment overview
==============================

This page shows how the OSQuery charm fits into a typical deployment.

The OSQuery charm is a subordinate that runs on the same machine as a principal
application. On each host, the charm installs and manages the ``osqueryd``
daemon. Every agent connects outward over TLS to a centrally managed OSQuery
Controller, which supplies the agents' configuration and collects their logs.

.. mermaid::

    flowchart TD
        subgraph host1["Machine 1"]
            principal1["Principal application unit"]
            osquery1["OSQuery subordinate<br/>(osqueryd)"]
            principal1 -.->|general-info| osquery1
        end
        subgraph host2["Machine 2"]
            principal2["Principal application unit"]
            osquery2["OSQuery subordinate<br/>(osqueryd)"]
            principal2 -.->|general-info| osquery2
        end
        controller["OSQuery Controller"]
        osquery1 -->|TLS: enroll / config / logs| controller
        osquery2 -->|TLS: enroll / config / logs| controller

Key points:

- The ``general-info`` relation places one OSQuery subordinate unit on each
  principal machine. See :ref:`Relation endpoints <reference_relation_endpoints>`.
- Each ``osqueryd`` agent is configured from the Juju configuration, which the
  charm renders into an OSQuery flagfile. See :ref:`Configurations
  <reference_configurations>`.
- All agents communicate with the OSQuery Controller over TLS. The controller,
  not Juju, owns the fleet's query schedules, telemetry rules, and log storage.

.. TODO: Add a link to the OSQuery Controller deployment documentation once it's
   published.
