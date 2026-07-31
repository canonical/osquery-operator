.. meta::
   :description: Technical reference for the Terraform module available for deploying the __charm_name__ charm.

.. _reference_terraform:

Terraform module
================

The OSQuery charm ships a Terraform module that wraps the `Juju Terraform
provider <https://registry.terraform.io/providers/juju/juju/latest>`_, so you can
deploy and manage the charm declaratively. The module source lives in the
``terraform/`` directory of the repository.

For step-by-step usage instructions, see :ref:`How to deploy with Terraform
<how_to_terraform>`.

Module contents
---------------

.. list-table::
    :header-rows: 1

    * - File
      - Purpose
    * - ``main.tf``
      - Declares the ``juju_application`` resource for the OSQuery charm.
    * - ``variables.tf``
      - Declares the module's input variables.
    * - ``outputs.tf``
      - Declares the module's outputs, such as the application name.
    * - ``versions.tf``
      - Pins the required Terraform and provider versions.

Because OSQuery is a subordinate charm, the module intentionally omits the
``units`` input: Juju co-locates one OSQuery unit next to every unit of the
principal application it's related to. The module exposes an ``app_name`` output
and a ``requires`` output that surfaces the ``general-info`` endpoint, so
higher-level modules can integrate OSQuery with a principal application.

The authoritative description of the module's inputs and outputs is maintained
alongside the module itself:

- `Terraform module README <https://github.com/canonical/osquery-operator/blob/main/terraform/README.md>`_

.. TODO: Publish the module to the Terraform Registry and link it here once
   available.
