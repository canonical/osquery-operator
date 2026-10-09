# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Business exceptions for the osquery charm."""


class OsqueryError(Exception):
    """Base class for all user-defined osquery charm errors."""


class OsqueryInstallError(OsqueryError):
    """Raised when installing, removing or (re)starting osquery fails."""


class OsqueryConfigError(OsqueryError):
    """Raised when the charm configuration is invalid or cannot be applied.

    This covers both user-facing validation problems (for example a required
    option is unset or a referenced secret is missing) and failures while
    writing the generated flagfile or the secret/certificate files to disk.
    """
