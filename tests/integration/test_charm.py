# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests that deploy the OSQuery subordinate charm."""

import jubilant

from .conftest import OSQUERY_APP, PRINCIPAL_APP


def test_deploy_and_relate(juju: jubilant.Juju, charm_file: str):
    """The subordinate deploys, relates to a principal and becomes active.

    Steps:
    - Deploy the `ubuntu` principal application.
    - Deploy the OSQuery subordinate.
    - Relate the two and wait for the subordinate to become active.
    """
    juju.deploy(PRINCIPAL_APP, base="ubuntu@24.04")
    juju.deploy(
        charm_file,
        OSQUERY_APP,
        base="ubuntu@24.04",
    )
    juju.integrate(PRINCIPAL_APP, OSQUERY_APP)

    juju.wait(
        lambda status: jubilant.all_active(status, PRINCIPAL_APP, OSQUERY_APP),
        timeout=20 * 60,
    )
