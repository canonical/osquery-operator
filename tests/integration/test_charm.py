# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests that deploy the OSQuery subordinate charm."""

import contextlib
import json
import time
import uuid
from pathlib import Path

import jubilant
import pytest

from .conftest import BASES, CHARM_NAME, PACKAGE_NAME, PRINCIPAL_CHARM

# A single base is enough for the behavioural tests below; they exercise the
# running daemon rather than the per-base packaging, which test_deploy_and_relate
# already covers across every base.
BEHAVIOUR_BASE = "ubuntu@24.04"

DUMMY_CONTROLLER = Path(__file__).parent / "dummy_controller.py"


def _sh(juju: jubilant.Juju, unit: str, script: str) -> str:
    """Run a shell snippet on a unit and return its stdout.

    The snippet is wrapped so a non-zero exit does not raise, letting callers
    read output from commands like ``systemctl is-active`` that signal state
    through their exit code.
    """
    return juju.exec("bash", "-c", f"{script}\n", unit=unit, wait=120).stdout


def _osqueryd_count(juju: jubilant.Juju, unit: str) -> int:
    """Return the number of running ``osqueryd`` processes on the unit."""
    out = _sh(juju, unit, "pgrep -c -x osqueryd || true").strip()
    return int(out or "0")


def _principal_unit(juju: jubilant.Juju, app: str) -> str:
    """Return the first unit name of ``app`` (robust to non-zero unit indices)."""
    status = juju.status()
    return next(iter(status.apps[app].units))


@pytest.mark.parametrize("base", BASES)
def test_deploy_and_relate(juju: jubilant.Juju, charm_paths, base: str):
    """The subordinate deploys, relates to a principal and becomes active.

    The charm is built for each supported Ubuntu base, so this test runs once
    per base to confirm the base-specific artifact installs OSQuery from the
    PPA on a matching principal machine.

    Steps:
    - Deploy the `ubuntu` principal application on the base under test.
    - Deploy the matching OSQuery subordinate artifact for that base.
    - Relate the two, set the required controller options and wait for active.
    - Confirm OSQuery is installed on the principal machine.
    - Confirm the generated flagfile reflects the configuration.
    - Remove the subordinate and confirm OSQuery is uninstalled.
    """
    # Give each base its own application names so the parametrised runs can
    # share a single Juju model without colliding.
    suffix = base.split("@", 1)[1].replace(".", "")
    principal_app = f"ubuntu{suffix}"
    osquery_app = f"osquery{suffix}"

    juju.deploy(PRINCIPAL_CHARM, principal_app, base=base)
    juju.deploy(charm_paths[CHARM_NAME][base], osquery_app, base=base)
    juju.integrate(principal_app, osquery_app)

    # The two required options must be set or the subordinate stays blocked.
    juju.config(
        osquery_app,
        {
            "controller-uri": "controller.example.com",
            "controller-env-uuid": "test-env-uuid",
        },
    )

    juju.wait(
        lambda status: jubilant.all_active(status, principal_app, osquery_app),
        timeout=20 * 60,
    )
    unit = _principal_unit(juju, principal_app)

    # The subordinate installs OSQuery onto the principal's machine.
    installed = juju.exec(
        "dpkg-query",
        "-f",
        "${db:Status-Status}",
        "-W",
        PACKAGE_NAME,
        unit=unit,
        wait=60,
    )
    assert installed.stdout.strip() == "installed"

    # The generated flagfile reflects the configuration: controller-uri becomes
    # the TLS hostname and controller-env-uuid expands into the config endpoint.
    flagfile = juju.exec(
        "cat",
        "/etc/osquery/osquery.flags",
        unit=unit,
        wait=60,
    )
    assert "--tls_hostname=controller.example.com:443" in flagfile.stdout
    assert "--config_tls_endpoint=/test-env-uuid/config" in flagfile.stdout

    # Removing the subordinate runs its stop hook, which uninstalls OSQuery.
    juju.remove_application(osquery_app)
    juju.wait(lambda status: osquery_app not in status.apps, timeout=10 * 60)

    # After `apt-get remove` the package leaves the "installed" state (dpkg still
    # knows it while config files linger, so check the status field, not the
    # exit code).
    removed = juju.exec(
        "dpkg-query",
        "-f",
        "${db:Status-Status}",
        "-W",
        PACKAGE_NAME,
        unit=unit,
        wait=60,
    )
    assert removed.stdout.strip() != "installed"


def _wait_for_stable_osqueryd_count(
    juju: jubilant.Juju, unit: str, expected: int, *, attempts: int = 18
) -> bool:
    """Poll until ``osqueryd`` holds ``expected`` processes across two samples.

    A single matching read is not enough: a crash-looping daemon momentarily
    shows the right number of processes between restarts. Requiring two spaced
    samples to agree confirms the daemon has settled and is genuinely running.

    Returns ``True`` once the count is stable; raises AssertionError otherwise.
    """
    stable = 0
    for _ in range(attempts):
        if _osqueryd_count(juju, unit) == expected:
            stable += 1
            if stable >= 2:
                return True
        else:
            stable = 0
        time.sleep(10)
    actual = _osqueryd_count(juju, unit)
    raise AssertionError(f"expected a stable {expected} osqueryd processes, found {actual}")


def _start_dummy_controller(juju: jubilant.Juju, unit: str) -> str:
    """Run the dummy HTTPS controller on ``unit`` and return its server cert.

    The controller listens on port 443 (osquery's hard-coded ``tls_hostname``
    port) and records enrollment request bodies to ``/root/enroll_request.json``.
    """
    juju.scp(str(DUMMY_CONTROLLER), f"{unit}:/tmp/dummy_controller.py")
    _sh(
        juju,
        unit,
        "openssl req -x509 -newkey rsa:2048 -nodes "
        "-keyout /root/ctrl.key -out /root/ctrl.crt -days 1 "
        '-subj "/CN=localhost" '
        '-addext "subjectAltName=DNS:localhost,IP:127.0.0.1"',
    )
    _sh(
        juju,
        unit,
        "systemctl reset-failed dummy-controller 2>/dev/null; "
        "systemd-run --unit=dummy-controller --collect /usr/bin/python3 "
        "/tmp/dummy_controller.py 443 /root/ctrl.crt /root/ctrl.key "
        "/root/enroll_request.json",
    )
    return _sh(juju, unit, "cat /root/ctrl.crt")


def test_daemon_enrols_and_honours_config(juju: jubilant.Juju, charm_paths):
    """The subordinate blocks without a controller, then enrols and obeys config.

    A dummy HTTPS controller runs on the principal machine (co-located with the
    subordinate, so ``controller-uri=localhost`` reaches it on the hard-coded
    port 443). The test asserts, end-to-end, that:

    - the subordinate is ``blocked`` until the required controller options are
      set;
    - once configured, ``osqueryd`` is genuinely running (checked via systemd
      and the process table, since there is no osquery CLI on the host), meaning
      stable and not crash-looping;
    - a secret option (the enrollment secret) and a plain option
      (``host-identifier``) took effect: the real daemon enrols and the
      controller records both in the request body;
    - a further plain option reaches the running daemon and changes its
      behaviour: enabling ``disable-watchdog`` drops osquery from two processes
      (watchdog parent plus worker) to a single process.
    """
    principal_app = "ubuntu-enroll"
    osquery_app = "osquery-enroll"
    env_uuid = str(uuid.uuid4())
    enroll_secret = "integration-enroll-secret"  # nosec B105 - test fixture value
    # Unique per run: Juju secrets outlive the application, so a fixed name would
    # collide when the module-scoped model is reused across runs.
    secret_name = f"osquery-enroll-secret-{uuid.uuid4().hex[:8]}"

    juju.deploy(PRINCIPAL_CHARM, principal_app, base=BEHAVIOUR_BASE)
    juju.deploy(charm_paths[CHARM_NAME][BEHAVIOUR_BASE], osquery_app, base=BEHAVIOUR_BASE)
    juju.integrate(principal_app, osquery_app)

    unit = f"{principal_app}/0"
    try:
        # Without the required controller options the subordinate blocks while
        # the principal comes up ready for the dummy controller.
        juju.wait(
            lambda status: (
                jubilant.all_active(status, principal_app)
                and jubilant.all_blocked(status, osquery_app)
            ),
            timeout=20 * 60,
        )
        unit = _principal_unit(juju, principal_app)

        # Stand up the dummy controller on the principal machine.
        server_cert = _start_dummy_controller(juju, unit)
        hostname = _sh(juju, unit, "hostname").strip()

        # Supply the enrollment secret as a Juju user secret.
        secret_uri = juju.add_secret(secret_name, {"enroll-secret": enroll_secret})
        juju.grant_secret(secret_uri, osquery_app)

        # Point the agent at the dummy controller and give it an identifier.
        juju.config(
            osquery_app,
            {
                "controller-uri": "localhost",
                "controller-env-uuid": env_uuid,
                "tls-server-certs": server_cert,
                "host-identifier": "hostname",
                "enroll-secret": str(secret_uri),
            },
        )
        juju.wait(
            lambda status: jubilant.all_active(status, principal_app, osquery_app),
            timeout=10 * 60,
        )

        # The daemon is genuinely running under systemd, with the watchdog
        # enabled (osquery's default) there is a watchdog parent plus a worker:
        # two osqueryd processes. A stable count also proves it is not
        # crash-looping.
        assert _sh(juju, unit, "systemctl is-active osqueryd || true").strip() == "active"
        assert _wait_for_stable_osqueryd_count(juju, unit, 2)

        # The daemon enrols on start; wait for the controller to record it. This
        # proves the secret option (enroll secret) and a plain option
        # (host-identifier) both took effect end-to-end.
        recorded = _wait_for_enroll_request(juju, unit)
        assert recorded["enroll_secret"] == enroll_secret
        assert recorded["host_identifier"] == hostname

        # Turning the watchdog off must reach the daemon and collapse it to one
        # process, a behaviour change we can measure without an osquery CLI.
        juju.config(osquery_app, {"disable-watchdog": True})
        juju.wait(
            lambda status: jubilant.all_active(status, principal_app, osquery_app),
            timeout=10 * 60,
        )
        assert "--disable_watchdog=true" in _sh(juju, unit, "cat /etc/osquery/osquery.flags")
        assert _wait_for_stable_osqueryd_count(juju, unit, 1)
    finally:
        with contextlib.suppress(jubilant.CLIError, ValueError, KeyError, StopIteration):
            juju.exec(
                "bash",
                "-c",
                "systemctl stop dummy-controller 2>/dev/null || true\n",
                unit=unit,
                wait=120,
            )
        juju.remove_application(osquery_app, destroy_storage=True)
        juju.remove_application(principal_app, destroy_storage=True)
        with contextlib.suppress(jubilant.CLIError):
            juju.remove_secret(secret_name)


def _wait_for_enroll_request(juju: jubilant.Juju, unit: str, *, attempts: int = 24) -> dict:
    """Poll the dummy controller's recorded enrollment request body."""
    for _ in range(attempts):
        body = _sh(juju, unit, "cat /root/enroll_request.json 2>/dev/null || true").strip()
        if body:
            return json.loads(body)
        time.sleep(10)
    raise AssertionError("osqueryd never sent an enrollment request to the controller")
