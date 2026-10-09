[![CharmHub Badge](https://charmhub.io/osquery/badge.svg)](https://charmhub.io/osquery)
[![Publish to edge](https://github.com/canonical/osquery-operator/actions/workflows/publish_charm.yaml/badge.svg)](https://github.com/canonical/osquery-operator/actions/workflows/publish_charm.yaml)
[![Promote charm](https://github.com/canonical/osquery-operator/actions/workflows/promote_charm.yaml/badge.svg)](https://github.com/canonical/osquery-operator/actions/workflows/promote_charm.yaml)
[![Discourse Status](https://img.shields.io/discourse/status?server=https%3A%2F%2Fdiscourse.charmhub.io&style=flat&label=CharmHub%20Discourse)](https://discourse.charmhub.io)

# osquery operator

A [Juju](https://juju.is/) [charm](https://documentation.ubuntu.com/juju/3.6/reference/charm/)
deploying and managing [osquery](https://www.osquery.io/) on virtual machines and
bare-metal hosts.

<!-- TODO: Replace the upstream link above with a Canonical SecOps osquery
product page once one is available. -->

Osquery exposes an operating system as a high-performance relational database,
letting security and operations teams query the state of a host with SQL. This
charm deploys the Canonical SecOps fork of osquery as a
[subordinate](https://documentation.ubuntu.com/juju/3.6/reference/charm/#subordinate-charm)
agent that runs alongside a principal application on the same machine. It
installs osquery from the [`c-osquery` snap](https://snapcraft.io/c-osquery),
runs it as the `osqueryd` daemon, and connects it over TLS to a centrally managed osquery Controller that supplies
the agent's configuration and collects its logs.

Like any Juju charm, this charm supports one-line deployment, configuration,
integration, and scaling. For osquery, this includes:

- Installing and running the `osqueryd` daemon on any principal machine.
- Translating Juju configuration into the osquery flagfile and reconciling the
  daemon whenever the configuration changes.
- Enrolling the agent with an osquery Controller over TLS, with the enrollment
  secret and client certificates delivered through Juju secrets.

This charm makes operating osquery fleets simple and consistent for security,
DevOps, and SRE teams through Juju's clean interface.

## Get started

The osquery charm is a subordinate charm, so it attaches to a principal
application that occupies the machine. The quickest way to try it out is against
the minimal `ubuntu` principal on a local LXD cloud:

```bash
juju deploy ubuntu --base ubuntu@24.04
juju deploy osquery
juju integrate ubuntu osquery
```

The charm blocks until it's told which osquery Controller to enroll with. See the
[tutorials](https://github.com/canonical/osquery-operator/blob/main/docs/tutorial/index.rst)
for step-by-step instructions, including connecting the agent to a controller.

## Learn more

- [Developer documentation](https://osquery.readthedocs.io/en/latest/)
- [Charm documentation](https://github.com/canonical/osquery-operator/tree/main/docs)
<!-- TODO: Replace the documentation link above with the published documentation
site (Charmhub or Read the Docs) once available. -->
- [Contributing](https://github.com/canonical/osquery-operator/blob/main/CONTRIBUTING.md)

## Documentation

Our documentation is stored in the `docs` directory.
It is based on the Canonical Sphinx Stack
and hosted on [Read the Docs](https://about.readthedocs.com/). In structuring,
the documentation employs the [Diátaxis](https://diataxis.fr/) approach.

You may open a pull request with your documentation changes, or you can
[file a bug](https://github.com/canonical/osquery-operator/issues) to provide constructive feedback or suggestions.

To run the documentation locally before submitting your changes:

```bash
cd docs
make run
```

GitHub runs automatic checks on the documentation
to verify spelling, validate links and style guide compliance.

You can (and should) run the same checks locally:

```bash
make spelling
make linkcheck
make vale
make lint-md
```

## Project and community

The osquery Operator is a member of the Ubuntu family. It's an open-source
project that warmly welcomes community projects, contributions, suggestions,
fixes, and constructive feedback.

- [Code of conduct](https://ubuntu.com/community/code-of-conduct)
- [Get support](https://discourse.charmhub.io/)
- [Join our online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
- [Issue tracker](https://github.com/canonical/osquery-operator/issues)
