# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the osquery workload module."""

import os
import stat
import subprocess  # nosec B404

import pytest

import osquery
from errors import OSQueryConfigError, OSQueryInstallError


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


@pytest.fixture(name="as_current_user")
def as_current_user_fixture(monkeypatch):
    """Make the file writers chown to the test user instead of root."""
    monkeypatch.setattr(osquery, "FILE_OWNER_UID", os.getuid())
    monkeypatch.setattr(osquery, "FILE_OWNER_GID", os.getgid())


def test_write_secret_file_permissions(monkeypatch, tmp_path, as_current_user):
    path = tmp_path / "secrets" / "enroll.secret"

    osquery.write_secret_file(str(path), "topsecret")

    assert path.read_text() == "topsecret"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700


def test_write_public_file_permissions(monkeypatch, tmp_path, as_current_user):
    path = tmp_path / "certs" / "server-ca.pem"

    osquery.write_public_file(str(path), "-----BEGIN CERTIFICATE-----")

    assert path.read_text() == "-----BEGIN CERTIFICATE-----"
    assert stat.S_IMODE(path.stat().st_mode) == 0o644
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700


def test_write_flagfile(monkeypatch, tmp_path, as_current_user):
    flagfile = tmp_path / "osquery.flags"
    monkeypatch.setattr(osquery, "FLAGFILE_PATH", str(flagfile))

    osquery.write_flagfile("--tls_hostname=h:443\n")

    assert flagfile.read_text() == "--tls_hostname=h:443\n"
    assert stat.S_IMODE(flagfile.stat().st_mode) == 0o640


def test_write_file_is_atomic_and_overwrites(monkeypatch, tmp_path, as_current_user):
    path = tmp_path / "osquery.flags"
    monkeypatch.setattr(osquery, "FLAGFILE_PATH", str(path))

    osquery.write_flagfile("first\n")
    osquery.write_flagfile("second\n")

    assert path.read_text() == "second\n"
    # No temporary file is left behind after a successful write.
    assert list(tmp_path.glob(".*.tmp")) == []


def test_write_file_error_raises_config_error(monkeypatch, tmp_path, as_current_user):
    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(osquery.os, "chmod", boom)

    with pytest.raises(OSQueryConfigError):
        osquery.write_secret_file(str(tmp_path / "x"), "value")


def test_restart_enables_and_restarts(monkeypatch):
    calls = []
    monkeypatch.setattr(
        osquery.systemd, "service_enable", lambda name: calls.append(("enable", name))
    )
    monkeypatch.setattr(
        osquery.systemd, "service_restart", lambda name: calls.append(("restart", name))
    )

    osquery.restart()

    assert calls == [("enable", osquery.SERVICE_NAME), ("restart", osquery.SERVICE_NAME)]


def test_restart_failure_raises(monkeypatch):
    monkeypatch.setattr(osquery.systemd, "service_enable", lambda name: None)

    def fail(name):
        raise osquery.systemd.SystemdError("boom")

    monkeypatch.setattr(osquery.systemd, "service_restart", fail)

    with pytest.raises(OSQueryInstallError):
        osquery.restart()
