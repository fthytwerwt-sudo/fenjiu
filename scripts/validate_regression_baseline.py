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
ALLOWED_DOTENV_EXAMPLES = {".env.example"}
CONTENT_SKIP_PREFIXES = {
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
        "sha256": "c09412d6bd54c1877a600bff4353e807a99ecd81220e08a0a5bb227e03f29f5b",
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


def safe_path_label(path: str) -> str:
    if len(path) > 240:
        return "<path-too-long>"
    if "\0" in path:
        return "<malformed-path>"
    return path


def run_git(root: Path, args: list[str], *, required: bool) -> list[str]:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    if result.returncode != 0:
        if required:
            raise GitCommandError(args)
        return []
    return [line for line in result.stdout.splitlines() if line]


def run_git_z(root: Path, args: list[str], *, required: bool) -> list[str]:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if result.returncode != 0:
        if required:
            raise GitCommandError(args)
        return []
    records = result.stdout.split(b"\0")
    return [os.fsdecode(record) for record in records if record]


def tracked_files(root: Path) -> list[str]:
    return run_git_z(root, ["ls-files", "-z"], required=True)


def parse_porcelain_path(record: str) -> str | None:
    if not record.startswith("!! "):
        return None
    return record[3:]


def ignored_files(root: Path, findings: list[Finding]) -> list[str]:
    try:
        records = run_git_z(
            root,
            ["status", "--porcelain=v1", "-z", "--ignored=matching", "--untracked-files=all"],
            required=True,
        )
    except GitCommandError as error:
        findings.append(Finding("git_scan_failed", "<repository>", f"failed required git command: {error.args_for_display}"))
        return []
    return sorted(path for record in records if (path := parse_porcelain_path(record)))


def changed_files(root: Path, base_sha: str | None, findings: list[Finding]) -> list[str]:
    if not base_sha:
        return []
    try:
        paths = set(run_git_z(root, ["diff", "--name-only", "-z", base_sha, "--"], required=True))
        paths.update(run_git_z(root, ["diff", "--cached", "--name-only", "-z", base_sha, "--"], required=True))
        paths.update(run_git_z(root, ["ls-files", "--others", "--exclude-standard", "-z"], required=True))
    except GitCommandError as error:
        findings.append(Finding("git_scan_failed", "<repository>", f"failed required git command: {error.args_for_display}"))
        return []
    return sorted(paths)


def walk_files(root: Path) -> list[str]:
    paths: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name
            for name in dirnames
            if name not in {".git", ".omx"} and not (Path(dirpath) / name).is_symlink()
        ]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.is_symlink():
                continue
            paths.append(rel_path(root, path))
    return sorted(paths)


def path_is_forbidden(path: str) -> bool:
    parts = set(Path(path).parts)
    name = Path(path).name
    if path in ALLOWED_DOTENV_EXAMPLES:
        return False
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
    if Path(path).name.startswith(".env") and path not in ALLOWED_DOTENV_EXAMPLES:
        return False
    if path == ".git":
        return False
    return not any(path.startswith(prefix) for prefix in CONTENT_SKIP_PREFIXES)


def path_scan_failure(path: str) -> Finding:
    return Finding("path_scan_failed", safe_path_label(path), "path metadata could not be inspected safely")


def scan_paths(paths: Iterable[str], root: Path, *, changed_only: bool, ignored_only: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(set(paths)):
        label = safe_path_label(path)
        try:
            parsed_path = Path(path)
            candidate = root / path
        except (OSError, ValueError):
            findings.append(path_scan_failure(path))
            continue
        if parsed_path.name.startswith("._"):
            findings.append(Finding("appledouble", label, "AppleDouble metadata file is forbidden"))
        try:
            forbidden = path_is_forbidden(path)
        except (OSError, ValueError):
            findings.append(path_scan_failure(path))
            continue
        if forbidden:
            if ignored_only:
                category = "forbidden_ignored_path"
            else:
                category = "forbidden_changed_path" if changed_only else "forbidden_path"
            findings.append(Finding(category, label, "path matches forbidden baseline policy"))
        try:
            if not candidate.is_symlink() and candidate.is_file() and candidate.stat().st_size > 10 * 1024 * 1024:
                findings.append(Finding("large_file", label, "file is larger than 10 MiB"))
        except (OSError, ValueError):
            findings.append(path_scan_failure(path))
    return findings


def read_text_safely(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def is_safe_regular_file(root: Path, candidate: Path) -> bool:
    if candidate.is_symlink() or not candidate.is_file():
        return False
    try:
        root_resolved = root.resolve(strict=True)
        candidate_resolved = candidate.resolve(strict=True)
    except OSError:
        return False
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError:
        return False
    return True


def scan_content(root: Path, paths: Iterable[str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(set(paths)):
        label = safe_path_label(path)
        try:
            allowed = content_scan_allowed(path)
            candidate = root / path
        except (OSError, ValueError):
            findings.append(path_scan_failure(path))
            continue
        if not allowed:
            continue
        if not is_safe_regular_file(root, candidate):
            continue
        text = read_text_safely(candidate)
        if text is None:
            continue
        if ABSOLUTE_PATH_RE.search(text):
            findings.append(Finding("local_absolute_path", label, "local absolute path pattern found"))
        if SECRET_RE.search(text):
            findings.append(Finding("high_confidence_secret", label, "high-confidence secret-like assignment found"))
        if ("fixtures/" in path or "tests/" in path) and FIXTURE_LEAK_RE.search(text):
            findings.append(Finding("fixture_leak", label, "fixture is marked or sourced as real data"))
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
    findings: list[Finding] = []
    if all_files:
        scanned_paths = walk_files(root)
    else:
        try:
            scanned_paths = tracked_files(root)
        except GitCommandError as error:
            findings.append(Finding("git_scan_failed", "<repository>", f"failed required git command: {error.args_for_display}"))
            scanned_paths = walk_files(root)

    findings.extend(scan_paths(scanned_paths, root, changed_only=False))
    findings.extend(scan_content(root, scanned_paths))

    if base_sha:
        ignored = ignored_files(root, findings)
        if ignored:
            findings.extend(scan_paths(ignored, root, changed_only=False, ignored_only=True))

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
