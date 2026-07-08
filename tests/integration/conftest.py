# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for the OSQuery charm integration tests."""

import pathlib

import jubilant
import pytest

# The principal application the subordinate is related to. The `ubuntu` charm
# provides the implicit `juju-info` interface required by this subordinate.
PRINCIPAL_APP = "ubuntu"
OSQUERY_APP = "osquery"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the --charm-file command line option.

    Args:
        parser: the pytest command line parser.
    """
    parser.addoption(
        "--charm-file",
        action="store",
        help="Path to the packed OSQuery charm file under test.",
    )


@pytest.fixture(scope="module")
def charm_file(request: pytest.FixtureRequest) -> str:
    """Return the path to the packed charm under test.

    Args:
        request: the pytest request object.

    Returns:
        The path to the charm file.
    """
    charm = request.config.getoption("--charm-file")
    if charm:
        return str(pathlib.Path(charm).resolve())
    charms = list(pathlib.Path(".").glob("*.charm"))
    assert charms, "no .charm file found; pack the charm or pass --charm-file"
    return str(charms[0].resolve())


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
