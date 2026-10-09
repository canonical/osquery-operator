# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Workload management for the osquery agent.

This module contains the logic that interacts with the host system to install
and remove osquery. It is intentionally free of any Ops/Juju imports so that it
can be unit tested in isolation and reasoned about independently from the charm
lifecycle.
"""

import logging
import os
from pathlib import Path

from charmlibs import snap, systemd

from errors import OsqueryConfigError, OsqueryInstallError

logger = logging.getLogger(__name__)

# Canonical SecOps osquery fork (5.21.0, eBPF). Classic confinement: eBPF
# needs privileges no strict-confinement interface grants.
SNAP_NAME = "c-osquery"
# The snap's daemon app and its systemd unit.
SERVICE_NAME = "osqueryd"
SYSTEMD_UNIT = f"snap.{SNAP_NAME}.{SERVICE_NAME}"

# The snap's daemon reads its flagfile from $SNAP_COMMON/etc/osquery, which
# survives snap refreshes.
SNAP_COMMON = f"/var/snap/{SNAP_NAME}/common"
CONFIG_DIR = f"{SNAP_COMMON}/etc/osquery"
CERTS_DIR = f"{CONFIG_DIR}/certs"
FLAGFILE_PATH = f"{CONFIG_DIR}/osquery.flags"
# File-backed configuration options are materialised at these paths and then
# referenced from the flagfile.
ENROLL_SECRET_PATH = f"{CONFIG_DIR}/enroll.secret"  # nosec B105 - path, not a secret value
SERVER_CERTS_PATH = f"{CERTS_DIR}/server-ca.pem"
CLIENT_CERT_PATH = f"{CERTS_DIR}/client-ca.pem"
CLIENT_KEY_PATH = f"{CERTS_DIR}/client-key.pem"

# Ownership applied to every file and directory the charm manages under
# ``CONFIG_DIR``. Hooks run as root on the host, so these resolve to the
# ``root`` user and group. They are module-level so unit tests (which do not run
# as root) can override them to the test user before exercising the writers.
FILE_OWNER_UID = 0
FILE_OWNER_GID = 0

# Permission bits. Secret material is only readable by its owner (root) and its
# parent directory is not traversable by anyone else, as mandated by the spec.
SECRET_FILE_MODE = 0o600
PUBLIC_FILE_MODE = 0o644
FLAGFILE_MODE = 0o640
SECURE_DIR_MODE = 0o700


def install(channel: str) -> bool:
    """Ensure the osquery snap is installed and tracking ``channel``.

    Installs the snap (with classic confinement) when it is absent, and
    refreshes it onto ``channel`` when it currently tracks a different one. When
    the snap already tracks ``channel`` nothing is done: the store is not
    queried, and snapd's own automatic refreshes keep the revision current.

    This function is idempotent and cheap to call on every reconcile.

    Args:
        channel: the Snap Store channel to track, for example ``latest/edge``.

    Returns:
        ``True`` if the snap was installed or refreshed, ``False`` otherwise.

    Raises:
        OsqueryConfigError: if ``channel`` does not exist for the snap.
        OsqueryInstallError: if installing or refreshing the snap fails.
    """
    try:
        logger.info("Ensuring %s snap is installed from %s", SNAP_NAME, channel)
        return bool(snap.ensure_installed(SNAP_NAME, channel, classic=True, update=False))
    except snap.ChannelNotAvailableError as exc:
        raise OsqueryConfigError(
            f"snap channel '{channel}' is not available for {SNAP_NAME}"
        ) from exc
    except snap.Error as exc:
        raise OsqueryInstallError(f"failed to install {SNAP_NAME}: {exc}") from exc


def uninstall() -> None:
    """Remove the osquery snap from the system.

    snapd stops the daemon before removing the snap. The removal purges the
    snap's data instead of saving an automatic snapshot, because
    ``$SNAP_COMMON`` holds the enrollment secret and the TLS client key, which
    must not outlive the unit.

    Raises:
        OsqueryInstallError: if removing the snap fails.
    """
    try:
        logger.info("Removing %s snap", SNAP_NAME)
        snap.remove(SNAP_NAME, purge=True)
    except snap.Error as exc:
        raise OsqueryInstallError(f"failed to remove {SNAP_NAME}: {exc}") from exc


def is_installed() -> bool:
    """Return whether the osquery snap is installed (on any channel).

    Raises:
        OsqueryInstallError: if snapd cannot be queried.
    """
    try:
        snap.list_one(SNAP_NAME)
        return True
    except snap.NotInstalledError:
        return False
    except snap.Error as exc:
        raise OsqueryInstallError(f"failed to query {SNAP_NAME}: {exc}") from exc


def is_running() -> bool:
    """Return whether the osquery daemon is currently running."""
    return systemd.service_running(SYSTEMD_UNIT)


def _write_file(path: str, content: str, *, file_mode: int, dir_mode: int) -> bool:
    """Write ``content`` to ``path`` with strict ownership and permissions.

    The parent directory is created if missing and its ownership and permissions
    are re-applied on every call so drift is corrected even when the file content
    is unchanged. The file is opened (creating it if necessary) and its ownership
    and permissions are set before any content is written, so sensitive data is
    never briefly readable through a loosely-permissioned file. If the file
    already holds exactly ``content`` the write is skipped, but its ownership and
    permissions are still re-enforced.

    Args:
        path: absolute path of the file to write.
        content: text content to write.
        file_mode: permission bits to apply to the file.
        dir_mode: permission bits to apply to the parent directory.

    Returns:
        ``True`` if the file content changed, ``False`` if it already matched.

    Raises:
        OsqueryConfigError: if the file or directory cannot be written.
    """
    target = Path(path)
    parent = target.parent
    try:
        # Always enforce the parent directory's ownership and permissions so
        # drift (for example a loosened mode) is corrected on every reconcile.
        parent.mkdir(parents=True, exist_ok=True)
        os.chown(parent, FILE_OWNER_UID, FILE_OWNER_GID)
        os.chmod(parent, dir_mode)

        if target.exists() and target.read_text(encoding="utf-8") == content:
            # Content is unchanged: still re-enforce ownership and permissions.
            os.chown(target, FILE_OWNER_UID, FILE_OWNER_GID)
            os.chmod(target, file_mode)
            return False

        # Open (truncating any existing file), then set ownership and permissions
        # before writing any content so secret material is never exposed through
        # a loosely-permissioned file.
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, file_mode)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            os.fchown(fd, FILE_OWNER_UID, FILE_OWNER_GID)
            os.fchmod(fd, file_mode)
            handle.write(content)
        return True
    except OSError as exc:
        raise OsqueryConfigError(f"failed to write {path}: {exc}") from exc


def write_flagfile(content: str) -> bool:
    """Write the generated osquery flagfile to disk.

    Returns:
        ``True`` if the flagfile content changed, ``False`` if it already matched.

    Raises:
        OsqueryConfigError: if the flagfile cannot be written.
    """
    logger.info("Writing osquery flagfile to %s", FLAGFILE_PATH)
    return _write_file(FLAGFILE_PATH, content, file_mode=FLAGFILE_MODE, dir_mode=SECURE_DIR_MODE)


def write_secret_file(path: str, content: str) -> bool:
    """Write secret material with owner-only (600) permissions.

    The parent directory is locked down to 700 so the secret is not readable by
    other users on the host.

    Args:
        path: absolute path of the secret file.
        content: the secret value to write.

    Returns:
        ``True`` if the file content changed, ``False`` if it already matched.

    Raises:
        OsqueryConfigError: if the file cannot be written.
    """
    logger.info("Writing secret file %s", path)
    return _write_file(path, content, file_mode=SECRET_FILE_MODE, dir_mode=SECURE_DIR_MODE)


def write_public_file(path: str, content: str) -> bool:
    """Write non-secret material (such as a CA certificate) to disk.

    The file itself is world-readable (644) but it still lives inside a 700
    directory owned by root, matching the layout the secret files require.

    Args:
        path: absolute path of the file.
        content: the value to write.

    Returns:
        ``True`` if the file content changed, ``False`` if it already matched.

    Raises:
        OsqueryConfigError: if the file cannot be written.
    """
    logger.info("Writing file %s", path)
    return _write_file(path, content, file_mode=PUBLIC_FILE_MODE, dir_mode=SECURE_DIR_MODE)


def restart() -> None:
    """Enable and (re)start the osquery daemon so it reloads its flagfile.

    Osquery reads the flagfile only at start-up, so the service must be bounced
    for configuration changes to take effect. The service is also enabled so it
    survives reboots.

    Raises:
        OsqueryInstallError: if the service fails to start.
    """
    try:
        logger.info("Enabling and restarting %s.%s", SNAP_NAME, SERVICE_NAME)
        snap.start(SNAP_NAME, SERVICE_NAME, enable=True)
        snap.restart(SNAP_NAME, SERVICE_NAME)
    except snap.Error as exc:
        raise OsqueryInstallError(f"failed to restart {SNAP_NAME}.{SERVICE_NAME}: {exc}") from exc
