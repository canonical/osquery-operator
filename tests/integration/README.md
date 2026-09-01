# Integration tests

These tests deploy the OSQuery subordinate charm onto real Juju machines (LXD)
and exercise it end to end. There are two suites:

| Suite | File | Controller | Marker | tox env |
| --- | --- | --- | --- | --- |
| Charm behaviour | [`test_charm.py`](test_charm.py) | A minimal **dummy** HTTPS controller co-located on the principal machine | *(none)* | `integration` |
| Real osctrl | [`test_osctrl.py`](test_osctrl.py) | A **real** [osctrl](https://osctrl.net/) deployment in a dedicated LXD VM | `osctrl` | `integration-osctrl` |

The `osctrl` marker separates the two suites for **local** runs: `tox -e
integration` runs the fast charm suite (`-m "not osctrl"`), while `tox -e
integration-osctrl` runs the real-osctrl suite (`-m osctrl`). On CI both suites
run on every pull request — see [Continuous integration](#continuous-integration).

## Contents

- [`conftest.py`](conftest.py) — the `juju` model fixture and the session-scoped
  `osctrl` fixture.
- [`test_charm.py`](test_charm.py) — packaging and behaviour tests against the
  dummy controller.
- [`dummy_controller.py`](dummy_controller.py) — a tiny HTTPS server that records
  osquery enrollment requests; used only by `test_charm.py`.
- [`test_osctrl.py`](test_osctrl.py) — the real-osctrl enrollment and
  log-shipping test.
- [`osctrl_manager.py`](osctrl_manager.py) — lifecycle manager for the osctrl VM
  (launch, provision, snapshot/restore, and Postgres-based assertions).
- [`osctrl/`](osctrl/) — the osctrl Docker Compose stack copied into the VM
  (`docker-compose.yaml`, `.env`, `osctrl-nginx.conf`, `provision.sh`).

## Prerequisites

The tests run on an Ubuntu host with passwordless `sudo` and the user in the
`lxd` group. One-time setup:

```bash
sudo snap install concierge charmcraft astral-uv --classic
uv python install
uv tool install tox --with tox-uv

# Installs Juju 3.6, initialises LXD, bootstraps the `concierge-lxd`
# controller and creates the `testing` model (see concierge.yaml).
sudo concierge prepare --verbose

# Installs opcli (from charm-ci) and the rest of the integration deps.
uv sync --group integration
```

Ensure `PATH` includes `$HOME/.local/bin` and `/snap/bin`.

### Build the charms first

Both suites deploy the charm through the `charm_paths` fixture, which reads the
per-base artifact paths from `artifacts.build.yaml`. Build them before running:

```bash
uv run --group integration opcli artifacts build
```

This packs the charm for every supported base (Ubuntu 22.04, 24.04 and 26.04)
and writes `artifacts.build.yaml`. It takes several minutes.

## Running the tests

Pass `--model testing` to reuse the concierge-created model; without `--model`
the `juju` fixture creates a temporary model per test module.

```bash
# Default suite (dummy controller). Excludes the osctrl suite.
tox -e integration -- --model testing

# Real-osctrl suite only.
tox -e integration-osctrl -- --model testing
```

Useful pytest options (defined in [`../conftest.py`](../conftest.py)):

| Option | Effect |
| --- | --- |
| `--model NAME` | Reuse an existing Juju model instead of a temporary one. |
| `--rebuild-osctrl` | Delete and rebuild the osctrl VM from scratch instead of restoring its provisioned snapshot. |
| `--keep-models` | Keep temporarily-created models after the run. |

Run a single test by node id, e.g.:

```bash
tox -e integration-osctrl -- --model testing \
  tests/integration/test_osctrl.py::test_osquery_enrols_with_real_osctrl_and_ships_logs
```

## Suite 1: charm behaviour (`test_charm.py`)

Runs against `dummy_controller.py`, a self-contained HTTPS server started on the
principal machine that records enrollment request bodies. No external network or
VM is required.

- **`test_deploy_and_relate[<base>]`** — parametrised over all supported bases.
  Deploys the `ubuntu` principal and the matching OSQuery subordinate artifact,
  relates them, sets the two required controller options, and asserts the
  OSQuery apt package is installed and the generated
  `/etc/osquery/osquery.flags` reflects the configuration. Removing the
  subordinate uninstalls the package.
- **`test_daemon_enrols_and_honours_config`** — starts the dummy controller on
  the principal (reachable at `controller-uri=localhost` on osquery's hard-coded
  port 443) and asserts, end to end, that the subordinate is `blocked` until the
  controller options are set; that `osqueryd` runs stably (not crash-looping);
  that a secret option (the enrollment secret) and a plain option
  (`host-identifier`) reach the daemon (the controller records both); and that
  toggling `disable-watchdog` changes the running process count.

## Suite 2: real osctrl (`test_osctrl.py`)

`test_osquery_enrols_with_real_osctrl_and_ships_logs` proves the full path
against a genuine osctrl controller, with **no TLS certificate handed to the
charm** — onboarding uses only an enrollment token, exactly as a real fleet
would.

Flow:

1. Create a fresh osctrl TLS environment (with a fast scheduled query) and read
   its UUID and enrollment secret.
2. Deploy the `ubuntu` principal and OSQuery subordinate; confirm the
   subordinate `blocked`s until the controller options are set.
3. Make the controller reachable and trusted on the principal machine:
   - add an `osctrl.lxd` `/etc/hosts` entry pointing at the VM's bridge IP;
   - append the controller certificate to osquery's **own** CA bundle (see the
     gotcha below).
4. Configure the subordinate (`controller-uri`, `controller-env-uuid`,
   `enroll-secret` as a Juju secret, and short logger/config periods) and wait
   for it to go `active`.
5. Assert, reading osctrl's Postgres directly, that the node enrolled and that
   osquery shipped both status logs and scheduled-query result logs, and that
   the recorded node hostname matches the machine's FQDN.

### The osctrl stack

The controller runs in a dedicated LXD **virtual machine** named `osctrl`
(separate from the Juju machines so its lifecycle is managed with `lxc`
directly). Inside the VM, [`provision.sh`](osctrl/provision.sh) installs Docker,
generates a self-signed certificate whose SAN covers `osctrl.lxd` and the VM's
IP, and brings up the [Compose stack](osctrl/docker-compose.yaml):

```text
osquery --443--> nginx --9000--> osctrl-tls --> postgres / redis
```

- Released `jmpsec/osctrl-*` images (version pinned in [`osctrl/.env`](osctrl/.env));
  no local build.
- `nginx` terminates TLS on 443 and proxies the osquery endpoints to `osctrl-tls`
  ([`osctrl-nginx.conf`](osctrl/osctrl-nginx.conf)).
- `osctrl-cli` sits behind a Compose profile and is invoked via
  `docker compose run` for one-off admin commands (create environment, read the
  enrollment secret). Mutating commands need the global `--db` flag.
- The tests read enrolled nodes and osquery logs **straight from Postgres**
  (`osquery_nodes`, `osquery_status_data`, `osquery_result_data`), so no API
  component or auth token is needed.

### VM lifecycle (snapshot reuse)

[`osctrl_manager.py`](osctrl_manager.py) keeps runs fast and deterministic:

- **First use:** launch the VM, provision the stack, then take a *stateless*
  snapshot named `provisioned` of the empty-but-ready controller.
- **Subsequent runs:** restore the `provisioned` snapshot, guaranteeing a clean
  controller with no leftover environments or nodes.
- **`--rebuild-osctrl`:** delete the VM and rebuild from scratch (use this if the
  stack or provisioning changes).

The VM persists between runs; delete it manually with `lxc delete osctrl
--force` if you want a completely clean slate without passing the flag.

### Gotcha: osquery uses its own CA bundle

osquery ships as a statically linked binary and validates TLS against its own
certificate bundle at `/opt/osquery/share/osquery/certs/certs.pem` (a Mozilla
bundle), **not** the system trust store. Installing a CA into the system store
(e.g. `update-ca-certificates`) has no effect on osquery. The test therefore
appends the controller certificate directly to that bundle. In production, a
publicly trusted controller certificate is already present in the bundle and no
machine change is needed.

## Markers

The `osctrl` marker is registered in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
  "osctrl: integration tests that stand up a real osctrl controller in an LXD VM (requires nested virtualisation and Docker Hub access)",
]
```

Select or exclude the osctrl suite with `-m osctrl` / `-m "not osctrl"`.

## Continuous integration

Both suites run on **every pull request** through the shared spread/opcli
workflow ([`../../.github/workflows/integration_test.yaml`](../../.github/workflows/integration_test.yaml),
which calls `canonical/charm-ci`). spread auto-discovers one job per test module
and runs it with the `integration-ci` tox env (no marker filter), so
`test_charm.py` and `test_osctrl.py` each run their own tests.

Because the osctrl job stands up a real controller, the CI runner must expose
`/dev/kvm` (nested virtualisation, to launch the LXD VM) and reach Docker Hub (to
pull the `jmpsec/osctrl-*` images). Standard GitHub-hosted `ubuntu-*` runners
expose `/dev/kvm`.

## Troubleshooting

- **`charm_paths` KeyError / missing artifact:** run `opcli artifacts build`
  first; the fixture reads `artifacts.build.yaml`.
- **osctrl test times out at enrollment:** confirm the VM is reachable at
  `osctrl.lxd:443` from the principal (the test adds the hosts entry) and that
  the controller certificate was appended to osquery's bundle. Check the daemon
  with `journalctl -u osqueryd` on the principal machine — repeated
  `certificate verify failed` means the bundle append did not take effect.
- **Stale controller state:** rerun with `--rebuild-osctrl`, or `lxc delete
  osctrl --force` to force a fresh provision.
- **No `/dev/kvm`:** the osctrl suite cannot launch an LXD VM; run it on a host
  or runner with nested virtualisation enabled.
