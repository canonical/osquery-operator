.. meta::
   :description: Learn how to deploy the OSQuery charm with Terraform.

.. _how_to_terraform:

How to deploy with Terraform
============================

This charm ships a `Terraform <https://www.terraform.io/>`_ module that wraps the
Juju provider, so you can manage an OSQuery deployment declaratively alongside the
rest of your infrastructure.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO

Prerequisites
-------------

- Terraform installed.
- The `Juju Terraform provider <https://registry.terraform.io/providers/juju/juju/latest>`_
  configured against your Juju controller.
- An existing Juju model, or a principal application to attach the subordinate to.

Use the module
--------------

Reference the module from the charm's repository in your Terraform configuration:

.. code-block:: hcl

    module "osquery" {
      source     = "git::https://github.com/canonical/osquery-operator//terraform"
      model_name = "my-model"
    }

The module's inputs and outputs are documented in the :ref:`Terraform reference
<reference_terraform>` and in the module's own ``README``.

Plan and apply
--------------

Initialize the working directory, review the plan, and apply it:

.. code-block:: bash

    terraform init
    terraform plan
    terraform apply

After ``terraform apply`` completes, integrate the OSQuery subordinate with a
principal application and configure it as described in the :ref:`advanced
tutorial <tutorial_advanced_deployment>`.
