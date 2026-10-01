# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the osquery workload module."""

import os
import stat

import pytest

import osquery
from errors import OSQueryConfigError, OSQueryInstallError


def _api_error(cls):
    """Build a charmlibs.snap API error of type ``cls`` for a test."""
    return cls("boom", kind="test", value=None)


def test_install_ensures_classic_snap_on_channel(monkeypatch):
    calls = []

    def fake_ensure(name, channel, *, classic, update):
        calls.append((name, channel, classic, update))
        return True

    monkeypatch.setattr(osquery.snap, "ensure_installed", fake_ensure)

    assert osquery.install("latest/edge") is True
    # Classic confinement is required, and the store is not polled for updates
    # on every reconcile: snapd refreshes the revision on its own.
    assert calls == [(osquery.SNAP_NAME, "latest/edge", True, False)]


def test_install_reports_no_change(monkeypatch):
    monkeypatch.setattr(osquery.snap, "ensure_installed", lambda *_a, **_k: None)

    assert osquery.install("latest/edge") is False


def test_install_unavailable_channel_raises_config_error(monkeypatch):
    def fail(*_args, **_kwargs):
        raise _api_error(osquery.snap.ChannelNotAvailableError)

    monkeypatch.setattr(osquery.snap, "ensure_installed", fail)

    with pytest.raises(OSQueryConfigError, match="nope/stable"):
        osquery.install("nope/stable")


def test_install_failure_raises(monkeypatch):
    def fail(*_args, **_kwargs):
        raise _api_error(osquery.snap.ChangeError)

    monkeypatch.setattr(osquery.snap, "ensure_installed", fail)

    with pytest.raises(OSQueryInstallError):
        osquery.install("latest/edge")


def test_install_snapd_unreachable_raises(monkeypatch):
    def fail(*_args, **_kwargs):
        raise osquery.snap.SocketNotFoundError("no snapd")

    monkeypatch.setattr(osquery.snap, "ensure_installed", fail)

    with pytest.raises(OSQueryInstallError):
        osquery.install("latest/edge")


def test_is_installed_true(monkeypatch):
    monkeypatch.setattr(osquery.snap, "list_one", lambda name: object())
    assert osquery.is_installed() is True


def test_is_installed_false(monkeypatch):
    def raise_not_installed(name):
        raise _api_error(osquery.snap.NotInstalledError)

    monkeypatch.setattr(osquery.snap, "list_one", raise_not_installed)
    assert osquery.is_installed() is False


def test_is_installed_snapd_error_raises(monkeypatch):
    def fail(name):
        raise osquery.snap.ConnectionError("snapd restarting")

    monkeypatch.setattr(osquery.snap, "list_one", fail)

    with pytest.raises(OSQueryInstallError):
        osquery.is_installed()


def test_is_running_checks_snap_systemd_unit(monkeypatch):
    seen = []

    def fake_running(name):
        seen.append(name)
        return True

    monkeypatch.setattr(osquery.systemd, "service_running", fake_running)

    assert osquery.is_running() is True
    assert seen == ["snap.c-osquery.osqueryd"]


def test_uninstall_purges_snap(monkeypatch):
    calls = []
    monkeypatch.setattr(osquery.snap, "remove", lambda name, *, purge: calls.append((name, purge)))

    osquery.uninstall()

    # Purged so no snapshot of the secrets under $SNAP_COMMON is kept.
    assert calls == [(osquery.SNAP_NAME, True)]


def test_uninstall_failure_raises(monkeypatch):
    def fail(name, *, purge):
        raise _api_error(osquery.snap.ChangeError)

    monkeypatch.setattr(osquery.snap, "remove", fail)

    with pytest.raises(OSQueryInstallError):
        osquery.uninstall()


def test_config_paths_live_under_snap_common():
    """Every managed file lives where the snap's daemon wrapper reads it."""
    for path in (
        osquery.FLAGFILE_PATH,
        osquery.ENROLL_SECRET_PATH,
        osquery.SERVER_CERTS_PATH,
        osquery.CLIENT_CERT_PATH,
        osquery.CLIENT_KEY_PATH,
    ):
        assert path.startswith("/var/snap/c-osquery/common/etc/osquery/")
    assert osquery.FLAGFILE_PATH == "/var/snap/c-osquery/common/etc/osquery/osquery.flags"


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


def test_write_file_overwrites_existing_content(monkeypatch, tmp_path, as_current_user):
    path = tmp_path / "osquery.flags"
    monkeypatch.setattr(osquery, "FLAGFILE_PATH", str(path))

    osquery.write_flagfile("first\n")
    osquery.write_flagfile("second\n")

    assert path.read_text() == "second\n"


def test_write_secret_file_permissions_set_before_content(monkeypatch, tmp_path, as_current_user):
    """Permissions must be tightened to 0o600 before any content is written."""
    path = tmp_path / "secrets" / "enroll.secret"
    records = []
    real_fchmod = os.fchmod

    def spy_fchmod(fd, mode):
        # Capture the file size at the moment permissions are applied.
        records.append((mode, os.fstat(fd).st_size))
        return real_fchmod(fd, mode)

    monkeypatch.setattr(osquery.os, "fchmod", spy_fchmod)

    osquery.write_secret_file(str(path), "topsecret")

    # The mode was set to 0o600 while the file was still empty (size 0).
    assert (0o600, 0) in records
    assert path.read_text() == "topsecret"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_write_file_reports_change(monkeypatch, tmp_path, as_current_user):
    path = tmp_path / "osquery.flags"
    monkeypatch.setattr(osquery, "FLAGFILE_PATH", str(path))

    # First write creates the file: reported as changed.
    assert osquery.write_flagfile("first\n") is True
    # Identical content: no change, so the write is skipped.
    assert osquery.write_flagfile("first\n") is False
    # Different content: reported as changed again.
    assert osquery.write_flagfile("second\n") is True


def test_write_file_skips_write_when_unchanged(monkeypatch, tmp_path, as_current_user):
    path = tmp_path / "osquery.flags"
    monkeypatch.setattr(osquery, "FLAGFILE_PATH", str(path))
    osquery.write_flagfile("same\n")

    def fail(*_args, **_kwargs):
        raise AssertionError("the file should not be reopened when content is unchanged")

    monkeypatch.setattr(osquery.os, "open", fail)

    assert osquery.write_flagfile("same\n") is False


def test_write_file_repairs_permission_drift_without_rewrite(
    monkeypatch, tmp_path, as_current_user
):
    """Unchanged content still re-enforces file and directory permissions."""
    path = tmp_path / "secrets" / "enroll.secret"
    osquery.write_secret_file(str(path), "topsecret")

    # Simulate drift: someone loosens the secret and its directory.
    os.chmod(path, 0o644)  # nosec B103 - deliberately loosened to test drift repair
    os.chmod(path.parent, 0o755)  # nosec B103 - deliberately loosened to test drift repair

    def fail(*_args, **_kwargs):
        raise AssertionError("the file should not be reopened when content is unchanged")

    monkeypatch.setattr(osquery.os, "open", fail)

    changed = osquery.write_secret_file(str(path), "topsecret")

    assert changed is False
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700


def test_write_file_error_raises_config_error(monkeypatch, tmp_path, as_current_user):
    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(osquery.os, "chmod", boom)

    with pytest.raises(OSQueryConfigError):
        osquery.write_secret_file(str(tmp_path / "x"), "value")


def test_write_file_write_failure_raises_config_error(monkeypatch, tmp_path, as_current_user):
    """A failure while applying permissions during the write raises cleanly."""
    path = tmp_path / "secrets" / "enroll.secret"

    def boom(*_args, **_kwargs):
        raise OSError("no space left")

    monkeypatch.setattr(osquery.os, "fchmod", boom)

    with pytest.raises(OSQueryConfigError):
        osquery.write_secret_file(str(path), "value")


def test_restart_enables_and_restarts(monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(
        osquery.snap,
        "start",
        lambda name, services, *, enable: calls.append(("start", name, services, enable)),
    )
    monkeypatch.setattr(
        osquery.snap,
        "restart",
        lambda name, services: calls.append(("restart", name, services)),
    )

    osquery.restart()

    assert calls == [
        ("start", osquery.SNAP_NAME, osquery.SERVICE_NAME, True),
        ("restart", osquery.SNAP_NAME, osquery.SERVICE_NAME),
    ]


def test_restart_failure_raises(monkeypatch):
    monkeypatch.setattr(osquery.snap, "start", lambda *_a, **_k: None)

    def fail(*_args, **_kwargs):
        raise _api_error(osquery.snap.ChangeError)

    monkeypatch.setattr(osquery.snap, "restart", fail)

    with pytest.raises(OSQueryInstallError):
        osquery.restart()
