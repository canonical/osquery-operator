# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

run "basic_deploy" {
  variables {
    model_uuid = run.setup_tests.model_uuid
    channel    = "latest/edge"
    # renovate: depName="osquery"
    revision = 1
    # The two required options; without them the subordinate stays blocked and
    # never reaches active status in the integration_test run below.
    config = {
      "controller-uri"      = "controller.example.com"
      "controller-env-uuid" = "test-env-uuid"
    }
  }

  assert {
    condition     = output.app_name == "osquery"
    error_message = "osquery app_name did not match expected"
  }
}

run "integration_test" {
  variables {
    model_uuid = run.setup_tests.model_uuid
  }

  module {
    source = "./tests/integration_test"
  }

  assert {
    condition     = data.external.app_status.result.status == "active"
    error_message = "osquery did not reach active status after integrating with a principal"
  }
}
