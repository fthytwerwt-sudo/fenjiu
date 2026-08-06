"""Import dependency guard for the P01-01 modular monolith skeleton."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROTECTED_DIRS = ("core/domain", "modules")
FORBIDDEN_TOP_LEVELS = {"adapters", "apps", "workflows"}
FORBIDDEN_MODULES = {
    "boto3",
    "celery",
    "crawl4ai",
    "django",
    "fastapi",
    "flask",
    "httpx",
    "langchain",
    "langgraph",
    "openai",
    "os",
    "pydantic",
    "requests",
    "sqlalchemy",
    "starlette",
}

IMPORTABLE_PACKAGES = (
    "apps.api",
    "apps.admin",
    "apps.worker",
    "core.application",
    "core.contracts",
    "core.domain",
    "core.security",
    "modules.truth_center",
    "modules.ingestion",
    "modules.leads",
    "modules.crm",
    "modules.customer_service",
    "modules.content_video",
    "adapters.storage",
    "adapters.database",
    "adapters.queue",
    "adapters.ai",
    "adapters.crawl",
    "adapters.crm",
    "adapters.support",
    "adapters.video",
    "workflows",
)


def _import_roots(node: ast.AST) -> set[str]:
    roots: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in child.names)
        elif isinstance(child, ast.ImportFrom) and child.module:
            roots.add(child.module.split(".", 1)[0])
    return roots


def assert_no_forbidden_imports(source: str) -> None:
    node = ast.parse(source)
    forbidden = sorted((_import_roots(node) & FORBIDDEN_TOP_LEVELS) | (_import_roots(node) & FORBIDDEN_MODULES))
    if forbidden:
        raise AssertionError(f"forbidden imports: {', '.join(forbidden)}")


class ImportBoundaryTests(unittest.TestCase):
    def test_skeleton_packages_are_importable(self) -> None:
        for package in IMPORTABLE_PACKAGES:
            with self.subTest(package=package):
                importlib.import_module(package)

    def test_domain_and_modules_do_not_import_outer_layers_or_sdks(self) -> None:
        for directory in PROTECTED_DIRS:
            for path in (ROOT / directory).rglob("*.py"):
                with self.subTest(path=path.relative_to(ROOT)):
                    assert_no_forbidden_imports(path.read_text(encoding="utf-8"))

    def test_reverse_import_assertion_fails_for_outer_layer_import(self) -> None:
        with self.assertRaises(AssertionError):
            assert_no_forbidden_imports("from adapters.video import provider\n")

    def test_reverse_import_assertion_fails_for_provider_sdk_import(self) -> None:
        with self.assertRaises(AssertionError):
            assert_no_forbidden_imports("import requests\n")

    def test_external_action_defaults_are_fail_closed(self) -> None:
        from core.application import ExternalActionGuard
        from core.contracts import default_execution_policy

        ExternalActionGuard(default_execution_policy()).assert_no_external_action()
        self.assertFalse(default_execution_policy().external_execution_allowed)
        self.assertFalse(default_execution_policy().business_external_ready)


if __name__ == "__main__":
    unittest.main()
