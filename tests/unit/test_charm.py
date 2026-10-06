# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the OSQuery charm lifecycle."""

import pytest
from ops import testing

import osquery
from charm import OSQueryCharm
from errors import OSQueryConfigError, OSQueryInstallError

# The snap channel charmcraft.yaml defaults the snap-channel option to.
DEFAULT_CHANNEL = "latest/edge"

# The two options a working deployment must always set.
VALID_CONFIG = {
    "controller-uri": "controller.example.com",
    "controller-env-uuid": "env-abc",
}


@pytest.fixture(name="ctx")
def ctx_fixture():
    """Return an ops testing context for the charm."""
    return testing.Context(OSQueryCharm)


@pytest.mark.parametrize(
    "event",
    [
        "install",
        "upgrade_charm",
        "start",
        "config_changed",
        "update_status",
    ],
)
def test_reconcile_installs_and_configures_when_missing(ctx, patch_workload, event):
    """Every reconcile event installs, configures and reports active."""
    state = testing.State(config=VALID_CONFIG)

    out = ctx.run(getattr(ctx.on, event)(), state)

    assert patch_workload.installed is True
    assert patch_workload.install_count == 1
    assert patch_workload.channel == DEFAULT_CHANNEL
    assert patch_workload.restarted == 1
    assert patch_workload.flagfile is not None
    assert "--tls_hostname=controller.example.com:443" in patch_workload.flagfile
    assert out.unit_status == testing.ActiveStatus()


def test_reconcile_is_idempotent_when_already_installed(ctx, patch_workload):
    """Reconciling with OSQuery already on the configured channel does not reinstall."""
    patch_workload.installed = True
    patch_workload.channel = DEFAULT_CHANNEL
    state = testing.State(config=VALID_CONFIG)

    out = ctx.run(ctx.on.update_status(), state)

    assert patch_workload.install_count == 0
    assert out.unit_status == testing.ActiveStatus()


def test_snap_channel_option_selects_channel(ctx, patch_workload):
    """The snap is installed from the channel set in snap-channel."""
    state = testing.State(config={**VALID_CONFIG, "snap-channel": "5.21/stable"})

    out = ctx.run(ctx.on.install(), state)

    assert patch_workload.channel == "5.21/stable"
    assert out.unit_status == testing.ActiveStatus()


def test_snap_channel_change_refreshes_snap(ctx, patch_workload):
    """Changing snap-channel moves an installed snap onto the new channel."""
    patch_workload.installed = True
    patch_workload.channel = DEFAULT_CHANNEL
    state = testing.State(config={**VALID_CONFIG, "snap-channel": "latest/beta"})

    ctx.run(ctx.on.config_changed(), state)

    assert patch_workload.install_count == 1
    assert patch_workload.channel == "latest/beta"


def test_snap_channel_not_rendered_as_flag(ctx, patch_workload):
    """snap-channel configures the charm, so it never reaches the flagfile."""
    state = testing.State(config=VALID_CONFIG)

    ctx.run(ctx.on.config_changed(), state)

    assert "snap_channel" not in patch_workload.flagfile


def test_empty_snap_channel_blocks(ctx, patch_workload):
    """An empty snap-channel blocks the unit before anything is installed."""
    state = testing.State(config={**VALID_CONFIG, "snap-channel": ""})

    out = ctx.run(ctx.on.config_changed(), state)

    assert out.unit_status == testing.BlockedStatus("missing required configuration: snap-channel")
    assert patch_workload.installed is False


def test_unavailable_snap_channel_blocks(ctx, monkeypatch):
    """A channel the store does not offer blocks the unit with a clear message."""
    monkeypatch.setattr("osquery.is_installed", lambda: False)

    def fail_install(channel):
        raise OSQueryConfigError(f"snap channel '{channel}' is not available for c-osquery")

    monkeypatch.setattr("osquery.install", fail_install)
    state = testing.State(config={**VALID_CONFIG, "snap-channel": "nope/stable"})

    out = ctx.run(ctx.on.config_changed(), state)

    assert out.unit_status == testing.BlockedStatus(
        "snap channel 'nope/stable' is not available for c-osquery"
    )


def test_reconcile_does_not_restart_when_config_unchanged(ctx, patch_workload):
    """A reconcile that changes nothing on disk leaves the daemon untouched."""
    patch_workload.installed = True
    patch_workload.running = True
    state = testing.State(config=VALID_CONFIG)

    # First reconcile renders and applies the config, restarting once.
    ctx.run(ctx.on.config_changed(), state)
    assert patch_workload.restarted == 1

    # A second reconcile with identical config must not restart again.
    out = ctx.run(ctx.on.update_status(), state)

    assert patch_workload.restarted == 1
    assert out.unit_status == testing.ActiveStatus()


def test_reconcile_restarts_stopped_daemon_without_config_change(ctx, patch_workload):
    """A stopped daemon is restarted even when the config did not change."""
    patch_workload.installed = True
    state = testing.State(config=VALID_CONFIG)

    ctx.run(ctx.on.config_changed(), state)
    assert patch_workload.restarted == 1

    # Simulate the daemon dying (or a reboot) with the config unchanged.
    patch_workload.running = False
    ctx.run(ctx.on.update_status(), state)

    assert patch_workload.restarted == 2


def test_flagfile_contains_defaults_and_endpoints(ctx, patch_workload):
    """Charm defaults and env-derived endpoints end up in the flagfile."""
    state = testing.State(config=VALID_CONFIG)

    ctx.run(ctx.on.config_changed(), state)

    flagfile = patch_workload.flagfile
    assert "--config_tls_endpoint=/env-abc/config" in flagfile
    assert "--logger_plugin=tls" in flagfile
    assert "--force=true" in flagfile
    assert "--carver_block_size=5120000" in flagfile


def test_missing_required_config_blocks(ctx, patch_workload):
    """With no controller config the unit blocks and nothing is applied."""
    state = testing.State()

    out = ctx.run(ctx.on.config_changed(), state)

    assert isinstance(out.unit_status, testing.BlockedStatus)
    assert "controller-uri" in out.unit_status.message
    assert "controller-env-uuid" in out.unit_status.message
    # The snap is still installed, but no flagfile is written and the daemon
    # is not restarted while required configuration is missing.
    assert patch_workload.installed is True
    assert patch_workload.flagfile is None
    assert patch_workload.restarted == 0


def test_secret_config_written_and_referenced(ctx, patch_workload):
    """A secret-typed option is resolved, written to disk and referenced."""
    secret = testing.Secret(tracked_content={"enroll-secret": "s3cr3t"})
    state = testing.State(
        config={**VALID_CONFIG, "enroll-secret": secret.id},
        secrets={secret},
    )

    ctx.run(ctx.on.config_changed(), state)

    assert patch_workload.files[osquery.ENROLL_SECRET_PATH] == "s3cr3t"
    assert f"--enroll_secret_path={osquery.ENROLL_SECRET_PATH}" in patch_workload.flagfile


def test_secret_single_field_fallback(ctx, patch_workload):
    """A single-field secret is accepted even without the expected field name."""
    secret = testing.Secret(tracked_content={"whatever": "value"})
    state = testing.State(
        config={**VALID_CONFIG, "enroll-secret": secret.id},
        secrets={secret},
    )

    ctx.run(ctx.on.config_changed(), state)

    assert patch_workload.files[osquery.ENROLL_SECRET_PATH] == "value"


def test_secret_multiple_fields_blocks(ctx, patch_workload):
    """An ambiguous multi-field secret blocks the unit."""
    secret = testing.Secret(tracked_content={"a": "1", "b": "2"})
    state = testing.State(
        config={**VALID_CONFIG, "enroll-secret": secret.id},
        secrets={secret},
    )

    out = ctx.run(ctx.on.config_changed(), state)

    assert isinstance(out.unit_status, testing.BlockedStatus)


def test_missing_secret_blocks(ctx, patch_workload):
    """Referencing a secret that was not granted blocks the unit."""
    state = testing.State(config={**VALID_CONFIG, "enroll-secret": "secret:cvh7kruupa1s46bqvuig"})

    out = ctx.run(ctx.on.config_changed(), state)

    assert isinstance(out.unit_status, testing.BlockedStatus)


def test_public_cert_written_with_public_writer(ctx, patch_workload):
    """A non-secret certificate option is materialised and referenced."""
    state = testing.State(config={**VALID_CONFIG, "tls-server-certs": "CERTDATA"})

    ctx.run(ctx.on.config_changed(), state)

    assert patch_workload.files[osquery.SERVER_CERTS_PATH] == "CERTDATA"
    assert f"--tls_server_certs={osquery.SERVER_CERTS_PATH}" in patch_workload.flagfile


def test_proxy_hostname_flag_from_env(ctx, patch_workload, monkeypatch):
    """proxy_hostname comes from juju-https-proxy (JUJU_CHARM_HTTPS_PROXY), as host:port."""
    monkeypatch.setenv("JUJU_CHARM_HTTPS_PROXY", "http://proxy:3128")
    state = testing.State(config=VALID_CONFIG)

    ctx.run(ctx.on.config_changed(), state)

    assert "--proxy_hostname=proxy:3128\n" in patch_workload.flagfile


@pytest.mark.parametrize("name", ["HTTPS_PROXY", "https_proxy"])
def test_proxy_hostname_flag_from_legacy_proxy(ctx, patch_workload, monkeypatch, name):
    """On models with the legacy https-proxy, Juju sets HTTPS_PROXY/https_proxy instead."""
    monkeypatch.setenv(name, "http://squid.internal:3128")
    state = testing.State(config=VALID_CONFIG)

    ctx.run(ctx.on.config_changed(), state)

    assert "--proxy_hostname=squid.internal:3128\n" in patch_workload.flagfile


def test_juju_proxy_wins_over_legacy_proxy(ctx, patch_workload, monkeypatch):
    monkeypatch.setenv("JUJU_CHARM_HTTPS_PROXY", "http://juju-proxy:3128")
    monkeypatch.setenv("HTTPS_PROXY", "http://legacy-proxy:3128")
    state = testing.State(config=VALID_CONFIG)

    ctx.run(ctx.on.config_changed(), state)

    assert "--proxy_hostname=juju-proxy:3128\n" in patch_workload.flagfile


def test_no_proxy_flag_without_proxy(ctx, patch_workload):
    state = testing.State(config=VALID_CONFIG)

    ctx.run(ctx.on.config_changed(), state)

    assert "proxy_hostname" not in patch_workload.flagfile


def test_stop_uninstalls_workload(ctx, patch_workload):
    """Stopping the unit uninstalls the workload."""
    patch_workload.installed = True
    state = testing.State()

    ctx.run(ctx.on.stop(), state)

    assert patch_workload.uninstalled is True


@pytest.mark.parametrize(
    "event",
    [
        "install",
        "upgrade_charm",
        "start",
        "config_changed",
        "update_status",
    ],
)
def test_reconcile_failure_sets_blocked_status(ctx, monkeypatch, event):
    """A workload error during install is converted to blocked status."""
    monkeypatch.setattr("osquery.is_installed", lambda: False)

    def fail_install(channel):
        raise OSQueryInstallError("install failed")

    monkeypatch.setattr("osquery.install", fail_install)
    state = testing.State(config=VALID_CONFIG)

    out = ctx.run(getattr(ctx.on, event)(), state)

    assert out.unit_status == testing.BlockedStatus("install failed")


def test_stop_failure_sets_blocked_status(ctx, monkeypatch):
    """A custom workload error is converted to blocked status during stop."""

    def fail_uninstall():
        raise OSQueryInstallError("remove failed")

    monkeypatch.setattr("osquery.uninstall", fail_uninstall)
    state = testing.State()

    out = ctx.run(ctx.on.stop(), state)

    assert out.unit_status == testing.BlockedStatus("remove failed")
