# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the OSQuery charm lifecycle."""

import pytest
from ops import testing

from charm import OSQueryCharm
from errors import OSQueryInstallError


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

    assert patch_workload.installed is True
    assert patch_workload.install_count == 1
    assert out.unit_status == testing.ActiveStatus()


def test_reconcile_is_idempotent_when_already_installed(ctx, patch_workload):
    """Reconciling with OSQuery already installed does not reinstall."""
    patch_workload.installed = True
    state = testing.State()

    out = ctx.run(ctx.on.update_status(), state)

    assert patch_workload.install_count == 0
    assert out.unit_status == testing.ActiveStatus()


def test_stop_uninstalls_workload(ctx, patch_workload):
    """Stopping the unit uninstalls the workload."""
    patch_workload.installed = True
    state = testing.State()

    ctx.run(ctx.on.stop(), state)

    assert patch_workload.uninstalled is True


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
def test_reconcile_failure_sets_blocked_status(ctx, monkeypatch, event):
    """A custom workload error is converted to blocked status during reconcile."""

    monkeypatch.setattr("osquery.is_installed", lambda: False)

    def fail_install():
        raise OSQueryInstallError("install failed")

    monkeypatch.setattr("osquery.install", fail_install)
    state = testing.State()

    out = ctx.run(getattr(ctx.on, event)(), state)

    assert out.unit_status == testing.BlockedStatus("install failed")


def test_stop_failure_sets_blocked_status(ctx, monkeypatch):
    """A custom workload error is converted to blocked status during stop."""

    def fail_uninstall():
        raise OSQueryInstallError("remove failed")

    monkeypatch.setattr("osquery.uninstall", fail_uninstall)
    state = testing.State()

    out = ctx.run(ctx.on.stop(), state)

    assert out.unit_status == testing.BlockedStatus("remove failed")
