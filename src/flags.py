# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Translation of charm configuration into an OSQuery flagfile.

This module is intentionally free of any Ops/Juju imports. It takes a plain
mapping of resolved configuration values (secrets already resolved to their
plaintext by the charm) and produces the ``--flag=value`` lines that make up the
OSQuery flagfile, plus the metadata the charm needs to materialise file-backed
options on disk.

The mapping is derived directly from the charm specification. There are three
kinds of configuration options:

* *Custom* options whose value is expanded into one or more flags
  (``controller-uri`` and ``controller-env-uuid``).
* *File-backed* options whose value is written to a file on disk; the flag then
  points at that file (the enrollment secret and the TLS certificate/key).
* *One-to-one* options that map to a single flag with the same name, replacing
  dashes with underscores (for example ``carver-block-size`` ->
  ``--carver_block_size``).
"""

from collections import OrderedDict
from collections.abc import Mapping
from typing import Any

import osquery

# --- Custom-mapping option names ---------------------------------------------
CONTROLLER_URI = "controller-uri"
CONTROLLER_ENV_UUID = "controller-env-uuid"

# --- File-backed option names ------------------------------------------------
ENROLL_SECRET = "enroll-secret"  # nosec B105 - option name, not a secret value
TLS_SERVER_CERTS = "tls-server-certs"
TLS_CLIENT_CERT = "tls-client-cert"
TLS_CLIENT_KEY = "tls-client-key"

# Options the charm must have set before it can build a working flagfile.
REQUIRED_CONFIGS = (CONTROLLER_URI, CONTROLLER_ENV_UUID)

# File-backed options and the on-disk path each one is written to. The flagfile
# references these paths rather than the raw values.
FILE_CONFIGS: "OrderedDict[str, str]" = OrderedDict(
    (
        (ENROLL_SECRET, osquery.ENROLL_SECRET_PATH),
        (TLS_SERVER_CERTS, osquery.SERVER_CERTS_PATH),
        (TLS_CLIENT_CERT, osquery.CLIENT_CERT_PATH),
        (TLS_CLIENT_KEY, osquery.CLIENT_KEY_PATH),
    )
)

# File-backed options whose value is sensitive and must be written with 600
# permissions. The remaining file-backed options are public certificates.
SECRET_CONFIGS = (ENROLL_SECRET, TLS_CLIENT_KEY)

# The flags each file-backed option controls, in the same order as ``FILE_CONFIGS``.
FILE_CONFIG_FLAGS = {
    ENROLL_SECRET: "enroll_secret_path",
    TLS_SERVER_CERTS: "tls_server_certs",
    TLS_CLIENT_CERT: "tls_client_cert",
    TLS_CLIENT_KEY: "tls_client_key",
}

# Options that map one-to-one to a flag of the same name (dashes become
# underscores). Listed in specification order for readability.
ONE_TO_ONE_CONFIGS = (
    "alarm-timeout",
    "carver-block-size",
    "carver-compression",
    "carver-disable-function",
    "config-accelerated-refresh",
    "config-check",
    "config-dump",
    "config-plugin",
    "config-enable-backup",
    "config-refresh",
    "config-tls-max-attempts",
    "database-dump",
    "disable-carver",
    "disable-distributed",
    "disable-enrollment",
    "disable-reenrollment",
    "disable-watchdog",
    "distributed-interval",
    "distributed-plugin",
    "distributed-tls-max-attempts",
    "enable-signal-handler",
    "enroll-always",
    "force",
    "host-identifier",
    "logger-plugin",
    "logger-stderr",
    "logger-tls-compress",
    "logger-tls-period",
    "tls-enroll-max-attempts",
    "tls-session-reuse",
    "tls-session-timeout",
    "watchdog-delay",
    "watchdog-level",
    "watchdog-memory-limit",
    "watchdog-utilization-limit",
)

# Every non-secret option the charm reads directly from ``self.config``. Secret
# options (``SECRET_CONFIGS``) are resolved separately by the charm because they
# require a Juju secret lookup.
PLAIN_CONFIGS = (
    CONTROLLER_URI,
    CONTROLLER_ENV_UUID,
    TLS_SERVER_CERTS,
    TLS_CLIENT_CERT,
    *ONE_TO_ONE_CONFIGS,
)


def missing_required(values: Mapping[str, Any]) -> list[str]:
    """Return the names of required options that are unset or empty.

    Args:
        values: mapping of option name to its resolved value.

    Returns:
        The list of required option names whose value is missing, in
        specification order.
    """
    return [name for name in REQUIRED_CONFIGS if not values.get(name)]


def _render(value: Any) -> str:
    """Render a configuration value the way OSQuery expects it in a flagfile."""
    if isinstance(value, bool):
        # gflags expects lower-case boolean literals.
        return "true" if value else "false"
    return str(value)


def build_flags(values: Mapping[str, Any], proxy_hostname: str) -> "OrderedDict[str, str]":
    """Build the ordered mapping of OSQuery flags from resolved config values.

    The required options are assumed to be present; call :func:`missing_required`
    first. Options that are unset (``None``) are omitted so OSQuery falls back to
    its own defaults.

    Args:
        values: mapping of option name to its resolved value.
        proxy_hostname: value of ``JUJU_CHARM_HTTPS_PROXY``; the ``proxy_hostname``
            flag is only emitted when this is non-empty.

    Returns:
        An ordered mapping of flag name to rendered string value.
    """
    flags: OrderedDict[str, str] = OrderedDict()

    # controller-uri expands to the TLS hostname (always on port 443).
    flags["tls_hostname"] = f"{values[CONTROLLER_URI]}:443"

    # controller-env-uuid expands to every per-environment TLS endpoint.
    uuid = values[CONTROLLER_ENV_UUID]
    flags["enroll_tls_endpoint"] = f"/{uuid}/enroll"
    flags["config_tls_endpoint"] = f"/{uuid}/config"
    flags["logger_tls_endpoint"] = f"/{uuid}/log"
    flags["distributed_tls_read_endpoint"] = f"/{uuid}/read"
    flags["distributed_tls_write_endpoint"] = f"/{uuid}/write"
    flags["carver_start_endpoint"] = f"/{uuid}/init"
    flags["carver_continue_endpoint"] = f"/{uuid}/block"

    # File-backed options: the flag points at the materialised file.
    for name, flag in FILE_CONFIG_FLAGS.items():
        if values.get(name) is not None:
            flags[flag] = FILE_CONFIGS[name]

    # One-to-one options mapped to a flag of the same name.
    for name in ONE_TO_ONE_CONFIGS:
        value = values.get(name)
        if value is None:
            continue
        flags[name.replace("-", "_")] = _render(value)

    # Hardcoded flag: route OSQuery's outbound traffic through the Juju proxy
    # when one is configured for the model.
    if proxy_hostname:
        flags["proxy_hostname"] = proxy_hostname

    return flags


def render_flagfile(flags: Mapping[str, str]) -> str:
    """Render a flag mapping into flagfile text (one ``--flag=value`` per line)."""
    return "".join(f"--{name}={value}\n" for name, value in flags.items())
