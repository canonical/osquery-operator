# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.osquery.name
}

output "requires" {
  description = "Integration endpoints (relations) that this charm requires."
  value = {
    # OSQuery is a subordinate; it must be related to a principal application
    # over the `juju-info` interface to be scheduled onto a machine.
    general_info = "general-info"
  }
}
