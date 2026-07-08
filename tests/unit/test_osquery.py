# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the osquery workload module."""

import subprocess  # nosec B404

import pytest

import osquery
from errors import OSQueryInstallError


def test_install_success(monkeypatch):
    calls = {}

    def fake_run(cmd, check, capture_output):
        calls["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    def fake_add_package(name, version):
        calls["package"] = name
        calls["version"] = version

    monkeypatch.setattr(osquery.subprocess, "run", fake_run)
    monkeypatch.setattr(osquery.apt, "update", lambda: calls.setdefault("update", True))
    monkeypatch.setattr(osquery.apt, "add_package", fake_add_package)

    osquery.install()

    assert osquery.PPA in calls["cmd"]
    assert calls["update"] is True
    assert calls["package"] == osquery.PACKAGE_NAME
    assert calls["version"] == osquery.PACKAGE_VERSION


def test_install_failure_raises(monkeypatch):
    def fake_run(cmd, check, capture_output):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(osquery.subprocess, "run", fake_run)

    with pytest.raises(OSQueryInstallError):
        osquery.install()


def test_is_installed_true(monkeypatch):
    class FakePackage:
        present = True

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
        osquery.apt, "remove_package", lambda name: removed.setdefault("package", name)
    )

    osquery.uninstall()

    assert removed["stopped"] is True
    assert removed["package"] == osquery.PACKAGE_NAME


def test_uninstall_failure_raises(monkeypatch):
    monkeypatch.setattr(osquery, "stop", lambda: None)

    def fail(name):
        raise osquery.apt.PackageError("boom")

    monkeypatch.setattr(osquery.apt, "remove_package", fail)

    with pytest.raises(OSQueryInstallError):
        osquery.uninstall()
