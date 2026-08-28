.. meta::
   :description: Reference explaining that the OSQuery charm exposes no Juju actions.

.. _reference_actions:

Actions
=======

:ref:`Juju actions <juju:action>` are
operations that a charm exposes so operators can run them on demand.

.. vale Canonical.004-Canonical-product-names = NO

The OSQuery charm doesn't define any actions. Its behavior is entirely
configuration-driven: the charm reconciles the ``osqueryd`` daemon in response to
Juju events (such as configuration changes) rather than through operator-invoked
actions. See :ref:`Configurations <reference_configurations>` and
:ref:`Juju events <reference_juju_events>` for the mechanisms the charm does use.

.. vale Canonical.004-Canonical-product-names = YES

.. TODO: If actions are added to the charm in the future, document each action,
   its parameters, and its expected output here.
