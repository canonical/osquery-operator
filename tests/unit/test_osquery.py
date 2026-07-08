# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the osquery workload module."""

import subprocess  # nosec B404

import pytest

import osquery
from errors import OSQueryInstallError


def test_install_success(monkeypatch):
    commands = []

    def fake_run(cmd, check, capture_output):
        commands.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(osquery.subprocess, "run", fake_run)

    osquery.install()

    # The PPA is added, the cache refreshed and the pinned version installed.
    assert any(osquery.PPA in cmd for cmd in commands)
    install_cmd = commands[-1]
    assert "install" in install_cmd
    assert "--allow-downgrades" in install_cmd
    assert f"{osquery.PACKAGE_NAME}={osquery.PACKAGE_VERSION}" in install_cmd


def test_install_failure_raises(monkeypatch):
    def fake_run(cmd, check, capture_output):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(osquery.subprocess, "run", fake_run)

    with pytest.raises(OSQueryInstallError):
        osquery.install()


def test_installed_version_returns_version(monkeypatch):
    class FakePackage:
        version = "5.21.0custom19~noble1"

    monkeypatch.setattr(
        osquery.apt.DebianPackage, "from_installed_package", lambda name: FakePackage()
    )
    assert osquery.installed_version() == "5.21.0custom19~noble1"


def test_installed_version_returns_none_when_absent(monkeypatch):
    def raise_not_found(name):
        raise osquery.apt.PackageNotFoundError()

    monkeypatch.setattr(osquery.apt.DebianPackage, "from_installed_package", raise_not_found)
    assert osquery.installed_version() is None


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

    def fake_run(cmd, check, capture_output):
        removed["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(osquery.subprocess, "run", fake_run)

    osquery.uninstall()

    assert removed["stopped"] is True
    assert "remove" in removed["cmd"]
    assert osquery.PACKAGE_NAME in removed["cmd"]


def test_uninstall_failure_raises(monkeypatch):
    monkeypatch.setattr(osquery, "stop", lambda: None)

    def fail(cmd, check, capture_output):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(osquery.subprocess, "run", fail)

    with pytest.raises(OSQueryInstallError):
        osquery.uninstall()
