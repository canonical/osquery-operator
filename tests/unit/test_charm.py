# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the OSQuery charm lifecycle."""

import pytest
from ops import testing

import osquery
from charm import OSQueryCharm


@pytest.fixture(name="ctx")
def ctx_fixture():
    """Return an ops testing context for the charm."""
    return testing.Context(OSQueryCharm)


@pytest.mark.parametrize(
    "event",
    [
        "install",
        "upgrade_charm",
        "start",
        "config_changed",
        "update_status",
    ],
)
def test_reconcile_installs_when_missing(ctx, patch_workload, event):
    """Every reconcile event installs a missing workload and reports active."""
    state = testing.State()

    out = ctx.run(getattr(ctx.on, event)(), state)

    assert patch_workload.installed_version == osquery.PACKAGE_VERSION
    assert patch_workload.install_count == 1
    assert out.unit_status == testing.ActiveStatus()


def test_reconcile_is_idempotent_when_pinned_version_installed(ctx, patch_workload):
    """Reconciling with the pinned version already installed does not reinstall."""
    patch_workload.installed_version = osquery.PACKAGE_VERSION
    state = testing.State()

    out = ctx.run(ctx.on.update_status(), state)

    assert patch_workload.install_count == 0
    assert out.unit_status == testing.ActiveStatus()


def test_reconcile_reinstalls_on_version_mismatch(ctx, patch_workload):
    """A stale installed version is upgraded to the pinned version."""
    patch_workload.installed_version = "0.0.0old~noble1"
    state = testing.State()

    out = ctx.run(ctx.on.upgrade_charm(), state)

    assert patch_workload.install_count == 1
    assert patch_workload.installed_version == osquery.PACKAGE_VERSION
    assert out.unit_status == testing.ActiveStatus()


def test_stop_uninstalls_workload(ctx, patch_workload):
    """Stopping the unit uninstalls the workload."""
    patch_workload.installed_version = osquery.PACKAGE_VERSION
    state = testing.State()

    ctx.run(ctx.on.stop(), state)

    assert patch_workload.uninstalled is True
