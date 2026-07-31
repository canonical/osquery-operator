.. meta::
   :description: Reference for the metrics exposed by the OSQuery charm.

.. _reference_metrics:

Metrics
=======

The OSQuery charm doesn't currently expose Juju or Prometheus metrics.

OSQuery's operational data — scheduled query results, telemetry, and status
logs — is shipped directly to the OSQuery Controller over TLS, which is the
system of record for that data. The charm doesn't presently surface a separate
metrics endpoint for Juju or for the :ref:`Canonical Observability Stack
<how_to_integrate_with_cos>`.

For visibility into a running deployment today, use the Juju status and logs as
described in :ref:`how to troubleshoot <how_to_troubleshoot>`.

.. TODO: If a metrics endpoint (for example, a Prometheus scrape target or a
   COS integration) is added to the charm, document each metric, its type, and
   its labels here.
