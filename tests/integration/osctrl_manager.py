# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Manage a throwaway osctrl controller for the integration tests.

A real osctrl deployment is stood up inside a dedicated LXD virtual machine
(named ``osctrl``) that runs Docker. The VM is separate from the Juju-managed
machines so its lifecycle can be controlled directly with the ``lxc`` CLI:

* On first use the VM is launched, the osctrl compose stack (see the ``osctrl``
  directory next to this module) is provisioned, and a *stateless* snapshot of
  the provisioned-but-empty controller is taken.
* Subsequent runs restore that snapshot instead of rebuilding, which is fast and
  guarantees a clean controller with no leftover environments or nodes.
* Passing ``--rebuild-osctrl`` deletes the VM and builds it again from scratch.

Everything the test needs to assert -- that a node enrolled and that osquery is
shipping status and result logs -- is read straight from the osctrl Postgres
database, so no API component or authentication token is required.
"""

from __future__ import annotations

import logging
import re
import subprocess  # nosec B404
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Directory holding the compose file, nginx config and provision script that are
# copied into the VM.
_LOCAL_DIR = Path(__file__).parent / "osctrl"


@dataclass(frozen=True)
class OsctrlEnvironment:
    """An osctrl TLS environment the charm can enroll against.

    Attributes:
        uuid: the environment UUID, used to build the osquery TLS endpoints.
        secret: the enrollment secret osquery must present to enroll.
    """

    uuid: str
    secret: str


class OsctrlError(Exception):
    """Raised when an ``lxc`` or in-VM command fails."""


class OsctrlVM:
    """A real osctrl controller running in a dedicated LXD VM.

    The controller is reachable from the Juju machines at the stable LXD DNS
    name ``osctrl.lxd`` on port 443, terminated by nginx with a self-signed
    certificate whose SAN covers that name.
    """

    INSTANCE = "osctrl"
    SNAPSHOT = "provisioned"
    IMAGE = "ubuntu:24.04"
    HOSTNAME = "osctrl.lxd"
    ENVIRONMENT = "dev"
    SCHEDULED_QUERY = "os_version"

    _REMOTE_DIR = "/root/osctrl"

    def __init__(self, *, rebuild: bool = False) -> None:
        """Initialise the manager.

        Args:
            rebuild: when true, delete any existing VM and provision from
                scratch instead of restoring the snapshot.
        """
        self._rebuild = rebuild

    # -- low-level command helpers -------------------------------------------

    @staticmethod
    def _run(args: list[str], *, check: bool = True, stdin: str | None = None) -> str:
        """Run a command locally and return its stdout.

        Args:
            args: the argv to execute (no shell involved).
            check: raise :class:`OsctrlError` on a non-zero exit.
            stdin: optional text piped to the command's standard input.

        Returns:
            The command's standard output.
        """
        result = subprocess.run(  # nosec B603
            args,
            capture_output=True,
            text=True,
            input=stdin,
        )
        if check and result.returncode != 0:
            raise OsctrlError(
                f"command failed ({result.returncode}): {' '.join(args)}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result.stdout

    def _lxc(self, *args: str, check: bool = True) -> str:
        """Run an ``lxc`` command."""
        return self._run(["lxc", *args], check=check)

    def _exec(self, script: str, *, check: bool = True, stdin: str | None = None) -> str:
        """Run a bash snippet inside the VM and return its stdout."""
        return self._run(
            ["lxc", "exec", self.INSTANCE, "--", "bash", "-c", script],
            check=check,
            stdin=stdin,
        )

    def _cli(self, args: str) -> str:
        """Run an ``osctrl-cli`` command in DB mode inside the VM.

        The released cli image entrypoint is ``/bin/bash`` and mutating commands
        need the global ``--db`` flag to talk to the local database.
        """
        script = (
            f"cd {self._REMOTE_DIR} && docker compose run --rm "
            f"--entrypoint /opt/osctrl/bin/osctrl-cli osctrl-cli --db {args}"
        )
        return self._exec(script)

    def _psql(self, sql: str) -> str:
        """Run a SQL statement against the osctrl database and return the result."""
        script = (
            f"cd {self._REMOTE_DIR} && docker compose exec -T osctrl-postgres "
            f'psql -U osctrl -d osctrl -tAc "{sql}"'
        )
        return self._exec(script).strip()

    # -- lifecycle ------------------------------------------------------------

    def _instance_exists(self) -> bool:
        return (
            subprocess.run(  # nosec B603 B607
                ["lxc", "info", self.INSTANCE],
                capture_output=True,
            ).returncode
            == 0
        )

    def _snapshot_exists(self) -> bool:
        info = self._lxc("info", self.INSTANCE, check=False)
        return re.search(rf"^\s*{re.escape(self.SNAPSHOT)}\b", info, re.MULTILINE) is not None

    def ensure_up(self) -> None:
        """Ensure a clean, provisioned osctrl controller is running.

        Rebuilds from scratch when ``--rebuild-osctrl`` was given or when no
        usable snapshot exists, otherwise restores the provisioned snapshot.
        """
        if self._rebuild and self._instance_exists():
            logger.info("Deleting existing osctrl VM for a clean rebuild")
            self._lxc("delete", self.INSTANCE, "--force")

        if not self._instance_exists():
            self._create_and_provision()
        elif self._snapshot_exists():
            logger.info("Restoring the provisioned osctrl snapshot")
            self._restore()
        else:
            logger.info("osctrl VM has no snapshot; rebuilding from scratch")
            self._lxc("delete", self.INSTANCE, "--force")
            self._create_and_provision()

        self._wait_stack_ready()

    def _create_and_provision(self) -> None:
        """Launch the VM, provision the osctrl stack and snapshot it."""
        logger.info("Launching osctrl VM %s", self.INSTANCE)
        self._lxc(
            "launch",
            self.IMAGE,
            self.INSTANCE,
            "--vm",
            "-c",
            "limits.cpu=2",
            "-c",
            "limits.memory=4GiB",
        )
        self._wait_agent()
        self._exec("cloud-init status --wait")

        logger.info("Copying the osctrl stack into the VM")
        self._exec(f"rm -rf {self._REMOTE_DIR}")
        self._lxc("file", "push", "-r", str(_LOCAL_DIR), f"{self.INSTANCE}/root/")

        logger.info("Provisioning the osctrl stack (this can take a few minutes)")
        self._exec(f"bash {self._REMOTE_DIR}/provision.sh {self.HOSTNAME}")

        logger.info("Snapshotting the provisioned controller")
        self._lxc("stop", self.INSTANCE)
        self._lxc("snapshot", self.INSTANCE, self.SNAPSHOT)
        self._lxc("start", self.INSTANCE)
        self._wait_agent()

    def _restore(self) -> None:
        """Restore the provisioned snapshot to get a clean controller."""
        self._lxc("stop", self.INSTANCE, "--force", check=False)
        self._lxc("restore", self.INSTANCE, self.SNAPSHOT)
        self._lxc("start", self.INSTANCE)
        self._wait_agent()

    def _wait_agent(self, *, timeout: int = 300) -> None:
        """Wait until the LXD agent accepts commands in the VM."""
        self._wait(
            lambda: (
                subprocess.run(  # nosec B603 B607
                    ["lxc", "exec", self.INSTANCE, "--", "true"],
                    capture_output=True,
                ).returncode
                == 0
            ),
            timeout=timeout,
            description="LXD agent to be ready",
        )

    def _wait_stack_ready(self, *, timeout: int = 300) -> None:
        """Wait until Docker is up and the osctrl TLS endpoint answers."""
        self._wait(
            self._docker_ready,
            timeout=120,
            description="Docker daemon to be ready",
        )
        # Make sure the stack is running (restart policy usually handles this on
        # boot, but be explicit so a restored snapshot is guaranteed up).
        self._exec(f"cd {self._REMOTE_DIR} && docker compose up -d")
        self._wait(
            self._nginx_answers,
            timeout=timeout,
            description="osctrl TLS endpoint to answer",
        )

    def _docker_ready(self) -> bool:
        return (
            subprocess.run(  # nosec B603 B607
                ["lxc", "exec", self.INSTANCE, "--", "docker", "info"],
                capture_output=True,
            ).returncode
            == 0
        )

    def _nginx_answers(self) -> bool:
        code = self._exec(
            "curl -sk -o /dev/null -w '%{http_code}' https://localhost/",
            check=False,
        ).strip()
        return code not in ("", "000")

    @staticmethod
    def _wait(predicate, *, timeout: int, description: str, interval: int = 5) -> None:
        """Poll ``predicate`` until it is truthy or ``timeout`` seconds elapse."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                if predicate():
                    return
            except OsctrlError:
                pass
            time.sleep(interval)
        raise OsctrlError(f"timed out after {timeout}s waiting for {description}")

    # -- controller operations ------------------------------------------------

    def create_environment(self) -> OsctrlEnvironment:
        """Create a fresh TLS environment with a scheduled query.

        Returns:
            The environment UUID and enrollment secret.
        """
        logger.info("Creating osctrl environment %s", self.ENVIRONMENT)
        self._cli(f"environment add -n {self.ENVIRONMENT} --host {self.HOSTNAME} -c -l -q -C")
        show = self._cli(f"environment show -n {self.ENVIRONMENT}")
        match = re.search(r"UUID:\s*(\S+)", show)
        if not match:
            raise OsctrlError(f"could not parse environment UUID from:\n{show}")
        uuid = match.group(1)

        secret = (
            self._cli(f"environment node-actions secret -n {self.ENVIRONMENT}")
            .strip()
            .splitlines()[-1]
            .strip()
        )

        # A fast-running query so result logs appear quickly during the test.
        self._cli(
            f"environment add-scheduled-query -n {self.ENVIRONMENT} "  # nosec B608
            f"-q 'SELECT * FROM os_version;' -Q {self.SCHEDULED_QUERY} -i 20"
        )
        return OsctrlEnvironment(uuid=uuid, secret=secret)

    def server_certificate(self) -> str:
        """Return the PEM server certificate the controller presents on 443."""
        return self._exec(f"cat {self._REMOTE_DIR}/certs/osctrl.crt")

    def ip_address(self) -> str:
        """Return the VM's IPv4 address reachable from the Juju machines.

        ``hostname -I`` also lists the Docker bridge addresses and its ordering
        is not stable, so the source address the VM uses for outbound traffic --
        its LXD-bridge address, which other instances on that bridge can reach --
        is used instead.
        """
        return self._exec("ip -4 route get 1.1.1.1 | grep -oP 'src \\K[0-9.]+'").strip()

    def node_count(self) -> int:
        """Return the number of live enrolled nodes in the environment."""
        out = self._psql(
            "SELECT count(*) FROM osquery_nodes "  # nosec B608
            f"WHERE environment='{self.ENVIRONMENT}' AND deleted_at IS NULL"
        )
        return int(out or "0")

    def node_hostname(self) -> str:
        """Return the hostname of the most recently seen enrolled node."""
        return self._psql(
            "SELECT hostname FROM osquery_nodes "  # nosec B608
            f"WHERE environment='{self.ENVIRONMENT}' AND deleted_at IS NULL "
            "ORDER BY last_seen DESC LIMIT 1"
        )

    def status_log_count(self) -> int:
        """Return the number of osquery status log rows for the environment."""
        out = self._psql(
            f"SELECT count(*) FROM osquery_status_data WHERE environment='{self.ENVIRONMENT}'"  # nosec B608
        )
        return int(out or "0")

    def result_log_count(self) -> int:
        """Return the number of scheduled-query result log rows."""
        out = self._psql(
            "SELECT count(*) FROM osquery_result_data "  # nosec B608
            f"WHERE environment='{self.ENVIRONMENT}' AND name='{self.SCHEDULED_QUERY}'"
        )
        return int(out or "0")

    def wait_for(self, predicate, *, timeout: int, description: str) -> None:
        """Public wrapper around the internal polling helper."""
        self._wait(predicate, timeout=timeout, description=description)
