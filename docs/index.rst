.. meta::
   :description: Discover the osquery charm, a Juju operator that deploys and manages the osquery endpoint security monitoring agent.

.. vale Canonical.007-Headings-sentence-case = NO

.. _index:

osquery operator
================

Hello this is a fake change

.. vale Canonical.007-Headings-sentence-case = YES

A `Juju <https://juju.is/>`_ :ref:`charm <juju:charm>`
deploying and managing `osquery <https://www.osquery.io/>`_ on virtual machines and bare-metal hosts.

.. TODO: Replace the upstream link above if a Canonical SecOps osquery product
   page becomes available.

Osquery exposes an operating system as a high-performance relational database,
letting security and operations teams query the state of a host with SQL. This
charm deploys the Canonical SecOps fork of osquery as a
:ref:`subordinate <juju:subordinate-charm>`
agent that runs alongside a principal application on the same machine. It
installs osquery from the `c-osquery snap <https://snapcraft.io/c-osquery>`_,
runs it in daemon mode, and connects it over TLS to a centrally managed osquery Controller that supplies the
agent's configuration and collects its logs.

Like any Juju charm, this charm supports one-line deployment, configuration,
integration, scaling, and more. For osquery, this includes:

* Installing and running the ``osqueryd`` daemon on any principal machine.
* Translating Juju configuration into the osquery flagfile and reconciling the
  daemon whenever the configuration changes.
* Enrolling the agent with an osquery Controller over TLS, with the enrollment
  secret and client certificates delivered through Juju secrets.

This charm makes operating osquery fleets simple and consistent for security,
DevOps, and SRE teams through Juju's clean interface.

In this documentation
---------------------

.. list-table::
    :header-rows: 1

    * -
      -
    * - Get started
      - :ref:`Deploy the osquery charm <tutorial_basic_deployment>` | :ref:`Enroll an osquery Controller <tutorial_advanced_deployment>`
    * - Deployment
      - :ref:`Configurations <reference_configurations>` | :ref:`Relation endpoints <reference_relation_endpoints>`
    * - Operations
      - :ref:`Upgrade <how_to_upgrade>` | :ref:`Redeploy <how_to_redeploy>` | :ref:`Back up and restore <how_to_back_up_restore>` | :ref:`Troubleshoot <how_to_troubleshoot>` | :ref:`Metrics <reference_metrics>` | :ref:`Terraform <how_to_terraform>`
    * - Design
      - :ref:`Architecture <reference_charm_architecture>` | :ref:`Design <explanation_charm_design>`
    * - Security
      - :ref:`Overview <explanation_security>` | :ref:`Cryptography <reference_cryptographic_overview>`

How this documentation is organized
------------------------------------

This documentation uses the `Diátaxis documentation structure <https://diataxis.fr/>`_.

- The :ref:`Tutorial <tutorial_index>` takes you step-by-step through a basic deployment of the osquery charm.
- :ref:`How-to guides <how_to_index>` assume you have basic familiarity with the osquery charm. Learn more about setting up, using, maintaining, and contributing to this charm.
- :ref:`Reference <reference_index>` provides a guide to configurations, relations, and other technical details.
- :ref:`Explanation <explanation_index>` includes topic overviews, background and context and detailed discussion.
- :ref:`Release notes <release_notes_index>` holds all the release notes for the charm, including any system or upgrade requirements.

Contributing to this documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Documentation is an important part of this project, and we take the same open-source approach
to the documentation as the code. As such, we welcome community contributions, suggestions, and
constructive feedback on our documentation.
See :ref:`How to contribute <how_to_contribute>` for more information.

If there's a particular area of documentation that you'd like to see that's missing, please
`file a bug <https://github.com/canonical/osquery-operator/issues>`_.

Project and community
---------------------

The osquery Operator is a member of the Ubuntu family. It's an open-source project that warmly welcomes community
projects, contributions, suggestions, fixes, and constructive feedback.

Governance and policies
^^^^^^^^^^^^^^^^^^^^^^^^

- `Code of conduct <https://ubuntu.com/community/code-of-conduct>`_

Get involved
^^^^^^^^^^^^

- `Get support <https://discourse.charmhub.io/>`_
- `Join our online chat <https://matrix.to/#/#charmhub-charmdev:ubuntu.com>`_
- :ref:`Contribute <how_to_contribute>`

Releases
^^^^^^^^

- :ref:`Release notes <release_notes_index>`

Thinking about using the osquery Operator for your next project?
`Get in touch <https://matrix.to/#/#charmhub-charmdev:ubuntu.com>`_!

.. vale Canonical.013-Spell-out-numbers-below-10 = NO
.. vale Canonical.500-Repeated-words = NO

.. toctree::
    :hidden:
    :maxdepth: 1

    Tutorial <tutorial/index>
    How-to guides <how-to/index>
    Reference <reference/index>
    Explanation <explanation/index>
    Release notes <release-notes/index>
