#!/usr/bin/env python3
"""生成汾酒项目的轻量、可交接同步包。

只使用 Python 标准库。同步包采用严格 allowlist：它传递项目的协作上下文，
而不是备份整个工作目录。这样可以避免把媒体、QA、线索库和秘密信息交给新会话。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Iterable
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SYNC_ROOT = ROOT / "project_sync"
LATEST_DIR = SYNC_ROOT / "latest"
DIST_DIR = ROOT / "dist"
MAX_SYNC_FILE_BYTES = 1 * 1024 * 1024
PACKAGE_NAME_PREFIX = "fenjiu_project_sync_pack"
MANIFEST_SCHEMA_VERSION = 2

# 这些文件是同步包唯一允许复制的源文件。业务原件只在事实源地图中被定位，
# 不被默认复制到新会话，避免意外披露和上下文膨胀。
ALLOWLIST = (
    "AGENTS.md",
    "README.md",
    "PROJECT_ENTRY.md",
    "docs/project/PROJECT_GOAL.md",
    "docs/project/BUSINESS_STATUS.md",
    "docs/project/CURRENT_STATUS.md",
    "docs/project/SCOPE_AND_BOUNDARIES.md",
    "docs/project/DECISIONS.md",
    "docs/project/OPEN_QUESTIONS.md",
    "docs/project/RISKS_AND_BLOCKERS.md",
    "docs/project/NEXT_ACTIONS.md",
    "docs/project/SOURCE_OF_TRUTH.md",
    "docs/collaboration/CHATGPT_CODEX_WORKFLOW.md",
    "docs/collaboration/COLLABORATION_STATUS.md",
    "docs/collaboration/TASK_HANDOFF_TEMPLATE.md",
    "docs/collaboration/SESSION_HANDOFF_TEMPLATE.md",
    "docs/collaboration/EXECUTION_REPORT_TEMPLATE.md",
    "docs/collaboration/EXECUTION_HISTORY.md",
    "docs/collaboration/collaboration_mechanism_adoption.md",
    "docs/sync/README.md",
    "project_sync/PROJECT_SYNC_README.md",
    "scripts/build_project_sync_pack.py",
)

EXPECTED_PACKAGE_FILES = {
    "PROJECT_SYNC_README.md",
    "PROJECT_CONTEXT.md",
    "BUSINESS_STATUS.md",
    "CURRENT_STATUS.md",
    "COLLABORATION_STATUS.md",
    "DECISIONS.md",
    "OPEN_QUESTIONS.md",
    "RISKS_AND_BLOCKERS.md",
    "NEXT_ACTIONS.md",
    "SOURCE_OF_TRUTH.md",
    "AGENTS.md",
    "FILE_INDEX.md",
    "GIT_STATE.md",
    "PROJECT_SYNC_MANIFEST.json",
}

SECRET_FILENAME_PARTS = (
    ".env",
    "credential",
    "secret",
    "password",
    "passwd",
    "token",
    "cookie",
    "api_key",
    "apikey",
)
EXCLUDED_DIR_PARTS = {
    ".git",
    ".omx",
    "node_modules",
    "__pycache__",
    "qa",
    "output",
    "outputs",
}
EXCLUDED_SUFFIXES = {
    ".mp4",
    ".mov",
    ".wav",
    ".mp3",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".pdf",
    ".pyc",
    ".zip",
}
TEXT_SUFFIXES = {".md", ".py", ".json", ".txt", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
LOCAL_ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9])/(?:Users|Volumes)(?:/|$)"),
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]"),
)
HIGH_CONFIDENCE_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,})\b"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|passwd|access[_-]?token|auth[_-]?token)\b\s*[:=]\s*[\"']?([A-Za-z0-9_./+=-]{16,})"
    ),
)
SAFE_PLACEHOLDERS = {"example", "placeholder", "your_key", "your-api-key", "replace_me", "changeme", "<redacted>"}
SOURCE_GIT_FIELDS = {
    "branch",
    "source_commit",
    "short_source_commit",
    "worktree_status",
    "remote_origin",
}


class SyncPackError(RuntimeError):
    """可由用户理解的同步包失败。"""


def git_value(*args: str) -> str:
    """读取 Git 信息；空仓库和非 Git 场景使用明确占位符。"""

    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return "unavailable"
    return completed.stdout.strip() or "unavailable"


def git_worktree_status() -> str:
    """返回安全状态词，不把未跟踪文件名写入同步包。"""

    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return "unavailable"
    return "dirty" if completed.stdout.strip() else "clean"


def sanitize_remote_origin(remote: str) -> str:
    """将 Git 远端归一为不含凭据、查询参数或本机路径的 HTTPS URL。"""

    if remote == "unavailable":
        return remote

    candidate = remote.strip()
    scp_style = re.fullmatch(r"(?:[^@/\s]+@)?([^:/\s]+):(.+)", candidate)
    if scp_style:
        host, path = scp_style.groups()
    else:
        parsed = urlsplit(candidate)
        if parsed.scheme not in {"http", "https", "ssh"} or not parsed.hostname:
            return "unavailable"
        host, path = parsed.hostname, parsed.path

    segments = [segment for segment in path.split("/") if segment]
    if len(segments) != 2 or not all(re.fullmatch(r"[A-Za-z0-9._-]+", segment) for segment in segments):
        return "unavailable"
    return f"https://{host}/{segments[0]}/{segments[1]}"


def git_state() -> dict[str, str]:
    return {
        "branch": git_value("branch", "--show-current"),
        "source_commit": git_value("rev-parse", "HEAD"),
        "short_source_commit": git_value("rev-parse", "--short", "HEAD"),
        "worktree_status": git_worktree_status(),
        "remote_origin": sanitize_remote_origin(git_value("remote", "get-url", "origin")),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def contains_secret(path: Path) -> str | None:
    """只扫描 allowlist 的文本文件；返回命中的规则说明，不回显内容。"""

    if path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    content = read_text(path)
    for pattern in HIGH_CONFIDENCE_SECRET_PATTERNS:
        match = pattern.search(content)
        if not match:
            continue
        candidate = match.group(1) if match.lastindex else match.group(0)
        if candidate.strip().lower() not in SAFE_PLACEHOLDERS:
            return f"疑似秘密匹配规则：{pattern.pattern[:48]}..."
    return None


def contains_local_absolute_path(path: Path) -> str | None:
    """阻止本机路径随 allowlist 文件进入可跨机器使用的同步包。"""

    if path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    content = read_text(path)
    for pattern in LOCAL_ABSOLUTE_PATH_PATTERNS:
        if pattern.search(content):
            return "包含本机绝对路径"
    return None


def validate_allowlist() -> list[Path]:
    files: list[Path] = []
    failures: list[str] = []
    for relative in ALLOWLIST:
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"缺少 allowlist 文件：{relative}")
            continue
        if path.stat().st_size > MAX_SYNC_FILE_BYTES:
            failures.append(f"同步文件超过 {MAX_SYNC_FILE_BYTES // 1024 // 1024} MiB：{relative}")
            continue
        secret_reason = contains_secret(path)
        if secret_reason:
            failures.append(f"拒绝打包 {relative}：{secret_reason}")
            continue
        path_reason = contains_local_absolute_path(path)
        if path_reason:
            failures.append(f"拒绝打包 {relative}：{path_reason}")
            continue
        files.append(path)
    if failures:
        raise SyncPackError("同步包未生成：\n- " + "\n- ".join(failures))
    return files


def exclusion_category(relative: Path, size: int) -> tuple[str, str] | None:
    """仅返回安全类别；不会在生成物中保留被排除文件的路径。"""

    lowered = relative.as_posix().lower()
    parts = set(relative.parts)
    name = relative.name.lower()
    if ".git" in parts:
        return "git_internal", "Git 内部数据不属于可交接项目上下文"
    if any(part in EXCLUDED_DIR_PARTS for part in parts):
        return "local_runtime_or_cache", "本地运行、缓存或派生产物不进入同步包"
    if any(part.startswith("_qa") or "render" in part.lower() or "contact_sheet" in part.lower() for part in relative.parts):
        return "qa_or_rendered_output", "QA、渲染或联系表派生产物不进入同步包"
    if name == "research_channels.json":
        return "private_contacts", "可能含私人联系方式的本地资料不进入同步包"
    if name.startswith("._") or name == ".ds_store":
        return "system_metadata", "系统元数据会破坏跨机器可移植性"
    if any(token in name for token in SECRET_FILENAME_PARTS):
        return "credentials_or_recovery", "可能含凭据或账号恢复信息的文件不进入同步包"
    if relative.suffix.lower() in EXCLUDED_SUFFIXES:
        return "media_binary_or_archive", "媒体、二进制或压缩产物不进入同步包"
    if size > MAX_SYNC_FILE_BYTES:
        return "oversized_file", "超过同步包单文件大小限制"
    if lowered.startswith("dist/"):
        return "distribution_artifact", "历史同步或分发产物不重复装入同步包"
    return None


def iter_workspace_files() -> Iterable[Path]:
    for path in ROOT.rglob("*"):
        if path.is_file():
            yield path


def workspace_exclusion_summary() -> list[dict[str, object]]:
    """统计排除类别，不披露被排除文件名、目录结构或单个文件大小。"""

    summaries: dict[str, dict[str, object]] = {}
    for path in iter_workspace_files():
        relative = path.relative_to(ROOT)
        try:
            size = path.stat().st_size
        except OSError:
            continue
        category = exclusion_category(relative, size)
        if not category:
            continue
        category_name, reason = category
        summary = summaries.setdefault(
            category_name,
            {
                "category": category_name,
                "reason": reason,
                "count": 0,
                "file_size_range_bytes": {"min": size, "max": size},
            },
        )
        summary["count"] = int(summary["count"]) + 1
        size_range = summary["file_size_range_bytes"]
        if isinstance(size_range, dict):
            size_range["min"] = min(int(size_range["min"]), size)
            size_range["max"] = max(int(size_range["max"]), size)
    return [summaries[name] for name in sorted(summaries)]


def render_project_context() -> str:
    sections = (
        ("项目入口", ROOT / "PROJECT_ENTRY.md"),
        ("业务状态", ROOT / "docs/project/BUSINESS_STATUS.md"),
        ("当前总览", ROOT / "docs/project/CURRENT_STATUS.md"),
        ("事实源地图", ROOT / "docs/project/SOURCE_OF_TRUTH.md"),
        ("范围与边界", ROOT / "docs/project/SCOPE_AND_BOUNDARIES.md"),
        ("协作机制状态", ROOT / "docs/collaboration/COLLABORATION_STATUS.md"),
    )
    rendered = ["# 项目上下文｜PROJECT_CONTEXT", "", "本文件由同步包脚本生成，汇总最小必要上下文；完整规则仍以同包原文件为准。"]
    for title, path in sections:
        rendered.extend(["", f"## {title}", "", read_text(path).strip()])
    return "\n".join(rendered) + "\n"


def render_git_state(state: dict[str, str]) -> str:
    dirty = state["worktree_status"] or "clean"
    return "\n".join(
        (
            "# Git 状态｜GIT_STATE",
            "",
            f"- 生成时分支：`{state['branch']}`",
            f"- 生成时来源 commit：`{state['source_commit']}`",
            f"- 远端：`{state['remote_origin']}`",
            f"- 生成时工作区：`{dirty}`",
            "",
            "说明：`source_commit` 是生成同步包时工作区所基于的 commit，不等于之后提交同步包目录的 commit，因此不会形成 Manifest 自我引用。新会话开始写入前必须重新运行 `git status --short --branch`。",
            "",
        )
    )


def render_file_index() -> str:
    lines = [
        "# 文件索引｜FILE_INDEX",
        "",
        "本索引是明确的项目地图，不扫描或披露本机顶层目录、私有文件名或文件数量。业务原件仍以 `SOURCE_OF_TRUTH.md` 的优先级为准。",
        "",
        "## 项目地图",
        "",
        "| 类别 | 内容与读取边界 |",
        "|---|---|",
        "| 核心协作文件 | 先读本包中的 Agent 规则、项目入口、业务状态、总览、事实源、边界与协作状态。 |",
        "| 汾酒研究源文件 | 仅作为可追溯的历史研究输入；当前业务范围以业务状态和正式决策为准。 |",
        "| 供应链资料入口 | 按事实源地图定向回读本地供应链启动文件或模板；模板不等于供应链已确认。 |",
        "| 海鲜独立资料线 | 仅在明确的海鲜任务中读取；不得用于推导汾酒产品、客户、价格、资质或履约事实。 |",
        "| 本地私有资料 | 线索、联系方式、环境配置、凭据和恢复资料仅在本地受控使用，不上传、不打包。 |",
        "| 派生产物 | 媒体、渲染、QA、缓存与分发产物仅作线索；需要时回读来源文件，不能作为唯一事实源。 |",
        "",
    ]
    return "\n".join(lines)


def render_sync_readme(timestamp: str, state: dict[str, str]) -> str:
    return "\n".join(
        (
            "# 汾酒项目同步包｜PROJECT_SYNC_README",
            "",
            f"- 生成时间：`{timestamp}`",
            f"- 来源分支：`{state['branch']}`",
            f"- 来源 commit：`{state['source_commit']}`",
            "",
            "## 建议阅读顺序",
            "",
            "1. `AGENTS.md`",
            "2. `PROJECT_ENTRY.md`",
            "3. `BUSINESS_STATUS.md`",
            "4. `CURRENT_STATUS.md`",
            "5. `SOURCE_OF_TRUTH.md`",
            "6. `PROJECT_CONTEXT.md`",
            "7. `COLLABORATION_STATUS.md`",
            "8. `RISKS_AND_BLOCKERS.md`、`NEXT_ACTIONS.md`；仅在任务需要时，按 `FILE_INDEX.md` 回到原仓库读取原始资料。",
            "",
            "## 来源版本含义",
            "",
            "Manifest 的 `source_git.source_commit` 是生成时工作区所基于的 commit；若随后把 `project_sync/latest/` 提交到 Git，该提交会更晚。两者不同是正常的，避免 Manifest 声称包含自身的 commit。最新远端验证以 `COLLABORATION_STATUS.md` 为准。",
            "",
            "## 使用限制",
            "",
            "本包只传递项目协作上下文。它不包含业务原件、线索库、视频、图片、渲染、QA、缓存、凭据或私人信息；不应据此宣称合规、合作、上线、销售或履约已经成立。",
            "",
            "## 给新会话的开始指令",
            "",
            "请先复述项目目标、当前阶段、已确认事实、未知项、阻断条件和本轮完成标准。没有用户明确授权与必要书面条件时，不外发、不发布、不投放、不下单。",
            "",
        )
    )


def copy_allowlist(source_files: list[Path], destination: Path) -> None:
    # 将核心入口文件平铺到包根目录，方便非 GitHub 会话直接阅读；其余文件保留原相对路径。
    flattened = {
        "AGENTS.md",
        "README.md",
        "PROJECT_ENTRY.md",
        "docs/project/CURRENT_STATUS.md",
        "docs/project/BUSINESS_STATUS.md",
        "docs/project/DECISIONS.md",
        "docs/project/OPEN_QUESTIONS.md",
        "docs/project/RISKS_AND_BLOCKERS.md",
        "docs/project/NEXT_ACTIONS.md",
        "docs/project/SOURCE_OF_TRUTH.md",
        "docs/collaboration/COLLABORATION_STATUS.md",
    }
    for source in source_files:
        relative = source.relative_to(ROOT).as_posix()
        target = destination / (source.name if relative in flattened else relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        # copyfile 不复制扩展属性，避免外置盘生成 ._ AppleDouble 文件。
        shutil.copyfile(source, target)


def remove_system_metadata(directory: Path) -> None:
    """清理 macOS/FAT 外置盘生成的元数据，确保不会进入包或 manifest。"""

    try:
        paths = sorted(directory.rglob("*"), key=lambda item: len(item.parts), reverse=True)
    except FileNotFoundError:
        return
    for path in paths:
        if path.name.startswith("._") or path.name == ".DS_Store":
            try:
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink()
            except FileNotFoundError:
                # 外置盘的 AppleDouble 文件可在目录枚举期间被系统回收。
                continue


def replace_latest(package_dir: Path, timestamp_for_name: str) -> None:
    """以目录级替换更新 latest，避免外置盘元数据与 rmtree 并发冲突。"""

    backup = SYNC_ROOT / f".latest-stale-{timestamp_for_name}"
    if LATEST_DIR.exists():
        if backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
        os.replace(LATEST_DIR, backup)
    try:
        shutil.copytree(package_dir, LATEST_DIR, copy_function=shutil.copyfile)
        remove_system_metadata(LATEST_DIR)
    except Exception:
        if LATEST_DIR.exists():
            shutil.rmtree(LATEST_DIR, ignore_errors=True)
        if backup.exists() and not LATEST_DIR.exists():
            os.replace(backup, LATEST_DIR)
        raise
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)


def package_file_records(package_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(package_dir.rglob("*")):
        if path.is_file() and path.name != "PROJECT_SYNC_MANIFEST.json":
            records.append(
                {
                    "path": path.relative_to(package_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    return records


def root_relative_path(path: Path) -> str:
    """仅向用户显示仓库内相对路径，避免脚本输出本机绝对路径。"""

    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def archive_relative_path(archive_path: Path) -> str:
    """Manifest 只保存可跨机器解析的仓库内归档路径。"""

    relative = root_relative_path(archive_path)
    if relative == archive_path.name or not relative.startswith("dist/"):
        raise SyncPackError("同步 ZIP 必须位于仓库内的 dist/ 目录")
    return relative


def archive_destination(timestamp_for_name: str) -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    archive_base = DIST_DIR / f"{PACKAGE_NAME_PREFIX}_{timestamp_for_name}"
    archive_path = archive_base.with_suffix(".zip")
    if archive_path.exists():
        raise SyncPackError(f"为避免覆盖历史同步包，已存在同名 ZIP：{root_relative_path(archive_path)}")
    return archive_path


def make_archive(package_dir: Path, archive_path: Path) -> Path:
    shutil.make_archive(str(archive_path.with_suffix("")), "zip", root_dir=package_dir.parent, base_dir=package_dir.name)
    return archive_path


def valid_package_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    relative = PurePosixPath(value)
    return not relative.is_absolute() and all(part not in {"", ".", ".."} for part in relative.parts)


def archive_path_from_manifest(manifest: dict[str, object]) -> Path:
    relative = manifest.get("archive_relative_path")
    if not valid_package_relative_path(relative):
        raise SyncPackError("Manifest 缺少安全的 archive_relative_path")
    relative_path = PurePosixPath(str(relative))
    if relative_path.parts[0] != "dist" or relative_path.suffix != ".zip":
        raise SyncPackError("Manifest 的 archive_relative_path 不符合 dist/ ZIP 约定")
    return ROOT.joinpath(*relative_path.parts)


def is_safe_remote_origin(value: object) -> bool:
    if value == "unavailable":
        return True
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    segments = [segment for segment in parsed.path.split("/") if segment]
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
        and len(segments) == 2
        and all(re.fullmatch(r"[A-Za-z0-9._-]+", segment) for segment in segments)
    )


def manifest_string_values(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from manifest_string_values(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from manifest_string_values(item)


def manifest_contract_failures(manifest: dict[str, object]) -> list[str]:
    """验证 V2 Manifest 的脱敏与可移植性合约。"""

    failures: list[str] = []
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        failures.append(f"Manifest schema_version 必须为 {MANIFEST_SCHEMA_VERSION}")
    source_git = manifest.get("source_git")
    source_git_fields = source_git if isinstance(source_git, dict) else {}
    for forbidden_field in ("repository_root", "archive_path", "excluded_examples"):
        if forbidden_field in manifest or forbidden_field in source_git_fields:
            failures.append(f"Manifest 不得包含 {forbidden_field}")

    if not isinstance(source_git, dict) or set(source_git) != SOURCE_GIT_FIELDS:
        failures.append("Manifest source_git 字段不符合 V2 合约")
    else:
        if source_git.get("worktree_status") not in {"clean", "dirty", "unavailable"}:
            failures.append("Manifest worktree_status 必须是安全状态词")
        if not is_safe_remote_origin(source_git.get("remote_origin")):
            failures.append("Manifest remote_origin 未脱敏或格式无效")

    try:
        archive_path_from_manifest(manifest)
    except SyncPackError as exc:
        failures.append(str(exc))

    for text in manifest_string_values(manifest):
        if any(pattern.search(text) for pattern in LOCAL_ABSOLUTE_PATH_PATTERNS):
            failures.append("Manifest 包含本机绝对路径")
            break
    return failures


def verify_package(package_dir: Path, archive_path: Path | None = None) -> dict[str, object]:
    failures: list[str] = []
    missing = sorted(name for name in EXPECTED_PACKAGE_FILES if not (package_dir / name).is_file())
    if missing:
        failures.append("缺少关键文件：" + ", ".join(missing))
    manifest_path = package_dir / "PROJECT_SYNC_MANIFEST.json"
    manifest: dict[str, object] = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(read_text(manifest_path))
        except json.JSONDecodeError as exc:
            failures.append(f"manifest 不是有效 JSON：{exc}")
        else:
            failures.extend(manifest_contract_failures(manifest))
            manifest_archive_path: Path | None = None
            try:
                manifest_archive_path = archive_path_from_manifest(manifest)
            except SyncPackError:
                pass
            if archive_path is None:
                archive_path = manifest_archive_path
            elif manifest_archive_path is not None and archive_path != manifest_archive_path:
                failures.append("Manifest 的 archive_relative_path 与待验证 ZIP 不一致")

            records = manifest.get("files")
            if not isinstance(records, list):
                failures.append("manifest files 必须是列表")
                records = []
            for record in records:
                if not isinstance(record, dict):
                    failures.append("manifest 包含无效文件记录")
                    continue
                record_path = record.get("path")
                if not valid_package_relative_path(record_path):
                    failures.append("manifest 包含不安全文件路径")
                    continue
                path = package_dir.joinpath(*PurePosixPath(str(record_path)).parts)
                if not path.is_file():
                    failures.append("manifest 指向缺失文件")
                elif record.get("sha256") != sha256(path):
                    failures.append("文件校验和不匹配")
    elif not missing:
        failures.append("缺少 manifest")
    if archive_path is not None:
        if not archive_path.is_file():
            failures.append(f"ZIP 不存在：{root_relative_path(archive_path)}")
        else:
            try:
                with zipfile.ZipFile(archive_path) as archive:
                    bad_member = archive.testzip()
                    member_names = archive.namelist()
                if bad_member:
                    failures.append(f"ZIP 损坏成员：{bad_member}")
                if not any(name.endswith("/PROJECT_SYNC_MANIFEST.json") for name in member_names):
                    failures.append("ZIP 缺少 PROJECT_SYNC_MANIFEST.json")
                if any(Path(name).name.startswith("._") or Path(name).name == ".DS_Store" for name in member_names):
                    failures.append("ZIP 含 macOS 系统元数据文件")
            except zipfile.BadZipFile:
                failures.append("ZIP 无法读取")
    if failures:
        raise SyncPackError("同步包验证失败：\n- " + "\n- ".join(failures))
    return manifest


def build() -> tuple[Path, Path, dict[str, object]]:
    source_files = validate_allowlist()
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    timestamp_for_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    state = git_state()
    excluded_summary = workspace_exclusion_summary()

    SYNC_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fenjiu-sync-", dir=SYNC_ROOT) as temporary:
        temporary_root = Path(temporary)
        package_dir = temporary_root / f"{PACKAGE_NAME_PREFIX}_{timestamp_for_name}"
        package_dir.mkdir()
        copy_allowlist(source_files, package_dir)
        (package_dir / "PROJECT_CONTEXT.md").write_text(render_project_context(), encoding="utf-8")
        (package_dir / "GIT_STATE.md").write_text(render_git_state(state), encoding="utf-8")
        (package_dir / "FILE_INDEX.md").write_text(render_file_index(), encoding="utf-8")
        (package_dir / "PROJECT_SYNC_README.md").write_text(render_sync_readme(timestamp, state), encoding="utf-8")

        remove_system_metadata(package_dir)
        archive_path = archive_destination(timestamp_for_name)
        manifest: dict[str, object] = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "project": "fenjiu_nepal",
            "generated_at": timestamp,
            "source_git": state,
            "sync_strategy": "strict_allowlist",
            "max_file_bytes": MAX_SYNC_FILE_BYTES,
            "archive_relative_path": archive_relative_path(archive_path),
            "files": package_file_records(package_dir),
            "excluded_summary": excluded_summary,
            "notes": [
                "同步包只包含协作上下文和文件地图，不复制业务原件。",
                "发现疑似秘密时构建会失败，不会生成或更新同步包。",
                "排除统计只保留类别、原因、数量和文件大小范围，不记录任何被排除文件路径。",
                "source_git.source_commit 是生成时工作区所基于的 commit，不等于之后提交同步包目录的 commit。",
            ],
        }
        (package_dir / "PROJECT_SYNC_MANIFEST.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        remove_system_metadata(package_dir)
        make_archive(package_dir, archive_path)
        verify_package(package_dir, archive_path)

        replace_latest(package_dir, timestamp_for_name)
        (SYNC_ROOT / "PROJECT_SYNC_MANIFEST.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        remove_system_metadata(SYNC_ROOT)
    return LATEST_DIR, archive_path, manifest


def verify_existing() -> tuple[Path, dict[str, object]]:
    manifest_path = LATEST_DIR / "PROJECT_SYNC_MANIFEST.json"
    if not manifest_path.is_file():
        raise SyncPackError("未找到最新同步包。请先运行：python3 scripts/build_project_sync_pack.py")
    manifest = json.loads(read_text(manifest_path))
    archive_path = archive_path_from_manifest(manifest)
    verify_package(LATEST_DIR, archive_path)
    return archive_path, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="生成或验证汾酒项目同步包")
    parser.add_argument("--verify", action="store_true", help="只验证 project_sync/latest/ 和其 ZIP")
    args = parser.parse_args()
    try:
        if args.verify:
            archive_path, manifest = verify_existing()
            print(f"同步包验证通过：{root_relative_path(LATEST_DIR)}")
            print(f"ZIP：{root_relative_path(archive_path)}")
            print(f"文件数：{len(manifest.get('files', []))}")
        else:
            latest, archive_path, manifest = build()
            print("同步包生成成功。")
            print(f"最新目录：{root_relative_path(latest)}")
            print(f"ZIP：{root_relative_path(archive_path)}")
            print(f"来源分支：{manifest['source_git']['branch']}")
            print(f"来源 commit：{manifest['source_git']['source_commit']}")
            print(f"文件数：{len(manifest['files'])}")
    except SyncPackError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
