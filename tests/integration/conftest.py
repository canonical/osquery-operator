# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for the OSQuery charm integration tests."""

import jubilant
import pytest

# The principal charm the subordinate is related to. The `ubuntu` charm
# provides the implicit `juju-info` interface required by this subordinate.
PRINCIPAL_CHARM = "ubuntu"
# The name of the charm under test, as declared in charmcraft.yaml. This is the
# key used to look up the built charm files in the `charm_paths` fixture.
CHARM_NAME = "osquery"
# The apt package the subordinate installs on the principal's machine.
PACKAGE_NAME = "osquery"
# The systemd service the OSQuery package runs in daemon mode. The subordinate's
# whole purpose is to keep this daemon running on the principal's host.
SERVICE_NAME = "osqueryd"

# The Ubuntu bases the charm supports. The OSQuery PPA publishes packages for
# each of these releases, so the charm is built and tested against all of them.
BASES = ["ubuntu@22.04", "ubuntu@24.04", "ubuntu@26.04"]


@pytest.fixture(scope="module")
def juju(request: pytest.FixtureRequest):
    """Yield a Juju model for the test module.

    When ``--model`` is provided (for example by the spread/charm-ci runner) the
    existing model is reused, otherwise a temporary model is created.

    Args:
        request: the pytest request object.

    Yields:
        A jubilant.Juju instance bound to the model under test.
    """
    model = request.config.getoption("--model")
    if model:
        yield jubilant.Juju(model=model)
        return
    with jubilant.temp_model() as temp:
        yield temp
