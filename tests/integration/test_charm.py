# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests that deploy the OSQuery subordinate charm."""

import jubilant
import pytest

from .conftest import BASES, CHARM_NAME, PACKAGE_NAME, PRINCIPAL_CHARM


@pytest.mark.parametrize("base", BASES)
def test_deploy_and_relate(juju: jubilant.Juju, charm_paths, base: str):
    """The subordinate deploys, relates to a principal and becomes active.

    The charm is built for each supported Ubuntu base, so this test runs once
    per base to confirm the base-specific artifact installs OSQuery from the
    PPA on a matching principal machine.

    Steps:
    - Deploy the `ubuntu` principal application on the base under test.
    - Deploy the matching OSQuery subordinate artifact for that base.
    - Relate the two and wait for the subordinate to become active.
    - Confirm OSQuery is installed on the principal machine.
    - Remove the subordinate and confirm OSQuery is uninstalled.
    """
    # Give each base its own application names so the parametrised runs can
    # share a single Juju model without colliding.
    suffix = base.split("@", 1)[1].replace(".", "")
    principal_app = f"ubuntu-{suffix}"
    osquery_app = f"osquery-{suffix}"

    juju.deploy(PRINCIPAL_CHARM, principal_app, base=base)
    juju.deploy(charm_paths[CHARM_NAME][base], osquery_app, base=base)
    juju.integrate(principal_app, osquery_app)

    juju.wait(
        lambda status: jubilant.all_active(status, principal_app, osquery_app),
        timeout=20 * 60,
    )

    # The subordinate installs OSQuery onto the principal's machine.
    installed = juju.exec(
        "dpkg-query",
        "-f",
        "${db:Status-Status}",
        "-W",
        PACKAGE_NAME,
        unit=f"{principal_app}/0",
        wait=60,
    )
    assert installed.stdout.strip() == "installed"

    # Removing the subordinate runs its stop hook, which uninstalls OSQuery.
    juju.remove_application(osquery_app)
    juju.wait(lambda status: osquery_app not in status.apps, timeout=10 * 60)

    # After `apt-get remove` the package leaves the "installed" state (dpkg still
    # knows it while config files linger, so check the status field, not the
    # exit code).
    removed = juju.exec(
        "dpkg-query",
        "-f",
        "${db:Status-Status}",
        "-W",
        PACKAGE_NAME,
        unit=f"{principal_app}/0",
        wait=60,
    )
    assert removed.stdout.strip() != "installed"
