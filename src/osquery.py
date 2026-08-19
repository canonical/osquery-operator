# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Workload management for the OSQuery agent.

This module contains the logic that interacts with the host system to install
and remove OSQuery. It is intentionally free of any Ops/Juju imports so that it
can be unit tested in isolation and reasoned about independently from the charm
lifecycle.
"""

import logging
import os
import subprocess  # nosec B404
from pathlib import Path

from charmlibs import apt, systemd

from errors import OSQueryConfigError, OSQueryInstallError

logger = logging.getLogger(__name__)

# Launchpad-hosted PPA that distributes the custom OSQuery fork (based on
# 5.21.0) with eBPF support.
PPA = "ppa:jjimenezgarcia/osquery"
PACKAGE_NAME = "osquery"
SERVICE_NAME = "osqueryd"

# OSQuery reads its command-line flags from this flagfile on startup. The deb
# package ships a systemd unit whose environment file points ``FLAG_FILE`` here,
# so writing the charm-generated flags to this path makes the daemon pick them
# up on the next restart.
CONFIG_DIR = "/etc/osquery"
CERTS_DIR = "/etc/osquery/certs"
FLAGFILE_PATH = "/etc/osquery/osquery.flags"
# File-backed configuration options are materialised at these paths and then
# referenced from the flagfile.
ENROLL_SECRET_PATH = "/etc/osquery/enroll.secret"  # nosec B105 - path, not a secret value
SERVER_CERTS_PATH = "/etc/osquery/certs/server-ca.pem"
CLIENT_CERT_PATH = "/etc/osquery/certs/client-ca.pem"
CLIENT_KEY_PATH = "/etc/osquery/certs/client-key.pem"

# Ownership applied to every file and directory the charm manages under
# ``/etc/osquery``. Hooks run as root on the host, so these resolve to the
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


def install() -> None:
    """Install the latest OSQuery package from the Launchpad PPA.

    Steps:
    - Add the Launchpad PPA (which also imports its signing key).
    - Refresh the apt cache and install the latest OSQuery version.

    This function is idempotent: adding an already-present PPA and installing an
    already-present package are both no-ops.

    Raises:
        OSQueryInstallError: if adding the repository or installing the package
            fails.
    """
    try:
        logger.info("Adding OSQuery PPA %s", PPA)
        # add-apt-repository transparently resolves the PPA URL and imports the
        # Launchpad signing key, which the apt library cannot do on its own.
        subprocess.run(  # nosec B603
            ["/usr/bin/add-apt-repository", "--yes", PPA],
            check=True,
            capture_output=True,
        )
        logger.info("Installing %s package", PACKAGE_NAME)
        apt.add_package(PACKAGE_NAME, update_cache=True)
    except (subprocess.CalledProcessError, apt.Error) as exc:
        raise OSQueryInstallError(f"failed to install {PACKAGE_NAME}: {exc}") from exc


def uninstall() -> None:
    """Stop the service and remove the OSQuery package from the system.

    Raises:
        OSQueryInstallError: if removing the package fails.
    """
    stop()
    try:
        logger.info("Removing %s package", PACKAGE_NAME)
        apt.remove_package(PACKAGE_NAME)
    except apt.Error as exc:
        raise OSQueryInstallError(f"failed to remove {PACKAGE_NAME}: {exc}") from exc


def is_installed() -> bool:
    """Return whether the OSQuery package is installed (at any version)."""
    try:
        apt.DebianPackage.from_installed_package(PACKAGE_NAME)
        return True
    except apt.PackageNotFoundError:
        return False


def stop() -> None:
    """Stop the OSQuery daemon if it is running.

    Raises:
        OSQueryInstallError: if the service fails to stop.
    """
    try:
        if is_installed() and systemd.service_running(SERVICE_NAME):
            systemd.service_stop(SERVICE_NAME)
    except systemd.SystemdError as exc:
        raise OSQueryInstallError(f"failed to stop {SERVICE_NAME}: {exc}") from exc


def is_running() -> bool:
    """Return whether the OSQuery daemon is currently running."""
    return systemd.service_running(SERVICE_NAME)


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
        OSQueryConfigError: if the file or directory cannot be written.
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
        raise OSQueryConfigError(f"failed to write {path}: {exc}") from exc


def write_flagfile(content: str) -> bool:
    """Write the generated OSQuery flagfile to disk.

    Returns:
        ``True`` if the flagfile content changed, ``False`` if it already matched.

    Raises:
        OSQueryConfigError: if the flagfile cannot be written.
    """
    logger.info("Writing OSQuery flagfile to %s", FLAGFILE_PATH)
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
        OSQueryConfigError: if the file cannot be written.
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
        OSQueryConfigError: if the file cannot be written.
    """
    logger.info("Writing file %s", path)
    return _write_file(path, content, file_mode=PUBLIC_FILE_MODE, dir_mode=SECURE_DIR_MODE)


def restart() -> None:
    """Enable and (re)start the OSQuery daemon so it reloads its flagfile.

    OSQuery reads the flagfile only at start-up, so the service must be bounced
    for configuration changes to take effect. The service is also enabled so it
    survives reboots.

    Raises:
        OSQueryInstallError: if the service fails to start.
    """
    try:
        logger.info("Enabling and restarting %s", SERVICE_NAME)
        systemd.service_enable(SERVICE_NAME)
        systemd.service_restart(SERVICE_NAME)
    except systemd.SystemdError as exc:
        raise OSQueryInstallError(f"failed to restart {SERVICE_NAME}: {exc}") from exc
