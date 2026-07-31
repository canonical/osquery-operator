.. meta::
   :description: Learn how the OSQuery charm relates to observability and the Canonical Observability Stack.

.. _how_to_integrate_with_cos:

How to integrate with COS
=========================

The `Canonical Observability Stack (COS) <https://charmhub.io/topics/canonical-observability-stack>`_
provides metrics, logging, and dashboards for Juju applications.

The OSQuery charm doesn't currently integrate with COS. OSQuery reports its
telemetry and logs directly to its own OSQuery Controller over TLS, which is the
system of record for endpoint security data. The charm doesn't presently expose
a metrics, logging, or dashboard endpoint for COS to consume.

.. TODO: If COS integration (for example, a Grafana Agent or Prometheus scrape
   endpoint) is added to the charm, document the integration steps here and
   update :ref:`the metrics reference <reference_metrics>`.

For the observability that's available today, see:

- :ref:`How to troubleshoot <how_to_troubleshoot>` for inspecting agent status
  and logs.
- :ref:`Metrics <reference_metrics>` for the charm's current metrics support.
