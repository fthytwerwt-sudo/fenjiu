"""Regression tests for P01-02 local-only runtime entrypoints."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from apps.api.local_runtime import health_payload

ROOT = Path(__file__).resolve().parents[2]


class LocalRuntimeEntrypointTests(unittest.TestCase):
    def test_health_payload_is_fail_closed_and_synthetic(self) -> None:
        payload = health_payload("api")

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["capability_status"], "local_only")
        self.assertFalse(payload["external_send"])
        self.assertFalse(payload["public_publish"])
        self.assertFalse(payload["real_quote"])
        self.assertFalse(payload["payment"])
        self.assertFalse(payload["order_create"])
        self.assertFalse(payload["refund"])
        self.assertFalse(payload["external_execution_allowed"])
        self.assertFalse(payload["business_external_ready"])
        self.assertEqual(payload["scope"]["business_line_id"], "synthetic_business_line")

    def test_worker_noop_commands_do_not_write_or_load(self) -> None:
        for flag in ("--migrate-noop", "--load-fixtures-noop", "--healthcheck"):
            with self.subTest(flag=flag):
                result = subprocess.run(
                    [sys.executable, "-m", "apps.worker.local_runtime", flag],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=True,
                )
                payload = json.loads(result.stdout)
                self.assertFalse(payload["writes_data"])
                self.assertFalse(payload["loads_fixtures"])
                self.assertFalse(payload["external_execution_allowed"])

    def test_env_example_contains_only_local_placeholders(self) -> None:
        text = (ROOT / ".env.example").read_text(encoding="utf-8")

        self.assertIn("LOCAL_ONLY_PLACEHOLDER", text)
        self.assertNotIn("sk_", text)
        self.assertNotIn("http://", text)
        self.assertNotIn("https://", text)
        self.assertIn("FENJIU_EXTERNAL_EXECUTION_ALLOWED=false", text)
        self.assertIn("FENJIU_BUSINESS_EXTERNAL_READY=false", text)

    def test_makefile_documents_safe_targets(self) -> None:
        text = (ROOT / "Makefile").read_text(encoding="utf-8")

        for target in ("bootstrap", "dev-up", "dev-down", "migrate", "load-fixtures", "regression"):
            self.assertIn(f"{target}:", text)
        self.assertIn("does not install packages or copy .env", text)
        self.assertIn("Safe no-op migration probe", text)
        self.assertIn("no host ports", text)

    def test_compose_uses_pinned_images_and_no_host_ports(self) -> None:
        text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

        self.assertIn("postgres:16.14-alpine3.24", text)
        self.assertIn("valkey/valkey:8.1.9-alpine3.24", text)
        self.assertIn("python:3.13.9-slim-bookworm", text)
        self.assertNotIn("latest", text)
        self.assertNotIn("ports:", text)
        self.assertIn("expose:", text)
        self.assertIn("postgres_data:", text)
        self.assertIn("valkey_data:", text)


if __name__ == "__main__":
    unittest.main()
