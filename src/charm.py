#!/usr/bin/env python3
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for the OSQuery endpoint security monitoring agent."""

import logging

import ops

import osquery
from errors import OSQueryError

logger = logging.getLogger(__name__)


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
        framework.observe(self.on.update_status, self._reconcile)
        framework.observe(self.on.stop, self._on_stop)

    def _reconcile(self, _: ops.EventBase) -> None:
        """Reconcile the host with the desired charm state.

        Ensures OSQuery is installed and reports the resulting unit status. The
        handler is idempotent and safe to run on every lifecycle event, so a
        single reconcile method drives the whole charm (a holistic approach).
        """
        try:
            if not osquery.is_installed():
                self.unit.status = ops.MaintenanceStatus("installing OSQuery")
                osquery.install()
            self.unit.status = ops.ActiveStatus()
        except OSQueryError as exc:
            logger.exception("Failed to reconcile OSQuery workload")
            self.unit.status = ops.BlockedStatus(str(exc))

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
