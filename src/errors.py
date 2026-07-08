# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Business exceptions for the OSQuery charm."""


class OSQueryInstallError(Exception):
    """Raised when installing or removing the OSQuery package fails."""
