.. meta::
   :description: Learn how to contribute to the OSQuery charm.

.. _how_to_contribute:

How to contribute
=================

This document explains the processes and practices recommended for contributing
enhancements to the OSQuery charm.

.. vale Canonical.013-Spell-out-numbers-below-10 = NO
.. vale Canonical.500-Repeated-words = NO

- Each contribution should focus on a single change. If you're proposing several
  unrelated changes, split them into separate pull requests.
- Use `conventional commits <https://www.conventionalcommits.org/>`_ where
  possible so the history stays readable and changelogs can be generated.
- Before you invest significant effort in a large change, open an issue to
  discuss the design. This helps ensure your work aligns with the project's
  direction.
- Sign off your commits and, where possible, sign them cryptographically.

Overview
--------

The full development workflow — setting up your environment, building and
deploying the charm locally, running the tests, and the code-signing
requirements — is documented in the project's ``CONTRIBUTING.md`` file:

- `CONTRIBUTING.md <https://github.com/canonical/osquery-operator/blob/main/CONTRIBUTING.md>`_

Report issues and request features
----------------------------------

Report bugs and request features on the project's issue tracker:

- `Issue tracker <https://github.com/canonical/osquery-operator/issues>`_

When filing a bug, include the charm revision, the Juju version, and the relevant
output from ``juju status`` and ``juju debug-log``.

Contribute to the documentation
-------------------------------

Documentation is an important part of this project, and we welcome community
contributions. The documentation is written in reStructuredText and built with
Sphinx. The source lives in the ``docs/`` directory of the repository.

.. TODO: Add a link to the rendered documentation site once it's published on
   Read the Docs or Charmhub.

Use of generative AI
--------------------

This project welcomes contributions produced with the assistance of generative
AI tools. If you use such tools, you remain fully responsible for the
contribution: review the output carefully, ensure it's correct and appropriate,
and confirm that it doesn't introduce license or security issues. All the usual
review and testing standards apply regardless of how a change was produced.

Canonical contributor agreement
-------------------------------

Canonical welcomes contributions to the OSQuery charm. Please check out our
`contributor agreement <https://ubuntu.com/legal/contributors>`_ if you're
interested in contributing to the solution.
