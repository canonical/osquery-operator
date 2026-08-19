# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the config-to-flagfile translation module."""

from collections import OrderedDict

import flags
import osquery


def base_values():
    """Return a values mapping with every option unset (``None``)."""
    names = flags.PLAIN_CONFIGS + flags.SECRET_CONFIGS
    return dict.fromkeys(names)


def valid_values(**overrides):
    """Return a values mapping with the required options set."""
    values = base_values()
    values["controller-uri"] = "controller.example.com"
    values["controller-env-uuid"] = "env-abc"
    values.update(overrides)
    return values


def test_missing_required_reports_both_when_unset():
    assert flags.missing_required(base_values()) == ["controller-uri", "controller-env-uuid"]


def test_missing_required_empty_string_counts_as_missing():
    values = base_values()
    values["controller-uri"] = ""
    values["controller-env-uuid"] = "env"
    assert flags.missing_required(values) == ["controller-uri"]


def test_missing_required_none_when_all_present():
    assert flags.missing_required(valid_values()) == []


def test_controller_uri_expands_to_tls_hostname():
    result = flags.build_flags(valid_values(), "")
    assert result["tls_hostname"] == "controller.example.com:443"


def test_env_uuid_expands_to_every_endpoint():
    result = flags.build_flags(valid_values(), "")
    assert result["enroll_tls_endpoint"] == "/env-abc/enroll"
    assert result["config_tls_endpoint"] == "/env-abc/config"
    assert result["logger_tls_endpoint"] == "/env-abc/log"
    assert result["distributed_tls_read_endpoint"] == "/env-abc/read"
    assert result["distributed_tls_write_endpoint"] == "/env-abc/write"
    assert result["carver_start_endpoint"] == "/env-abc/init"
    assert result["carver_continue_endpoint"] == "/env-abc/block"


def test_one_to_one_option_maps_to_flag():
    result = flags.build_flags(valid_values(**{"host-identifier": "hostname"}), "")
    assert result["host_identifier"] == "hostname"


def test_booleans_render_lowercase():
    result = flags.build_flags(valid_values(**{"force": True, "disable-carver": False}), "")
    assert result["force"] == "true"
    assert result["disable_carver"] == "false"


def test_ints_render_as_strings():
    result = flags.build_flags(valid_values(**{"carver-block-size": 5120000}), "")
    assert result["carver_block_size"] == "5120000"


def test_unset_options_are_omitted():
    result = flags.build_flags(valid_values(), "")
    # alarm-timeout has no charm default, so when unset it must not appear.
    assert "alarm_timeout" not in result


def test_file_backed_flags_point_at_paths():
    values = valid_values(
        **{
            "enroll-secret": "secret",
            "tls-server-certs": "cert",
            "tls-client-cert": "clientcert",
            "tls-client-key": "key",
        }
    )
    result = flags.build_flags(values, "")
    assert result["enroll_secret_path"] == osquery.ENROLL_SECRET_PATH
    assert result["tls_server_certs"] == osquery.SERVER_CERTS_PATH
    assert result["tls_client_cert"] == osquery.CLIENT_CERT_PATH
    assert result["tls_client_key"] == osquery.CLIENT_KEY_PATH


def test_file_backed_flags_omitted_when_unset():
    result = flags.build_flags(valid_values(), "")
    assert "enroll_secret_path" not in result
    assert "tls_client_key" not in result


def test_proxy_hostname_only_when_set():
    assert "proxy_hostname" not in flags.build_flags(valid_values(), "")
    result = flags.build_flags(valid_values(), "http://proxy:3128")
    assert result["proxy_hostname"] == "http://proxy:3128"


def test_render_flagfile_format():
    text = flags.render_flagfile(OrderedDict([("tls_hostname", "h:443"), ("force", "true")]))
    assert text == "--tls_hostname=h:443\n--force=true\n"
