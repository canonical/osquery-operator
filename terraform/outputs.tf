# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "application" {
  description = "Object representing the deployed application."
  value       = juju_application.osquery
}

output "requires" {
  description = "Integration endpoints (relations) that this charm requires."
  value = {
    # OSQuery is a subordinate; it must be related to a principal application
    # over the `juju-info` interface to be scheduled onto a machine.
    general_info = {
      kind     = "endpoint"
      name     = juju_application.osquery.name
      endpoint = "general-info"
    }
  }
}
