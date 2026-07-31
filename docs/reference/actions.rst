.. meta::
   :description: Reference for the Juju actions supported by the OSQuery charm.

.. _reference_actions:

Actions
=======

`Juju actions <https://documentation.ubuntu.com/juju/3.6/reference/action/>`_ are
operations that a charm exposes so operators can run them on demand.

The OSQuery charm doesn't define any actions. Its behavior is entirely
configuration-driven: the charm reconciles the ``osqueryd`` daemon in response to
Juju events (such as configuration changes) rather than through operator-invoked
actions. See :ref:`Configurations <reference_configurations>` and :ref:`Juju
events <reference_juju_events>` for the mechanisms the charm does use.

.. TODO: If actions are added to the charm in the future, document each action,
   its parameters, and its expected output here.
