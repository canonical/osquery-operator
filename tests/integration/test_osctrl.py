# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration test against a real osctrl controller.

Unlike the tests in ``test_charm.py`` that use a minimal dummy controller, this
test stands up a genuine osctrl deployment (in a dedicated LXD VM) and checks
the full path: the charm enrolls osquery against osctrl over TLS -- trusting the
controller's self-signed certificate through the ``tls-server-certs`` option --
and osquery then ships status and scheduled-query result logs that land in
osctrl's database.
"""

import contextlib
import logging
import uuid

import jubilant

from .conftest import CHARM_NAME, PRINCIPAL_CHARM
from .osctrl_manager import OsctrlVM

logger = logging.getLogger(__name__)

# osctrl publishes packages for this base and it is enough to prove the path.
BASE = "ubuntu@24.04"


def _sh(juju: jubilant.Juju, unit: str, script: str) -> str:
    """Run a shell snippet on a unit (as root) and return its stdout."""
    return juju.exec("bash", "-c", f"{script}\n", unit=unit, wait=120).stdout


def _principal_unit(juju: jubilant.Juju, app: str) -> str:
    """Return the first unit name of ``app``."""
    return next(iter(juju.status().apps[app].units))


def test_osquery_enrols_with_real_osctrl_and_ships_logs(
    juju: jubilant.Juju, charm_paths, osctrl: OsctrlVM
):
    """Osquery enrols against a real osctrl and ships logs.

    Steps:
    - Create a fresh osctrl TLS environment (with a scheduled query) and read its
      UUID and enrollment secret.
    - Deploy the ``ubuntu`` principal and the osquery subordinate; confirm the
      subordinate blocks until the controller options are set.
    - Make the controller reachable on the principal machine with an
      ``osctrl.lxd`` hosts entry.
    - Configure the subordinate to point at osctrl, trusting its self-signed
      certificate through ``tls-server-certs``, and wait for it to go active.
    - Assert, reading osctrl's database directly, that the node enrolled and that
      osquery shipped both status logs and scheduled-query result logs.
    """
    env = osctrl.create_environment()

    principal_app = "ubuntu-osctrl"
    osquery_app = "osquery-osctrl"
    secret_name = f"osctrl-enroll-secret-{uuid.uuid4().hex[:8]}"

    juju.deploy(PRINCIPAL_CHARM, principal_app, base=BASE)
    juju.deploy(charm_paths[CHARM_NAME][BASE], osquery_app, base=BASE)
    juju.integrate(principal_app, osquery_app)

    unit = f"{principal_app}/0"
    try:
        # Without the controller options the subordinate blocks while the
        # principal comes up.
        juju.wait(
            lambda status: (
                jubilant.all_active(status, principal_app)
                and jubilant.all_blocked(status, osquery_app)
            ),
            timeout=20 * 60,
        )
        unit = _principal_unit(juju, principal_app)

        # Make the controller reachable at its stable name.
        controller_ip = osctrl.ip_address()
        _sh(
            juju,
            unit,
            f"grep -q ' {OsctrlVM.HOSTNAME}$' /etc/hosts "
            f"|| echo '{controller_ip} {OsctrlVM.HOSTNAME}' >> /etc/hosts",
        )

        # Supply the enrollment secret as a Juju user secret.
        secret_uri = juju.add_secret(secret_name, {"enroll-secret": env.secret})
        juju.grant_secret(secret_uri, osquery_app)

        # Point the subordinate at osctrl. Its certificate is self-signed and
        # the snap's CA bundle is read-only, so it goes in tls-server-certs.
        # Short logger/config periods keep the test quick.
        juju.config(
            osquery_app,
            {
                "controller-uri": OsctrlVM.HOSTNAME,
                "controller-env-uuid": env.uuid,
                "tls-server-certs": osctrl.server_certificate(),
                "enroll-secret": str(secret_uri),
                "logger-tls-period": 10,
                "config-refresh": 10,
            },
        )
        juju.wait(
            lambda status: jubilant.all_active(status, principal_app, osquery_app),
            timeout=15 * 60,
        )

        # The node enrols against the real controller over TLS.
        osctrl.wait_for(
            lambda: osctrl.node_count() >= 1,
            timeout=5 * 60,
            description="osquery to enrol against osctrl",
        )
        logger.info("osctrl reports %d enrolled node(s)", osctrl.node_count())

        # osquery ships status logs and scheduled-query result logs to osctrl.
        osctrl.wait_for(
            lambda: osctrl.status_log_count() >= 1,
            timeout=5 * 60,
            description="osquery status logs to reach osctrl",
        )
        osctrl.wait_for(
            lambda: osctrl.result_log_count() >= 1,
            timeout=5 * 60,
            description="scheduled-query result logs to reach osctrl",
        )
        logger.info(
            "osctrl received %d status log row(s) and %d result log row(s)",
            osctrl.status_log_count(),
            osctrl.result_log_count(),
        )

        # The enrolled node is the principal machine. osctrl records the
        # fully-qualified hostname osquery reports.
        enrolled_hostname = osctrl.node_hostname()
        expected_hostname = _sh(juju, unit, "hostname -f").strip()
        logger.info(
            "Enrolled node hostname %r (expected %r)", enrolled_hostname, expected_hostname
        )
        assert enrolled_hostname == expected_hostname
    finally:
        juju.remove_application(osquery_app, destroy_storage=True)
        juju.remove_application(principal_app, destroy_storage=True)
        with contextlib.suppress(jubilant.CLIError):
            juju.remove_secret(secret_name)
