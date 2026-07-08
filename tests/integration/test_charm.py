# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests that deploy the OSQuery subordinate charm."""

import jubilant

from .conftest import OSQUERY_APP, PACKAGE_NAME, PRINCIPAL_APP


def test_deploy_and_relate(juju: jubilant.Juju, charm_file: str):
    """The subordinate deploys, relates to a principal and becomes active.

    Steps:
    - Deploy the `ubuntu` principal application.
    - Deploy the OSQuery subordinate.
    - Relate the two and wait for the subordinate to become active.
    - Confirm OSQuery is installed on the principal machine.
    - Remove the subordinate and confirm OSQuery is uninstalled.
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

    # The subordinate installs OSQuery onto the principal's machine.
    installed = juju.exec(
        "dpkg-query",
        "-f",
        "${db:Status-Status}",
        "-W",
        PACKAGE_NAME,
        unit=f"{PRINCIPAL_APP}/0",
        wait=60,
    )
    assert installed.stdout.strip() == "installed"

    # Removing the subordinate runs its stop hook, which uninstalls OSQuery.
    juju.remove_application(OSQUERY_APP)
    juju.wait(lambda status: OSQUERY_APP not in status.apps, timeout=10 * 60)

    # After `apt-get remove` the package leaves the "installed" state (dpkg still
    # knows it while config files linger, so check the status field, not the
    # exit code).
    removed = juju.exec(
        "dpkg-query",
        "-f",
        "${db:Status-Status}",
        "-W",
        PACKAGE_NAME,
        unit=f"{PRINCIPAL_APP}/0",
        wait=60,
    )
    assert removed.stdout.strip() != "installed"
