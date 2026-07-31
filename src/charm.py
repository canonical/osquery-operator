#!/usr/bin/env python3
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for the OSQuery endpoint security monitoring agent."""

import logging
import os
from typing import Optional

import ops

import flags
import osquery
from errors import OSQueryConfigError, OSQueryError

logger = logging.getLogger(__name__)

# Environment variable Juju exposes to hooks when an HTTPS proxy is configured
# for the model. OSQuery routes its outbound TLS traffic through it.
HTTPS_PROXY_ENV = "JUJU_CHARM_HTTPS_PROXY"


class OSQueryCharm(ops.CharmBase):
    """Subordinate charm that manages the OSQuery agent on the host."""

    def __init__(self, framework: ops.Framework):
        """Initialize the charm and observe lifecycle events.

        Args:
            framework: the Ops framework instance.
        """
        super().__init__(framework)
        framework.observe(self.on.install, self._reconcile)
        framework.observe(self.on.upgrade_charm, self._reconcile)
        framework.observe(self.on.start, self._reconcile)
        framework.observe(self.on.config_changed, self._reconcile)
        framework.observe(self.on.secret_changed, self._reconcile)
        framework.observe(self.on.update_status, self._reconcile)
        framework.observe(self.on.stop, self._on_stop)

    def _reconcile(self, _: ops.EventBase) -> None:
        """Reconcile the host with the desired charm state.

        Ensures OSQuery is installed, applies the current configuration and
        reports the resulting unit status. The handler is idempotent and safe to
        run on every lifecycle event, so a single reconcile method drives the
        whole charm (a holistic approach).
        """
        try:
            if not osquery.is_installed():
                self.unit.status = ops.MaintenanceStatus("installing OSQuery")
                osquery.install()
            self.unit.status = ops.MaintenanceStatus("configuring OSQuery")
            self._configure()
            self.unit.status = ops.ActiveStatus()
        except OSQueryConfigError as exc:
            # A configuration problem is (usually) something the operator can
            # fix, so surface it plainly without a scary traceback.
            logger.warning("OSQuery configuration problem: %s", exc)
            self.unit.status = ops.BlockedStatus(str(exc))
        except OSQueryError as exc:
            logger.exception("Failed to reconcile OSQuery workload")
            self.unit.status = ops.BlockedStatus(str(exc))

    def _configure(self) -> None:
        """Render the flagfile and secret files, then (re)start the daemon.

        Raises:
            OSQueryConfigError: if a required option is unset, a referenced
                secret is missing, or a file cannot be written.
        """
        values = self._config_values()

        missing = flags.missing_required(values)
        if missing:
            raise OSQueryConfigError("missing required configuration: " + ", ".join(missing))

        self._write_config_files(values)

        proxy_hostname = os.environ.get(HTTPS_PROXY_ENV, "")
        flagfile = flags.render_flagfile(flags.build_flags(values, proxy_hostname))
        osquery.write_flagfile(flagfile)
        osquery.restart()

    def _config_values(self) -> dict:
        """Return every configuration value, with secrets resolved to plaintext.

        Returns:
            A mapping of option name to its resolved value. Options that are
            unset (and have no charm default) map to ``None``.
        """
        values: dict = {name: self.config.get(name) for name in flags.PLAIN_CONFIGS}
        for name in flags.SECRET_CONFIGS:
            values[name] = self._secret_value(name)
        return values

    def _write_config_files(self, values: dict) -> None:
        """Materialise the file-backed options on disk with correct permissions.

        Args:
            values: mapping of option name to its resolved value.
        """
        for name, path in flags.FILE_CONFIGS.items():
            content = values.get(name)
            if content is None:
                continue
            if name in flags.SECRET_CONFIGS:
                osquery.write_secret_file(path, content)
            else:
                osquery.write_public_file(path, content)

    def _secret_value(self, config_key: str) -> Optional[str]:
        """Resolve a secret-typed config option to its plaintext value.

        The option holds a Juju secret URI. The referenced secret is expected to
        expose the value under a field named after the option (for example
        ``enroll-secret``); a single-field secret is also accepted for
        convenience.

        Args:
            config_key: the name of the secret-typed config option.

        Returns:
            The secret value, or ``None`` if the option is unset.

        Raises:
            OSQueryConfigError: if the secret cannot be accessed or does not
                expose a usable field.
        """
        secret_id = self.config.get(config_key)
        if not secret_id:
            return None
        try:
            secret = self.model.get_secret(id=str(secret_id))
            content = secret.get_content(refresh=True)
        except ops.SecretNotFoundError as exc:
            raise OSQueryConfigError(
                f"secret for '{config_key}' not found; grant it to this application"
            ) from exc
        if config_key in content:
            return content[config_key]
        if len(content) == 1:
            return next(iter(content.values()))
        raise OSQueryConfigError(
            f"secret for '{config_key}' must expose a single field or a field named '{config_key}'"
        )

    def _on_stop(self, _: ops.EventBase) -> None:
        """Stop and uninstall OSQuery during unit tear-down."""
        try:
            self.unit.status = ops.MaintenanceStatus("removing OSQuery")
            osquery.uninstall()
        except OSQueryError as exc:
            logger.exception("Failed to stop OSQuery workload cleanly")
            self.unit.status = ops.BlockedStatus(str(exc))


if __name__ == "__main__":  # pragma: nocover
    ops.main(OSQueryCharm)
