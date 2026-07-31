.. meta::
   :description: How-to guides for operating the OSQuery charm, including basic operations, upgrades, and development.

.. _how_to_index:

How-to guides
=============

Manage the full operations lifecycle of the OSQuery charm, from initial
deployment through production maintenance. Each guide assumes that you've
already deployed the charm with Juju.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO
.. vale Canonical.500-Repeated-words = NO

Basic operations
----------------

These guides cover common day-to-day tasks for a running deployment.

.. toctree::
    :hidden:
    :maxdepth: 1

    Integrate with COS <integrate-with-cos>
    Troubleshoot <troubleshoot>

Update and refresh
------------------

Backups, redeployments, and upgrades keep the OSQuery charm current and let it
benefit from new features and fixes.

.. toctree::
    :hidden:
    :maxdepth: 1

    Back up and restore <back-up-restore>
    Redeploy <redeploy>
    Upgrade <upgrade>

Development
-----------

These guides help you deploy the charm with Terraform and contribute to the
project.

.. toctree::
    :hidden:
    :maxdepth: 1

    Use Terraform <terraform>
    Contribute <contribute>
