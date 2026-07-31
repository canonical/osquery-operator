# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_application" "osquery" {
  name       = var.app_name
  model_uuid = var.model_uuid

  charm {
    name     = "osquery"
    channel  = var.channel
    revision = var.revision
    base     = var.base
  }

  config      = var.config
  constraints = var.constraints

  # `units` is intentionally omitted. OSQuery is a subordinate charm: it does
  # not get its own units, instead Juju co-locates one OSQuery unit next to
  # every unit of the principal application it is related to. Setting `units`
  # on a subordinate application is rejected by the Juju Terraform provider.
}
