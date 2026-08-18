.. meta::
   :description: Reference documentation for all Juju events observed by the OSQuery charm.

.. _reference_juju_events:

Juju events
===========

The charm follows a holistic (reconcile) pattern: nearly every lifecycle event
is routed to a single idempotent handler that ensures OSQuery is installed,
renders the flagfile from the current configuration, and (re)starts the daemon.

The following Juju events are observed:

#. `install <https://canonical.com/juju/docs/juju-cli/latest/reference/hook/#install>`_:
      installs OSQuery from the PPA and applies the initial configuration.
#. `upgrade-charm <https://canonical.com/juju/docs/juju-cli/latest/reference/hook/#upgrade-charm>`_:
      re-runs the reconcile after a charm upgrade.
#. `start <https://canonical.com/juju/docs/juju-cli/latest/reference/hook/#start>`_:
      reconciles when the unit starts.
#. `config-changed <https://canonical.com/juju/docs/juju-cli/latest/reference/hook/#config-changed>`_:
      rebuilds the flagfile and secret files whenever an option changes, then
   restarts the daemon.
#. `secret-changed <https://canonical.com/juju/docs/juju-cli/latest/reference/hook/#secret-changed>`_:
      re-reads a Juju secret (for example the enrollment secret or TLS client
   key) when its content is updated, and re-applies the configuration.
#. `update-status <https://canonical.com/juju/docs/juju-cli/latest/reference/hook/#update-status>`_:
      periodically reconciles so the unit self-heals and reports accurate status.
#. `stop <https://canonical.com/juju/docs/juju-cli/latest/reference/hook/#stop>`_:
      stops the daemon and uninstalls the OSQuery package during tear-down.

.. seealso::

   See more in the Juju docs: `Hook
   <https://canonical.com/juju/docs/juju-cli/latest/reference/hook/>`_
