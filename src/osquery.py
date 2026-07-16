# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Workload management for the OSQuery agent.

This module contains the logic that interacts with the host system to install
and remove OSQuery. It is intentionally free of any Ops/Juju imports so that it
can be unit tested in isolation and reasoned about independently from the charm
lifecycle.
"""

import logging
import subprocess  # nosec B404

from charmlibs import apt, systemd

from errors import OSQueryInstallError

logger = logging.getLogger(__name__)

# Launchpad-hosted PPA that distributes the custom OSQuery fork (based on
# 5.21.0) with eBPF support.
PPA = "ppa:jjimenezgarcia/osquery"
PACKAGE_NAME = "osquery"
SERVICE_NAME = "osqueryd"


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
