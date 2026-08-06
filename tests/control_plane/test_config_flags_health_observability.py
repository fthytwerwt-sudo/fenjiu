"""P01-03 config, flags, health, readiness, and log-redaction tests."""

from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from apps.api.local_runtime import HealthHandler
from core.contracts import ExecutionPolicy, default_execution_policy
from core.security import (
    ConfigStatus,
    FailClosedFeatureFlags,
    FeatureFlagName,
    FeatureFlagPort,
    default_settings,
    fail_closed_settings,
)
from observability.health import liveness_payload, readiness_payload
from observability.json_logging import JsonLogEvent, render_json_log, write_json_log

ROOT = Path(__file__).resolve().parents[2]


class SettingsAndFeatureFlagTests(unittest.TestCase):
    def test_settings_do_not_read_environment_or_files(self) -> None:
        with patch("os.getenv", side_effect=AssertionError("environment access forbidden")):
            with patch("builtins.open", side_effect=AssertionError("file access forbidden")):
                settings = default_settings()

        self.assertEqual(settings.config_status, ConfigStatus.STATIC_DISABLED)
        self.assertFalse(settings.is_ready())
        self.assertFalse(settings.broker_available)
        self.assertFalse(settings.provider_available)
        self.assertFalse(settings.real_configuration_available)

    def test_unknown_and_invalid_config_states_fail_closed(self) -> None:
        unknown = fail_closed_settings(ConfigStatus.UNKNOWN_REJECTED)
        invalid = fail_closed_settings(object())

        self.assertEqual(unknown.config_status, ConfigStatus.UNKNOWN_REJECTED)
        self.assertEqual(invalid.config_status, ConfigStatus.INVALID_REJECTED)
        self.assertFalse(unknown.is_ready())
        self.assertFalse(invalid.is_ready())
        self.assertEqual(
            type(default_settings())(config_status="untrusted").config_status,
            ConfigStatus.INVALID_REJECTED,
        )

    def test_feature_flag_port_disables_every_sensitive_action(self) -> None:
        flags = FailClosedFeatureFlags()

        self.assertIsInstance(flags, FeatureFlagPort)
        self.assertEqual(set(flags.snapshot()), {flag.value for flag in FeatureFlagName})
        self.assertTrue(all(value is False for value in flags.snapshot().values()))
        self.assertTrue(all(flags.is_enabled(flag) is False for flag in FeatureFlagName))

    def test_fixture_prompt_and_unknown_values_cannot_override_flags(self) -> None:
        flags = FailClosedFeatureFlags()

        for untrusted in (
            "fixture_enable_external_send",
            "prompt_override_payment",
            "unknown_flag",
            "true",
        ):
            with self.subTest(untrusted=untrusted):
                self.assertFalse(flags.is_enabled(untrusted))

    def test_execution_policy_covers_all_sensitive_actions(self) -> None:
        policy = default_execution_policy()

        self.assertFalse(policy.any_sensitive_action_enabled())
        for field_name in (
            "external_send",
            "public_publish",
            "real_quote",
            "payment",
            "order_create",
            "refund",
            "inventory_writeback",
            "real_crawl",
            "real_video",
            "external_execution_allowed",
            "business_external_ready",
        ):
            self.assertIs(getattr(policy, field_name), False)

    def test_sensitive_policy_values_cannot_be_constructed(self) -> None:
        for field_name in (
            "external_send",
            "public_publish",
            "real_quote",
            "payment",
            "order_create",
            "refund",
            "inventory_writeback",
            "real_crawl",
            "real_video",
            "external_execution_allowed",
            "business_external_ready",
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(ValueError):
                    ExecutionPolicy(**{field_name: True})


class HealthContractTests(unittest.TestCase):
    def test_liveness_is_healthy_and_minimal(self) -> None:
        payload = liveness_payload("api")

        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["live"])
        self.assertEqual(payload["check"], "liveness")
        self.assertNotIn("config", payload)
        self.assertNotIn("scope", payload)
        self.assertNotIn("path", payload)

    def test_readiness_is_fail_closed_without_dependencies(self) -> None:
        payload = readiness_payload("api")

        self.assertEqual(payload["status"], "not_ready")
        self.assertFalse(payload["ready"])
        self.assertEqual(payload["check"], "readiness")
        self.assertEqual(payload["reason_code"], "dependencies_unavailable")
        rendered = json.dumps(payload, sort_keys=True)
        for forbidden in ("broker", "provider", "config_status", "secret", "path"):
            self.assertNotIn(forbidden, rendered)

    def test_component_input_cannot_leak_a_path(self) -> None:
        local_path = "/" + "Users/example/private/service"
        payload = liveness_payload(local_path)

        self.assertEqual(payload["component"], "unknown")
        self.assertNotIn(local_path, json.dumps(payload))

    def test_http_liveness_is_healthy_and_readiness_is_unavailable(self) -> None:
        from http.server import ThreadingHTTPServer

        server = ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]
        try:
            with urlopen(f"http://127.0.0.1:{port}/live", timeout=2) as response:
                live_payload = json.loads(response.read().decode("utf-8"))
            with self.assertRaises(HTTPError) as error:
                urlopen(f"http://127.0.0.1:{port}/ready", timeout=2)
            ready_payload = json.loads(error.exception.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(live_payload["status"], "ok")
        self.assertEqual(error.exception.code, 503)
        self.assertFalse(ready_payload["ready"])


class JsonLogRedactionTests(unittest.TestCase):
    def test_json_log_preserves_correlation_and_safe_metadata(self) -> None:
        event = JsonLogEvent(
            correlation_id="corr-123",
            component="api",
            event="policy.denied",
            result="blocked",
            metadata={"attempt": 1, "policy_code": "flag_disabled"},
        )
        payload = json.loads(render_json_log(event))

        self.assertEqual(payload["correlation_id"], "corr-123")
        self.assertEqual(payload["metadata"]["attempt"], 1)
        self.assertEqual(payload["metadata"]["policy_code"], "flag_disabled")

    def test_message_file_key_cookie_key_and_absolute_path_are_redacted(self) -> None:
        secret_value = "sk_" + "live_" + "redaction_test_value_123456"
        cookie_value = "session=" + "redaction_cookie_value_123456"
        local_path = "/" + "Users/example/private/input.txt"
        event = JsonLogEvent(
            correlation_id="corr-456",
            component="worker",
            event="input.rejected",
            result="blocked",
            metadata={
                "message": "private text " + secret_value,
                "file_name": "private-document.txt",
                "api_key": secret_value,
                "Cookie": cookie_value,
                "source_location": local_path,
                "nested": {"attachment_path": local_path},
            },
        )
        rendered = render_json_log(event)

        for forbidden_value in (secret_value, cookie_value, local_path, "private-document.txt"):
            self.assertNotIn(forbidden_value, rendered)
        payload = json.loads(rendered)
        self.assertEqual(payload["metadata"]["message"], "[REDACTED]")
        self.assertEqual(payload["metadata"]["file_name"], "[REDACTED]")
        self.assertEqual(payload["metadata"]["source_location"], "[REDACTED]")
        self.assertEqual(payload["metadata"]["nested"]["attachment_path"], "[REDACTED]")

    def test_identifier_fields_fail_closed_and_stream_is_json_lines(self) -> None:
        unsafe_correlation = "/" + "Volumes/private/correlation"
        event = JsonLogEvent(
            correlation_id=unsafe_correlation,
            component="api",
            event="health.probe",
            result="ok",
        )
        stream = StringIO()

        write_json_log(stream, event)
        rendered = stream.getvalue()
        payload = json.loads(rendered)

        self.assertTrue(rendered.endswith("\n"))
        self.assertEqual(payload["correlation_id"], "redacted_identifier")
        self.assertNotIn(unsafe_correlation, rendered)

    def test_settings_module_has_no_external_config_loader(self) -> None:
        source = (ROOT / "core/security/settings.py").read_text(encoding="utf-8")

        for forbidden_token in ("os.environ", "getenv(", "read_text(", "secret_reference"):
            self.assertNotIn(forbidden_token, source)


if __name__ == "__main__":
    unittest.main()
