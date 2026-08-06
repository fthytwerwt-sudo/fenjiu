"""Regression tests for P01-02 local-only runtime entrypoints."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from apps.admin import local_runtime as admin_runtime
from apps.api import local_runtime as api_runtime
from apps.api.local_runtime import health_payload

ROOT = Path(__file__).resolve().parents[2]


class LocalRuntimeEntrypointTests(unittest.TestCase):
    def test_health_payload_is_live_without_configuration_details(self) -> None:
        payload = health_payload("api")

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["check"], "liveness")
        self.assertTrue(payload["live"])
        self.assertEqual(payload["capability_status"], "local_control_plane")
        self.assertNotIn("scope", payload)
        self.assertNotIn("config", payload)

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
                self.assertEqual(payload["capability_status"], "local_control_plane")

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

        for target in (
            "bootstrap",
            "dev-up",
            "dev-down",
            "migrate",
            "migration-test",
            "load-fixtures",
            "regression",
        ):
            self.assertIn(f"{target}:", text)
        self.assertIn("WORKTREE_PATH := $(shell pwd -P)", text)
        self.assertIn("cksum", text)
        self.assertIn("COMPOSE_PROJECT_NAME ?= fenjiu-local-runtime-$(COMPOSE_PROJECT_SUFFIX)", text)
        self.assertIn("COMPOSE_CMD = COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) $(COMPOSE) -f $(COMPOSE_FILE)", text)
        self.assertIn("does not install packages or copy .env", text)
        self.assertIn("Apply allowlisted pure SQL migrations", text)
        self.assertIn("psql -X -v ON_ERROR_STOP=1 -h 127.0.0.1", text)
        self.assertIn("sh tests/migrations/run_scope_migration_regression.sh", text)
        self.assertIn("no host ports", text)
        self.assertIn("$(MAKE) compose-config", text)
        self.assertIn("$(MAKE) migration-test", text)

        migration_runner = (
            ROOT / "tests" / "migrations" / "run_scope_migration_regression.sh"
        ).read_text(encoding="utf-8")
        for required_fail_closed_token in (
            'command -v docker',
            'docker compose version',
            'docker info',
            'compose up -d --wait postgres',
            'sh tests/migrations/test_scope_migrations.sh',
            'compose down -v --remove-orphans',
        ):
            self.assertIn(required_fail_closed_token, migration_runner)

        for command in (
            "config --quiet",
            "up -d --wait",
            "exec -T api",
            "exec -T worker",
            "exec -T admin",
            "down",
        ):
            self.assertIn(f"$(COMPOSE_CMD) {command}", text)

    def test_compose_uses_pinned_images_and_no_host_ports(self) -> None:
        text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

        self.assertNotIn("name: fenjiu-local-runtime", text)
        self.assertNotIn("\nname:", text)
        self.assertIn("postgres:16.14-alpine3.24", text)
        self.assertIn("valkey/valkey:8.1.9-alpine3.24", text)
        self.assertIn("python:3.13.9-slim-bookworm", text)
        self.assertNotIn("latest", text)
        self.assertNotIn("ports:", text)
        self.assertIn("expose:", text)
        self.assertIn("postgres_data:", text)
        self.assertIn("valkey_data:", text)

    def test_api_healthcheck_rejects_external_url_before_network(self) -> None:
        with patch.object(sys, "argv", ["api", "--healthcheck", "--url", "http://example.invalid/health"]):
            with patch.object(api_runtime, "urlopen") as mocked_urlopen:
                with self.assertRaises(SystemExit) as error:
                    api_runtime.main()

        self.assertEqual(error.exception.code, 2)
        mocked_urlopen.assert_not_called()

    def test_admin_healthcheck_rejects_external_url_before_network(self) -> None:
        with patch.object(sys, "argv", ["admin", "--healthcheck", "--url", "http://example.invalid/health"]):
            with patch.object(admin_runtime, "urlopen") as mocked_urlopen:
                with self.assertRaises(SystemExit) as error:
                    admin_runtime.main()

        self.assertEqual(error.exception.code, 2)
        mocked_urlopen.assert_not_called()

    def test_healthcheck_urls_are_fixed_loopback_constants(self) -> None:
        self.assertEqual(api_runtime.API_HEALTH_URL, "http://127.0.0.1:8000/health")
        self.assertEqual(admin_runtime.ADMIN_HEALTH_URL, "http://127.0.0.1:8001/health")
        self.assertEqual(api_runtime.API_READINESS_URL, "http://127.0.0.1:8000/ready")
        self.assertEqual(admin_runtime.ADMIN_READINESS_URL, "http://127.0.0.1:8001/ready")


if __name__ == "__main__":
    unittest.main()
