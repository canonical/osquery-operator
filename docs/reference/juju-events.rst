.. meta::
   :description: Reference documentation for all Juju events observed by the OSQuery charm.

.. _reference_juju_events:

Juju events
===========

The charm follows a holistic (reconcile) pattern: nearly every lifecycle event
is routed to a single idempotent handler that ensures OSQuery is installed,
renders the flagfile from the current configuration, and (re)starts the daemon.

The following Juju events are observed:

#. :ref:`install <juju:hook-install>`:

   installs OSQuery from the PPA and applies the initial configuration.

#. :ref:`upgrade-charm <juju:hook-upgrade-charm>`:

   re-runs the reconcile after a charm upgrade.

#. :ref:`start <juju:hook-start>`:

   reconciles when the unit starts.

#. :ref:`config-changed <juju:hook-config-changed>`:

   rebuilds the flagfile and secret files whenever an option changes, then
   restarts the daemon.

#. :ref:`secret-changed <juju:hook-secret-changed>`:

   re-reads a Juju secret (for example the enrollment secret or TLS client
   key) when its content is updated, and re-applies the configuration.

#. :ref:`update-status <juju:hook-update-status>`:

   periodically reconciles so the unit self-heals and reports accurate status.

#. :ref:`stop <juju:hook-stop>`:

   stops the daemon and uninstalls the OSQuery package during tear-down.


.. seealso::

   See more in the Juju docs: :ref:`Hook <juju:hook>`
