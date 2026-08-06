"""Import dependency guard for the P01-01 modular monolith skeleton."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
import subprocess
import tempfile
from typing import Iterable
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROTECTED_DIRS = ("core/domain", "modules")
FILESYSTEM_METADATA_NAMES = {".DS_Store"}
LOCAL_TOP_LEVELS = {"adapters", "apps", "core", "modules", "workflows"}
FORBIDDEN_LOCAL_PREFIXES = (
    "adapters",
    "apps",
    "core.application",
    "core.security",
    "workflows",
)
FORBIDDEN_EXTERNAL_PREFIXES = {
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


def _is_filesystem_metadata(path: Path) -> bool:
    return any(
        part in FILESYSTEM_METADATA_NAMES or part.startswith("._")
        for part in path.parts
    )


def _is_eligible_python_source(path: Path) -> bool:
    if path.suffix != ".py":
        return False
    if _is_filesystem_metadata(path):
        return False
    if path.is_symlink():
        return False
    return path.is_file()


def _iter_eligible_python_sources(root: Path, directories: Iterable[str]) -> Iterable[Path]:
    for directory in directories:
        for path in (root / directory).rglob("*.py"):
            if _is_eligible_python_source(path):
                yield path


def _read_eligible_python_source(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise AssertionError(f"eligible Python source is not UTF-8: {path}") from exc


def _path_to_module(path: Path) -> tuple[str, bool]:
    rel = path.relative_to(ROOT).with_suffix("")
    parts = rel.parts
    if parts[-1] == "__init__":
        return ".".join(parts[:-1]), True
    return ".".join(parts), False


def _source_package(source_module: str, source_is_package: bool) -> str:
    if source_is_package:
        return source_module
    return source_module.rsplit(".", 1)[0]


def _resolve_relative_prefix(
    node: ast.ImportFrom,
    source_module: str,
    source_is_package: bool,
) -> str:
    if node.level == 0:
        return node.module or ""

    package_parts = _source_package(source_module, source_is_package).split(".")
    keep = len(package_parts) - (node.level - 1)
    if keep < 0:
        keep = 0
    prefix_parts = package_parts[:keep]
    if node.module:
        prefix_parts.extend(node.module.split("."))
    return ".".join(part for part in prefix_parts if part)


def _import_targets(
    node: ast.AST,
    source_module: str,
    source_is_package: bool,
) -> set[str]:
    targets: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Import):
            targets.update(alias.name for alias in child.names)
        elif isinstance(child, ast.ImportFrom):
            prefix = _resolve_relative_prefix(child, source_module, source_is_package)
            for alias in child.names:
                if alias.name == "*":
                    targets.add(prefix)
                elif prefix:
                    targets.add(f"{prefix}.{alias.name}")
                else:
                    targets.add(alias.name)
    return targets


def _has_prefix(module_name: str, prefixes: Iterable[str]) -> bool:
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for prefix in prefixes
    )


def _source_module_root(source_module: str) -> str:
    if source_module.startswith("modules."):
        return ".".join(source_module.split(".")[:2])
    if source_module == "core.domain" or source_module.startswith("core.domain."):
        return "core.domain"
    return source_module


def _is_allowed_protected_import(module_name: str, source_module: str) -> bool:
    if not module_name:
        return True

    root = module_name.split(".", 1)[0]
    if _has_prefix(module_name, FORBIDDEN_LOCAL_PREFIXES):
        return False
    if _has_prefix(module_name, FORBIDDEN_EXTERNAL_PREFIXES):
        return False
    if root not in LOCAL_TOP_LEVELS:
        return True
    if module_name == "core.contracts" or module_name.startswith("core.contracts."):
        return True
    if module_name == "core.domain.policies" or module_name.startswith(
        "core.domain.policies."
    ):
        return True

    source_root = _source_module_root(source_module)
    return module_name == source_root or module_name.startswith(f"{source_root}.")


def assert_no_forbidden_imports(
    source: str,
    source_module: str = "core.domain.policies",
    source_is_package: bool = False,
) -> None:
    node = ast.parse(source)
    forbidden = sorted(
        target
        for target in _import_targets(node, source_module, source_is_package)
        if not _is_allowed_protected_import(target, source_module)
    )
    if forbidden:
        raise AssertionError(f"forbidden imports: {', '.join(forbidden)}")


class ImportBoundaryTests(unittest.TestCase):
    def test_skeleton_packages_are_importable(self) -> None:
        for package in IMPORTABLE_PACKAGES:
            with self.subTest(package=package):
                importlib.import_module(package)

    def test_domain_and_modules_do_not_import_outer_layers_or_sdks(self) -> None:
        for path in _iter_eligible_python_sources(ROOT, PROTECTED_DIRS):
            module_name, source_is_package = _path_to_module(path)
            with self.subTest(path=path.relative_to(ROOT)):
                assert_no_forbidden_imports(
                    _read_eligible_python_source(path),
                    source_module=module_name,
                    source_is_package=source_is_package,
                )

    def test_metadata_python_lookalikes_are_skipped_before_decoding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "modules" / "example"
            package.mkdir(parents=True)
            source = package / "__init__.py"
            metadata = package / ".___init__.py"
            source.write_text(
                "from core.application import interfaces\n",
                encoding="utf-8",
            )
            metadata.write_bytes(b"\xff\xfe\x00not utf8")

            sources = list(_iter_eligible_python_sources(root, ("modules",)))
            ordinary_source = source.read_text(encoding="utf-8")

        self.assertEqual([source], sources)
        with self.assertRaises(AssertionError):
            assert_no_forbidden_imports(
                ordinary_source,
                source_module="modules.example",
                source_is_package=True,
            )

    def test_safe_relative_imports_remain_allowed(self) -> None:
        assert_no_forbidden_imports(
            "from . import policies\n",
            source_module="core.domain.rules",
        )
        assert_no_forbidden_imports(
            "from ..contracts import errors\n",
            source_module="core.domain.policies",
        )
        assert_no_forbidden_imports(
            "from . import private_types\n",
            source_module="modules.crm.services",
        )

    def test_reverse_import_assertion_fails_for_outer_layer_import(self) -> None:
        with self.assertRaises(AssertionError):
            assert_no_forbidden_imports("from adapters.video import provider\n")
        with self.assertRaises(AssertionError):
            assert_no_forbidden_imports("from core import application\n")
        with self.assertRaises(AssertionError):
            assert_no_forbidden_imports("from core import security\n")
        with self.assertRaises(AssertionError):
            assert_no_forbidden_imports(
                "from ..application import interfaces\n",
                source_module="core.domain.policies",
            )
        with self.assertRaises(AssertionError):
            assert_no_forbidden_imports(
                "from ..security import auth\n",
                source_module="core.domain.policies",
            )

    def test_reverse_import_assertion_fails_for_provider_sdk_import(self) -> None:
        with self.assertRaises(AssertionError):
            assert_no_forbidden_imports("import requests\n")

    def test_arbitrary_fixture_files_remain_ignored(self) -> None:
        ignored = subprocess.run(
            [
                "git",
                "check-ignore",
                "--no-index",
                "fixtures/unapproved_fixture.json",
            ],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(ignored.returncode, 0, ignored.stderr)

        approved = subprocess.run(
            [
                "git",
                "check-ignore",
                "--no-index",
                "fixtures/synthetic_metadata.json",
            ],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(approved.returncode, 1, approved.stdout)

    def test_external_action_defaults_are_fail_closed(self) -> None:
        from core.application import ExternalActionGuard
        from core.contracts import default_execution_policy

        ExternalActionGuard(default_execution_policy()).assert_no_external_action()
        self.assertFalse(default_execution_policy().external_execution_allowed)
        self.assertFalse(default_execution_policy().business_external_ready)


if __name__ == "__main__":
    unittest.main()
