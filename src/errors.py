# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Business exceptions for the OSQuery charm."""


class OSQueryError(Exception):
    """Base class for all user-defined OSQuery charm errors."""


class OSQueryInstallError(OSQueryError):
    """Raised when installing or removing the OSQuery package fails."""
