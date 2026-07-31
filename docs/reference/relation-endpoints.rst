.. meta::
   :description: Reference for the relation endpoints exposed by the OSQuery charm.

.. _reference_relation_endpoints:

Relation endpoints
==================

`Relation endpoints <https://documentation.ubuntu.com/juju/3.6/reference/relation/>`_
are the integration points a charm exposes so it can be connected to other
applications.

The OSQuery charm is a subordinate charm. It requires a single endpoint that
attaches it to a principal application, and it doesn't provide any endpoints of
its own.

Requires
--------

.. list-table::
    :header-rows: 1

    * - Endpoint
      - Interface
      - Scope
      - Description
    * - ``general-info``
      - ``juju-info``
      - ``container``
      - Attaches the OSQuery subordinate to a principal application so that the
        ``osqueryd`` agent runs on the same machine. The ``container`` scope
        restricts the relation to units that share a machine.

Because OSQuery is endpoint security monitoring software, it's designed to run
alongside any workload. Relating it over the generic ``juju-info`` interface lets
it attach to any principal machine charm — for example, the ``ubuntu`` charm — so
you can monitor arbitrary hosts.

Provides
--------

The charm doesn't currently provide any relation endpoints. It communicates with
its OSQuery Controller directly over TLS rather than through a Juju relation.

.. TODO: If the charm gains provided endpoints (for example, an observability or
   controller integration), document them here.
