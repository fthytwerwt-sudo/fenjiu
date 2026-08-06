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


if __name__ == "__main__":
    unittest.main()
