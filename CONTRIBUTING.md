# Contributing

This document explains the processes and practices recommended for contributing
enhancements to the OSQuery charm.

- Generally, before developing enhancements to this charm, you should consider
  [opening an issue](https://github.com/canonical/osquery-operator/issues)
  explaining your use case.
- If you would like to chat with us about your use cases or proposed
  implementation, you can reach us at
  [Charmhub Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com).
- Familiarizing yourself with the
  [Charmed Operator Framework](https://ops.readthedocs.io/en/latest/) library
  will help you a lot when working on new features or bug fixes.
- All enhancements require review before being merged. Code review typically
  examines code quality, test coverage, and user experience for Juju operators of
  this charm.
- When evaluating design decisions, we optimize for the following personas, in
  descending order of priority: charm users, charm operators, and charm
  developers.
- Please help us out in ensuring easy to review branches by rebasing your pull
  request branch onto the `main` branch. This also avoids merge commits and
  creates a linear Git commit history.

## Use of generative AI

This project welcomes contributions produced with the assistance of generative
AI tools. If you use such tools, you remain fully responsible for the
contribution: review the output carefully, make sure it's correct and
appropriate, and confirm that it doesn't introduce license or security issues.
All the usual review and testing standards apply regardless of how a change was
produced.

## Developing

The OSQuery charm is a subordinate machine charm. To make contributions to this
charm, you'll need a working [development setup](https://documentation.ubuntu.com/juju/3.6/howto/manage-your-deployment/).

The code for this charm can be downloaded as follows:

```bash
git clone https://github.com/canonical/osquery-operator.git
```

You can use the environments created by `tox` for development. For example, to
load the `unit` environment into your shell, run:

```bash
tox --notest -e unit
source .tox/unit/bin/activate
```

### Testing

This project uses `tox` for managing test environments. There are some
pre-configured environments that can be used for linting and formatting code when
you're preparing contributions to the charm:

```bash
tox run -e fmt          # update your code according to linting rules
tox run -e lint         # code style
tox run -e unit         # unit tests
tox run -e static       # static type and security checks
tox run -e integration  # integration tests
tox                     # runs 'lint' and 'unit' environments
```

## Build the charm

Build the charm in this git repository using:

```bash
charmcraft pack
```

## Deploy this charm

Because this is a subordinate charm, it must be integrated with a principal
application that occupies the machine. The following deploys the freshly built
charm against the minimal `ubuntu` principal:

```bash
# Create a working model
juju add-model test-osquery

# Deploy a principal application for the subordinate to attach to
juju deploy ubuntu --base ubuntu@24.04

# Deploy the locally built charm
juju deploy ./osquery_*.charm

# Integrate the subordinate with the principal
juju integrate ubuntu osquery
```

The charm blocks until it's configured with an OSQuery Controller. See the
[tutorial](docs/tutorial/index.rst) for the full configuration.

## Canonical contributor agreement

Canonical welcomes contributions to the OSQuery charm. Please check out our
[contributor agreement](https://ubuntu.com/legal/contributors) if you're
interested in contributing to the solution.

## Signing commits

To improve contribution tracking, we use the developer certificate of origin
([DCO 1.1](https://developercertificate.org/)) and require a "sign-off" for any
changes going into each branch.

The sign-off is a simple line at the end of the explanation for the commit,
certifying that you wrote it or otherwise have the right to pass it on as an
open-source contribution.

Assuming your name is `John Doe` and your email address is `johndoe@example.com`,
just include the following line at the bottom of your commit message, with your
details:

```
Signed-off-by: John Doe <johndoe@example.com>
```

You can sign off your commit automatically with `git commit -s` when you commit
your changes.

We also encourage you to sign your commits cryptographically. See the
[GitHub documentation on signing commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits)
for details.
