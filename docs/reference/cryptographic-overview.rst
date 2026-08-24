.. meta::
   :description: Reference for the cryptographic technology used by the OSQuery charm.

.. _reference_cryptographic_overview:

Cryptographic overview
======================

This page summarizes the cryptographic technology the OSQuery charm relies on and
how sensitive material is handled.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO

Transport security
------------------

The OSQuery agent communicates with its OSQuery Controller exclusively over TLS.
All enrollment, configuration retrieval, log delivery, and distributed-query
traffic is carried over these TLS connections.

The agent always verifies the controller's server certificate. If
``tls-server-certs`` is left unset, the agent validates the controller against
its bundle of publicly trusted certificate authorities, so a controller that
presents a publicly trusted certificate is trusted without any extra
configuration. Set ``tls-server-certs`` only to pin a private or self-signed
certificate authority instead.

Client authentication (mutual TLS) is optional. When the controller requires it,
the agent authenticates itself using the client certificate and key provided in
``tls-client-cert`` and ``tls-client-key`` respectively.

Secrets handling
----------------

Sensitive configuration values are delivered to the charm through mechanisms that
keep them out of plain-text configuration:

- The enrollment secret is passed as a `Juju secret
  <https://canonical.com/juju/docs/juju-cli/3.6/reference/secret/>`_ referenced by
  the ``enroll-secret`` option, rather than as a plain configuration value.
- The TLS certificates and key are supplied as file-backed configuration
  options.

The charm writes these values into the OSQuery flagfile and the associated files
on the host so that ``osqueryd`` can read them at runtime. See :ref:`the security
explanation <explanation_security>` for the accompanying threat model and
best-practice guidance.

.. TODO: Document the specific cipher suites and TLS versions negotiated once the
   OSQuery Controller's cryptographic profile is finalized.
