# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

terraform {
  required_version = "~> 1.12"
  required_providers {
    external = {
      version = "> 2"
      source  = "hashicorp/external"
    }
    juju = {
      version = "~> 1.0"
      source  = "juju/juju"
    }
  }
}

provider "juju" {}

variable "model_uuid" {
  type = string
}

# OSQuery is a subordinate charm, so it needs a principal application to be
# scheduled onto a machine. `ubuntu` is a minimal principal machine charm that
# provides the `juju-info` interface every principal exposes.
resource "juju_application" "ubuntu" {
  model_uuid = var.model_uuid
  charm {
    base    = "ubuntu@24.04"
    channel = "latest/stable"
    name    = "ubuntu"
  }
}

resource "juju_integration" "osquery" {
  model_uuid = var.model_uuid

  application {
    name     = "osquery"
    endpoint = "general-info"
  }

  application {
    name = juju_application.ubuntu.name
  }
}

# tflint-ignore: terraform_unused_declarations
data "external" "app_status" {
  program = ["bash", "${path.module}/wait-for-active.sh", var.model_uuid, "osquery", "5m"]

  depends_on = [
    juju_integration.osquery
  ]
}
