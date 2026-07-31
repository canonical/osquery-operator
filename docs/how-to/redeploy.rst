.. meta::
   :description: Learn how to redeploy the OSQuery charm.

.. _how_to_redeploy:

How to redeploy
===============

Because the OSQuery charm is stateless, redeploying it is straightforward: remove
the application and deploy it again against the same principal. The agent
re-enrolls with the OSQuery Controller once its configuration is reapplied.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO

Capture the current configuration
---------------------------------

Before removing the application, capture its configuration so you can reapply it:

.. code-block:: bash

    juju config osquery > osquery-config-backup.yaml

Remove the existing application
-------------------------------

Remove the OSQuery subordinate. This leaves the principal application untouched:

.. code-block:: bash

    juju remove-application osquery

Deploy and integrate again
--------------------------

Deploy the charm again and integrate it with the same principal application:

.. code-block:: bash

    juju deploy osquery
    juju integrate <principal-application> osquery

Reapply the configuration
-------------------------

Reapply the configuration you captured earlier, including the controller
settings, enrollment secret, and TLS certificates. See the :ref:`advanced
tutorial <tutorial_advanced_deployment>` for the full set of options.

Confirm that the charm settles into an ``active`` state:

.. code-block:: bash

    juju status --watch 2s
