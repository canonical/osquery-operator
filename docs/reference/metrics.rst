.. meta::
   :description: Reference for the metrics exposed by the osquery charm.

.. _reference_metrics:

Metrics
=======

The osquery charm doesn't currently expose Juju or Prometheus metrics.

Osquery's operational data — scheduled query results, telemetry, and status
logs — is shipped directly to the osquery Controller over TLS, which is the
system of record for that data. The charm doesn't presently surface a separate
metrics endpoint for Juju or for the Canonical Observability Stack.

For visibility into a running deployment today, use the Juju status and logs as
described in :ref:`how to troubleshoot <how_to_troubleshoot>`.
