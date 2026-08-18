.. meta::
   :description: Reference documentation for the configuration options of the OSQuery charm.

.. _reference_configurations:

Configurations
==============

The OSQuery charm is configured entirely through Juju configuration options.
The charm doesn't use cross-charm relations for configuration: you set options with
``juju config`` and the charm applies them.

How configurations are applied
------------------------------

On every configuration change the charm:

#. Resolves each option (including any referenced Juju secrets)
#. Writes the file-backed options (enrollment secret and TLS material) to disk
   with strict ownership and permissions
#. Renders the OSQuery flagfile to ``/etc/osquery/osquery.flags``
#. Enables and restarts the ``osqueryd`` service so the new flags take effect

The flagfile is the `OSQuery flagfile
<https://osquery.readthedocs.io/en/stable/installation/cli-flags/#flagfile>`_.
Each charm option maps to one or more OSQuery command-line flags. Unset options that
have no charm default are omitted from the flagfile, so
OSQuery falls back to its own built-in defaults.

Required options
----------------

Two options must be set before the charm can build a working flagfile. Until
both are set the unit reports ``blocked`` with a message naming the missing
options.

``controller-uri``
   Hostname of the OSQuery Controller. It sets ``--tls_hostname`` to
   ``<controller-uri>:443``.

``controller-env-uuid``
   UUID of the environment on the controller. A single value expands into every
   per-environment TLS endpoint flag:

   .. list-table::
      :header-rows: 1

      * - Flag
        - Value
      * - ``--enroll_tls_endpoint``
        - ``/<uuid>/enroll``
      * - ``--config_tls_endpoint``
        - ``/<uuid>/config``
      * - ``--logger_tls_endpoint``
        - ``/<uuid>/log``
      * - ``--distributed_tls_read_endpoint``
        - ``/<uuid>/read``
      * - ``--distributed_tls_write_endpoint``
        - ``/<uuid>/write``
      * - ``--carver_start_endpoint``
        - ``/<uuid>/init``
      * - ``--carver_continue_endpoint``
        - ``/<uuid>/block``

File-backed options
-------------------

Some options carry file contents rather than a scalar value. The charm writes
the content to a well-known path and points the matching flag at it. Secret
material (the enrollment secret and the client key) is written as a
``root``-owned file with ``600`` permissions, inside a ``root``-owned directory
with ``700`` permissions.

.. list-table::
   :header-rows: 1

   * - Option
     - Type
     - Path
     - Flag
   * - ``enroll-secret``
     - secret
     - ``/etc/osquery/enroll.secret``
     - ``--enroll_secret_path``
   * - ``tls-server-certs``
     - string
     - ``/etc/osquery/certs/server-ca.pem``
     - ``--tls_server_certs``
   * - ``tls-client-cert``
     - string
     - ``/etc/osquery/certs/client-ca.pem``
     - ``--tls_client_cert``
   * - ``tls-client-key``
     - secret
     - ``/etc/osquery/certs/client-key.pem``
     - ``--tls_client_key``

.. _configurations_secrets:

Providing secrets
-----------------

The ``enroll-secret`` and ``tls-client-key`` options are of Juju type
``secret``, so their values are supplied as Juju user secrets rather than as
plaintext configuration. Create the secret with a single field named after the
option, grant it to the application, and set the option to the secret's URI:

.. code-block:: bash

   secret_id=$(juju add-secret osquery-enroll enroll-secret#file=enroll.secret)
   juju grant-secret osquery-enroll osquery
   juju config osquery enroll-secret="$secret_id"

The charm reads the value from the field named after the option (for example
``enroll-secret``). For convenience, a secret that exposes exactly one field is
also accepted regardless of the field's name. If a referenced secret cannot be
accessed (for example, if it wasn't granted to the application), the unit reports
``blocked``.

One-to-one options
------------------

The remaining options map directly to a single flag of the same name, with
dashes replaced by underscores (for example, ``carver-block-size`` sets
``--carver_block_size``). Options that have a charm default are always passed
to the OSQuery workload. Options without a default are only passed once the
user sets them to a specific value.

The following table lists all one-to-one options. Please refer to the `OSQuery flagfile
<https://osquery.readthedocs.io/en/stable/installation/cli-flags/#flagfile>`_ for the
meaning of each flag.

.. list-table::
   :header-rows: 1

   * - Option
     - Type
     - Default
     - Flag
   * - ``alarm-timeout``
     - int
     -
     - ``--alarm_timeout``
   * - ``carver-block-size``
     - int
     - ``5120000``
     - ``--carver_block_size``
   * - ``carver-compression``
     - boolean
     -
     - ``--carver_compression``
   * - ``carver-disable-function``
     - boolean
     - ``false``
     - ``--carver_disable_function``
   * - ``config-accelerated-refresh``
     - int
     -
     - ``--config_accelerated_refresh``
   * - ``config-check``
     - boolean
     -
     - ``--config_check``
   * - ``config-dump``
     - boolean
     -
     - ``--config_dump``
   * - ``config-plugin``
     - string
     - ``tls``
     - ``--config_plugin``
   * - ``config-enable-backup``
     - boolean
     -
     - ``--config_enable_backup``
   * - ``config-refresh``
     - int
     - ``300``
     - ``--config_refresh``
   * - ``config-tls-max-attempts``
     - int
     - ``5``
     - ``--config_tls_max_attempts``
   * - ``database-dump``
     - boolean
     -
     - ``--database_dump``
   * - ``disable-carver``
     - boolean
     - ``false``
     - ``--disable_carver``
   * - ``disable-distributed``
     - boolean
     - ``false``
     - ``--disable_distributed``
   * - ``disable-enrollment``
     - boolean
     -
     - ``--disable_enrollment``
   * - ``disable-reenrollment``
     - boolean
     -
     - ``--disable_reenrollment``
   * - ``disable-watchdog``
     - boolean
     -
     - ``--disable_watchdog``
   * - ``distributed-interval``
     - int
     - ``60``
     - ``--distributed_interval``
   * - ``distributed-plugin``
     - string
     - ``tls``
     - ``--distributed_plugin``
   * - ``distributed-tls-max-attempts``
     - int
     - ``5``
     - ``--distributed_tls_max_attempts``
   * - ``enable-signal-handler``
     - boolean
     -
     - ``--enable_signal_handler``
   * - ``enroll-always``
     - boolean
     -
     - ``--enroll_always``
   * - ``force``
     - boolean
     - ``true``
     - ``--force``
   * - ``host-identifier``
     - string
     - ``uuid``
     - ``--host_identifier``
   * - ``logger-plugin``
     - string
     - ``tls``
     - ``--logger_plugin``
   * - ``logger-stderr``
     - boolean
     -
     - ``--logger_stderr``
   * - ``logger-tls-compress``
     - boolean
     - ``true``
     - ``--logger_tls_compress``
   * - ``logger-tls-period``
     - int
     - ``600``
     - ``--logger_tls_period``
   * - ``tls-enroll-max-attempts``
     - int
     -
     - ``--tls_enroll_max_attempts``
   * - ``tls-session-reuse``
     - boolean
     -
     - ``--tls_session_reuse``
   * - ``tls-session-timeout``
     - int
     -
     - ``--tls_session_timeout``
   * - ``watchdog-delay``
     - int
     -
     - ``--watchdog_delay``
   * - ``watchdog-level``
     - int
     -
     - ``--watchdog_level``
   * - ``watchdog-memory-limit``
     - int
     -
     - ``--watchdog_memory_limit``
   * - ``watchdog-utilization-limit``
     - int
     -
     - ``--watchdog_utilization_limit``

Hardcoded flags
---------------

Some flags are always managed by the charm and are not exposed as options:

``--proxy_hostname``
   Set to the value of the ``JUJU_CHARM_HTTPS_PROXY`` environment variable that
   Juju exposes to the charm when the model has an HTTPS proxy configured. It is
   only emitted when a proxy is configured, so OSQuery routes its outbound TLS
   traffic through it.

.. note::

   ``config-plugin``, ``distributed-plugin`` and ``logger-plugin`` all default
   to ``tls`` through their respective options, matching the controller-driven
   deployment model.

Keeping the option list up to date
----------------------------------

The set of supported flags is derived systematically from the OSQuery fork's
source. The ``scripts/extract_flags.py`` helper scans the source tree and
exports every flag definition (along with whether it is a plugin flag,
remote-configurable, or shell-only) to a CSV. Re-run the script whenever the OSQuery
version is bumped to review any newly added flags:

.. code-block:: bash

   python3 scripts/extract_flags.py --root /path/to/osquery --output flags.csv

.. seealso::

   Read more about configurations in the Juju docs: `Configuration
   <https://canonical.com/juju/docs/juju-cli/latest/reference/configuration/>`_

