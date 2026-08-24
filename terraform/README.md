<!-- Remember to update this file for your charm -- replace __charm_name__ with the appropriate name. -->

This folder contains a base [Terraform][Terraform] module for the `osquery` charm.

The module uses the [Terraform Juju provider][Terraform Juju provider] to model the charm
deployment onto any machine cloud environment managed by [Juju][Juju].

`osquery` is a **subordinate machine charm**. It does not run on its own machine;
instead Juju co-locates one OSQuery unit next to every unit of the principal
application it is related to over the `juju-info` interface. For this reason the
module deliberately does not expose a `units` variable — the unit count is
derived from the principal.

## Module structure

- **main.tf** - Defines the `osquery` Juju application to be deployed.
- **variables.tf** - Allows customization of the deployment, such as the Juju
  model, application name, channel, revision, base and constraints.
- **outputs.tf** - Integrates the module with other Terraform modules, primarily
  by exposing the required integration endpoints and the deployed Juju application.
- **versions.tf** - Defines the Terraform and provider versions.

The tables below (requirements, providers, resources, inputs and outputs) are
generated automatically from the module source with [terraform-docs][terraform-docs].
Do not edit them by hand; regenerate them with `terraform-docs .` from this
directory.

## Using the `osquery` base module in higher level modules

If you want to use `osquery` as part of your Terraform module, import it like
shown below:

```text
data "juju_model" "my_model" {
  name = var.model
}

module "osquery" {
  source = "git::https://github.com/canonical/osquery-operator//terraform"

  model_uuid = data.juju_model.my_model.uuid
  # (Customize app_name, channel, revision, base or constraints here if needed)
}
```

Because OSQuery is a subordinate, you must relate it to a principal machine
application over its `general-info` endpoint. For example, to monitor a
`ubuntu` principal:

```text
resource "juju_application" "ubuntu" {
  model_uuid = data.juju_model.my_model.uuid
  charm {
    name    = "ubuntu"
    base    = "ubuntu@24.04"
    channel = "latest/stable"
  }
}

resource "juju_integration" "osquery" {
  model_uuid = data.juju_model.my_model.uuid

  application {
    name     = module.osquery.application.name
    endpoint = module.osquery.requires.general_info.endpoint
  }

  application {
    name = juju_application.ubuntu.name
  }
}
```

The complete list of available integrations can be found [in the Integrations tab][osquery-integrations].

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| terraform | ~> 1.12 |
| juju | ~> 1.0 |

## Providers

| Name | Version |
|------|---------|
| juju | ~> 1.0 |

## Resources

| Name | Type |
|------|------|
| [juju_application.osquery](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| model\_uuid | UUID of the Juju model where the application will be deployed. | `string` | n/a | yes |
| app\_name | Name of the application in the Juju model. | `string` | `"osquery"` | no |
| base | The operating system on which to deploy. Supported: ubuntu@22.04, ubuntu@24.04 and ubuntu@26.04. | `string` | `"ubuntu@24.04"` | no |
| channel | The channel to use when deploying a charm. | `string` | `"latest/stable"` | no |
| config | Application config. Details about available options can be found at https://charmhub.io/osquery/configurations. | `map(string)` | `{}` | no |
| constraints | Juju constraints to apply for this application. | `string` | `null` | no |
| revision | Revision number of the charm | `number` | `null` | no |

## Outputs

| Name | Description |
|------|-------------|
| application | Object representing the deployed application. |
| requires | Integration endpoints (relations) that this charm requires. |
<!-- END_TF_DOCS -->

[Terraform]: https://developer.hashicorp.com/terraform
[Terraform Juju provider]: https://registry.terraform.io/providers/juju/juju/latest
[Juju]: https://juju.is
[osquery-integrations]: https://charmhub.io/osquery/integrations
[terraform-docs]: https://terraform-docs.io
