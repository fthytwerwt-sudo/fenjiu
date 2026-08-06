from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate_regression_baseline.py"


class RegressionBaselineScannerTests(unittest.TestCase):
    def run_scan(self, files: dict[str, str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--all-files",
                    "--skip-legacy",
                ],
                text=True,
                capture_output=True,
            )

    def run_repo_scan(self, *extra_args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(ROOT),
                "--skip-legacy",
                *extra_args,
            ],
            text=True,
            capture_output=True,
        )

    def git(self, root: Path, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
        return result.stdout.strip()

    def commit_temp_repo(self, root: Path) -> str:
        self.git(root, "init")
        (root / ".gitignore").write_text(".env*\n", encoding="utf-8")
        (root / "README.md").write_text("synthetic fixture repo\n", encoding="utf-8")
        self.git(root, "add", ".gitignore", "README.md")
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=P00-03 Test",
                "-c",
                "user.email=p00-03@example.invalid",
                "commit",
                "-m",
                "baseline",
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
        )
        return self.git(root, "rev-parse", "HEAD")

    def test_clean_synthetic_fixture_passes(self) -> None:
        marker = "is_" + "synthetic"
        result = self.run_scan({"fixtures/demo.json": f'{{"{marker}": true, "business_line_id": "fenjiu_nepal"}}'})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_forbidden_path_fails_without_printing_content(self) -> None:
        secret_value = "SHOULD_NOT_BE_" + "REPORTED_123456"
        secret_assignment = "TOKEN=" + secret_value
        result = self.run_scan({".env": secret_assignment})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forbidden_path", result.stdout)
        self.assertNotIn(secret_value, result.stdout + result.stderr)

    def test_env_local_fails_without_scanning_content(self) -> None:
        key_name = "api_" + "key"
        secret_value = "sk_live_" + "envlocal1234567890abcdef"
        local_path = "/" + "Users/example/private/env.local"
        content = f"{key_name} = {secret_value}\nlocal_path = {local_path}\n"
        result = self.run_scan({".env.local": content})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forbidden_path", result.stdout)
        self.assertNotIn("high_confidence_secret", result.stdout)
        self.assertNotIn("local_absolute_path", result.stdout)
        self.assertNotIn(secret_value, result.stdout + result.stderr)
        self.assertNotIn(local_path, result.stdout + result.stderr)

    def test_ignored_env_in_git_repo_fails_by_path_only(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            base_sha = self.commit_temp_repo(root)
            key_name = "api_" + "key"
            secret_value = "sk_live_" + "ignoredenv1234567890abcdef"
            (root / ".env").write_text(f"{key_name} = {secret_value}\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--base-sha",
                    base_sha,
                    "--skip-legacy",
                ],
                text=True,
                capture_output=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forbidden_ignored_path", result.stdout)
        self.assertNotIn("high_confidence_secret", result.stdout)
        self.assertNotIn(secret_value, result.stdout + result.stderr)

    def test_symlink_outside_root_is_not_read(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as outside_dir:
            root = Path(root_dir)
            secret_value = "sk_live_" + "symlinkoutside1234567890abcdef"
            external = Path(outside_dir) / "external.txt"
            external.write_text("api_" + f"key = {secret_value}\n", encoding="utf-8")
            link = root / "linked.txt"
            try:
                link.symlink_to(external)
            except OSError as error:
                self.skipTest(f"symlink unavailable: {error}")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--all-files",
                    "--skip-legacy",
                ],
                text=True,
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn(secret_value, result.stdout + result.stderr)

    def test_appledouble_fails(self) -> None:
        result = self.run_scan({"docs/._hidden.md": "metadata"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("appledouble", result.stdout)

    def test_local_absolute_path_fails_without_full_value_echo(self) -> None:
        secret_path = "/" + "Users/example/private/project/file.txt"
        result = self.run_scan({"docs/report.md": f"local path: {secret_path}\n"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("local_absolute_path", result.stdout)
        self.assertNotIn(secret_path, result.stdout + result.stderr)

    def test_high_confidence_secret_fails_without_value_echo(self) -> None:
        secret_value = "sk_live_" + "1234567890abcdefghijklmnop"
        key_name = "api_" + "key"
        result = self.run_scan({"docs/report.md": f"{key_name} = {secret_value}\n"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("high_confidence_secret", result.stdout)
        self.assertNotIn(secret_value, result.stdout + result.stderr)

    def test_fixture_marked_real_fails(self) -> None:
        marker = "is_" + "synthetic"
        result = self.run_scan({"tests/fixtures/customer.json": f'{{"{marker}": false}}'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture_leak", result.stdout)

    def test_invalid_base_sha_fails_closed(self) -> None:
        result = self.run_repo_scan("--base-sha", "invalid_base_for_test")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git_scan_failed", result.stdout)


if __name__ == "__main__":
    unittest.main()
