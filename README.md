[![CharmHub Badge](https://charmhub.io/osquery/badge.svg)](https://charmhub.io/osquery)
[![Publish to edge](https://github.com/canonical/osquery-operator/actions/workflows/publish_charm.yaml/badge.svg)](https://github.com/canonical/osquery-operator/actions/workflows/publish_charm.yaml)
[![Promote charm](https://github.com/canonical/osquery-operator/actions/workflows/promote_charm.yaml/badge.svg)](https://github.com/canonical/osquery-operator/actions/workflows/promote_charm.yaml)
[![Discourse Status](https://img.shields.io/discourse/status?server=https%3A%2F%2Fdiscourse.charmhub.io&style=flat&label=CharmHub%20Discourse)](https://discourse.charmhub.io)

# OSQuery operator

A [Juju](https://juju.is/) [charm](https://documentation.ubuntu.com/juju/3.6/reference/charm/)
deploying and managing [OSQuery](https://www.osquery.io/) on virtual machines and
bare-metal hosts.

<!-- TODO: Replace the upstream link above with a Canonical SecOps OSQuery
product page once one is available. -->

OSQuery exposes an operating system as a high-performance relational database,
letting security and operations teams query the state of a host with SQL. This
charm deploys the Canonical SecOps fork of OSQuery as a
[subordinate](https://documentation.ubuntu.com/juju/3.6/reference/charm/#subordinate-charm)
agent that runs alongside a principal application on the same machine. It
installs OSQuery from a Launchpad-hosted PPA, runs it as the `osqueryd` daemon,
and connects it over TLS to a centrally managed OSQuery Controller that supplies
the agent's configuration and collects its logs.

Like any Juju charm, this charm supports one-line deployment, configuration,
integration, and scaling. For OSQuery, this includes:

- Installing and running the `osqueryd` daemon on any principal machine.
- Translating Juju configuration into the OSQuery flagfile and reconciling the
  daemon whenever the configuration changes.
- Enrolling the agent with an OSQuery Controller over TLS, with the enrollment
  secret and client certificates delivered through Juju secrets.

This charm makes operating OSQuery fleets simple and consistent for security,
DevOps, and SRE teams through Juju's clean interface.

## Get started

The OSQuery charm is a subordinate charm, so it attaches to a principal
application that occupies the machine. The quickest way to try it out is against
the minimal `ubuntu` principal on a local LXD cloud:

```bash
juju deploy ubuntu --base ubuntu@24.04
juju deploy osquery
juju integrate ubuntu osquery
```

The charm blocks until it's told which OSQuery Controller to enroll with. See the
[tutorials](https://github.com/canonical/osquery-operator/blob/main/docs/tutorial/index.rst)
for step-by-step instructions, including connecting the agent to a controller.

## Learn more

- * [Developer documentation](https://osquery.readthedocs.io/en/latest/)
- [Charm documentation](https://github.com/canonical/osquery-operator/tree/main/docs)
<!-- TODO: Replace the documentation link above with the published documentation
site (Charmhub or Read the Docs) once available. -->
- [Contributing](https://github.com/canonical/osquery-operator/blob/main/CONTRIBUTING.md)

## Project and community

The OSQuery Operator is a member of the Ubuntu family. It's an open-source
project that warmly welcomes community projects, contributions, suggestions,
fixes, and constructive feedback.

- [Code of conduct](https://ubuntu.com/community/code-of-conduct)
- [Get support](https://discourse.charmhub.io/)
- [Join our online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
- [Issue tracker](https://github.com/canonical/osquery-operator/issues)
