# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Shared fixtures for the OSQuery charm unit tests."""

import pytest

import osquery


@pytest.fixture(name="patch_workload")
def patch_workload_fixture(monkeypatch):
    """Patch all host-level workload side effects.

    The osquery module talks to apt, systemd and the local filesystem. For unit
    tests we replace those side effects with in-memory recorders so the charm
    logic can be exercised without touching the host.

    Yields:
        A recorder object capturing the workload interactions.
    """

    class Recorder:
        def __init__(self):
            self.installed = False
            self.uninstalled = False
            self.install_count = 0

    recorder = Recorder()

    def fake_install():
        recorder.installed = True
        recorder.install_count += 1

    def fake_uninstall():
        recorder.uninstalled = True

    def fake_is_installed():
        return recorder.installed

    monkeypatch.setattr(osquery, "install", fake_install)
    monkeypatch.setattr(osquery, "uninstall", fake_uninstall)
    monkeypatch.setattr(osquery, "is_installed", fake_is_installed)
    yield recorder
