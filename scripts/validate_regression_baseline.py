#!/usr/bin/env python3
"""Dry-safe regression and sensitive-content baseline scanner."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PATH_PARTS = {
    ".env",
    "outputs",
    "raw_local",
    "private",
    "media",
    "renders",
    "research_channels.json",
}
FORBIDDEN_SUFFIXES = {
    ".docx",
    ".xlsx",
    ".xls",
    ".pdf",
    ".mp4",
    ".mov",
    ".m4v",
    ".mp3",
    ".wav",
    ".zip",
}
CONTENT_SKIP_PREFIXES = {
    ".git",
    ".git/",
    ".omx/",
    "project_sync/latest/",
    "project_sync/PROJECT_SYNC_MANIFEST.json",
}
ABSOLUTE_PATH_RE = re.compile(r"(?<![`A-Za-z0-9_])/(Users|Volumes|tmp|private|var)/|[A-Za-z]:\\")
SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password|cookie|authorization)\b\s*[:=]\s*['\"]?([A-Za-z0-9_./+=-]{16,})"
)
FIXTURE_LEAK_RE = re.compile(
    r"(?i)(['\"]?is_synthetic['\"]?\s*[:=]\s*false|['\"]?fixture_source['\"]?\s*[:=]\s*['\"]?real|['\"]?real_fixture['\"]?\s*[:=]\s*true)"
)

LEGACY_BASELINES = {
    "scripts/build_project_sync_pack.py": {
        "sha256": "3db48ced864b80949b67bc6b5b940795269f80461ba2688d5b9d5aac8c2ae605",
        "help_contains": ["--verify"],
    },
    "scripts/validate_gpt_project_mechanism_sync.py": {
        "sha256": "504c7ed887623f2dc8d9629910a244e68f09ba48252e6537a8572e474c7f313e",
        "help_contains": ["--write-manifest", "--no-report"],
    },
}


@dataclass(frozen=True)
class Finding:
    category: str
    path: str
    detail: str


class GitCommandError(RuntimeError):
    def __init__(self, args: list[str]) -> None:
        super().__init__("git command failed")
        self.args_for_display = " ".join(args)


def rel_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def run_git(root: Path, args: list[str], *, required: bool) -> list[str]:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    if result.returncode != 0:
        if required:
            raise GitCommandError(args)
        return []
    return [line for line in result.stdout.splitlines() if line]


def tracked_files(root: Path) -> list[str]:
    return run_git(root, ["ls-files"], required=False)


def changed_files(root: Path, base_sha: str | None, findings: list[Finding]) -> list[str]:
    if not base_sha:
        return []
    try:
        paths = set(run_git(root, ["diff", "--name-only", base_sha, "--"], required=True))
        paths.update(run_git(root, ["diff", "--cached", "--name-only", base_sha, "--"], required=True))
        paths.update(run_git(root, ["ls-files", "--others", "--exclude-standard"], required=True))
    except GitCommandError as error:
        findings.append(Finding("git_command_failed", "<repository>", f"failed required git command: {error.args_for_display}"))
        return []
    return sorted(paths)


def walk_files(root: Path) -> list[str]:
    paths: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in {".git", ".omx"}]
        for filename in filenames:
            path = Path(dirpath) / filename
            paths.append(rel_path(root, path))
    return sorted(paths)


def path_is_forbidden(path: str) -> bool:
    parts = set(Path(path).parts)
    name = Path(path).name
    if name.startswith(".env"):
        return True
    if name.startswith("._"):
        return True
    if name == ".DS_Store":
        return True
    if path.startswith("outputs/"):
        return True
    if any(part in FORBIDDEN_PATH_PARTS for part in parts):
        return True
    return Path(path).suffix.lower() in FORBIDDEN_SUFFIXES


def content_scan_allowed(path: str) -> bool:
    if Path(path).name.startswith(".env"):
        return False
    if path == ".git":
        return False
    return not any(path.startswith(prefix) for prefix in CONTENT_SKIP_PREFIXES)


def scan_paths(paths: Iterable[str], root: Path, *, changed_only: bool) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(set(paths)):
        candidate = root / path
        if Path(path).name.startswith("._"):
            findings.append(Finding("appledouble", path, "AppleDouble metadata file is forbidden"))
        if path_is_forbidden(path):
            category = "forbidden_changed_path" if changed_only else "forbidden_path"
            findings.append(Finding(category, path, "path matches forbidden baseline policy"))
        if candidate.is_file() and candidate.stat().st_size > 10 * 1024 * 1024:
            findings.append(Finding("large_file", path, "file is larger than 10 MiB"))
    return findings


def read_text_safely(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def scan_content(root: Path, paths: Iterable[str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(set(paths)):
        if not content_scan_allowed(path):
            continue
        candidate = root / path
        if not candidate.is_file():
            continue
        text = read_text_safely(candidate)
        if text is None:
            continue
        if ABSOLUTE_PATH_RE.search(text):
            findings.append(Finding("local_absolute_path", path, "local absolute path pattern found"))
        if SECRET_RE.search(text):
            findings.append(Finding("high_confidence_secret", path, "high-confidence secret-like assignment found"))
        if ("fixtures/" in path or "tests/" in path) and FIXTURE_LEAK_RE.search(text):
            findings.append(Finding("fixture_leak", path, "fixture is marked or sourced as real data"))
    return findings


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_legacy_baselines(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel, baseline in LEGACY_BASELINES.items():
        path = root / rel
        if not path.exists():
            findings.append(Finding("legacy_missing", rel, "baseline file is missing"))
            continue
        actual_sha = file_sha256(path)
        if actual_sha != baseline["sha256"]:
            findings.append(Finding("legacy_hash_mismatch", rel, "baseline SHA-256 changed"))
            continue
        result = subprocess.run(
            [sys.executable, rel, "--help"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            findings.append(Finding("legacy_help_failed", rel, "--help returned non-zero"))
            continue
        help_text = result.stdout + result.stderr
        missing = [token for token in baseline["help_contains"] if token not in help_text]
        if missing:
            findings.append(Finding("legacy_help_mismatch", rel, f"missing help tokens: {', '.join(missing)}"))
    return findings


def render_findings(findings: list[Finding]) -> str:
    if not findings:
        return "P00-03 regression baseline validation passed.\n"
    lines = ["P00-03 regression baseline validation failed."]
    for finding in findings:
        lines.append(f"ERROR: {finding.category}: {finding.path}: {finding.detail}")
    return "\n".join(lines) + "\n"


def run_scan(root: Path, *, base_sha: str | None, all_files: bool, legacy: bool) -> list[Finding]:
    if all_files:
        scanned_paths = walk_files(root)
    else:
        scanned_paths = tracked_files(root)
        if not scanned_paths:
            scanned_paths = walk_files(root)

    findings: list[Finding] = []
    findings.extend(scan_paths(scanned_paths, root, changed_only=False))
    findings.extend(scan_content(root, scanned_paths))

    changed = changed_files(root, base_sha, findings)
    if changed:
        findings.extend(scan_paths(changed, root, changed_only=True))

    if legacy:
        findings.extend(validate_legacy_baselines(root))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate dry-safe regression and sensitive scan baseline.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="repository or fixture root to scan")
    parser.add_argument("--base-sha", help="optional base commit used to detect changed forbidden paths")
    parser.add_argument("--all-files", action="store_true", help="scan every file under root instead of git tracked files")
    parser.add_argument("--skip-legacy", action="store_true", help="skip legacy hash and --help baseline checks")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    findings = run_scan(root, base_sha=args.base_sha, all_files=args.all_files, legacy=not args.skip_legacy)
    sys.stdout.write(render_findings(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
