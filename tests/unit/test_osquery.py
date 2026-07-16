# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the osquery workload module."""

import subprocess  # nosec B404

import pytest

import osquery
from errors import OSQueryInstallError


def test_install_success(monkeypatch):
    commands = []
    added = []

    def fake_run(cmd, check, capture_output):
        commands.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(osquery.subprocess, "run", fake_run)
    monkeypatch.setattr(
        osquery.apt, "add_package", lambda name, update_cache: added.append((name, update_cache))
    )

    osquery.install()

    # The PPA is added and the latest package is installed via the apt library.
    assert any(osquery.PPA in cmd for cmd in commands)
    assert added == [(osquery.PACKAGE_NAME, True)]


def test_install_failure_raises(monkeypatch):
    def fake_run(cmd, check, capture_output):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(osquery.subprocess, "run", fake_run)

    with pytest.raises(OSQueryInstallError):
        osquery.install()


def test_install_apt_failure_raises(monkeypatch):
    def fake_run(cmd, check, capture_output):
        return subprocess.CompletedProcess(cmd, 0)

    def fail(name, update_cache):
        raise osquery.apt.PackageError("boom")

    monkeypatch.setattr(osquery.subprocess, "run", fake_run)
    monkeypatch.setattr(osquery.apt, "add_package", fail)

    with pytest.raises(OSQueryInstallError):
        osquery.install()


def test_is_installed_true(monkeypatch):
    class FakePackage:
        version = "5.21.0custom19~noble1"

    monkeypatch.setattr(
        osquery.apt.DebianPackage, "from_installed_package", lambda name: FakePackage()
    )
    assert osquery.is_installed() is True


def test_is_installed_false(monkeypatch):
    def raise_not_found(name):
        raise osquery.apt.PackageNotFoundError()

    monkeypatch.setattr(osquery.apt.DebianPackage, "from_installed_package", raise_not_found)
    assert osquery.is_installed() is False


def test_is_running_delegates_to_systemd(monkeypatch):
    monkeypatch.setattr(osquery.systemd, "service_running", lambda name: True)
    assert osquery.is_running() is True


def test_stop_when_running(monkeypatch):
    stopped: dict = {}
    monkeypatch.setattr(osquery, "is_installed", lambda: True)
    monkeypatch.setattr(osquery.systemd, "service_running", lambda name: True)
    monkeypatch.setattr(
        osquery.systemd, "service_stop", lambda name: stopped.setdefault("name", name)
    )

    osquery.stop()

    assert stopped["name"] == osquery.SERVICE_NAME


def test_stop_when_not_installed_is_noop(monkeypatch):
    monkeypatch.setattr(osquery, "is_installed", lambda: False)

    def fail(name):
        raise AssertionError("service_stop should not be called")

    monkeypatch.setattr(osquery.systemd, "service_stop", fail)

    osquery.stop()


def test_uninstall_success(monkeypatch):
    removed: dict = {}
    monkeypatch.setattr(osquery, "stop", lambda: removed.setdefault("stopped", True))
    monkeypatch.setattr(
        osquery.apt, "remove_package", lambda name: removed.setdefault("name", name)
    )

    osquery.uninstall()

    assert removed["stopped"] is True
    assert removed["name"] == osquery.PACKAGE_NAME


def test_uninstall_failure_raises(monkeypatch):
    monkeypatch.setattr(osquery, "stop", lambda: None)

    def fail(name):
        raise osquery.apt.PackageError("boom")

    monkeypatch.setattr(osquery.apt, "remove_package", fail)

    with pytest.raises(OSQueryInstallError):
        osquery.uninstall()
