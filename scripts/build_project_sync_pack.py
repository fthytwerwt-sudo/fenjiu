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
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SYNC_ROOT = ROOT / "project_sync"
LATEST_DIR = SYNC_ROOT / "latest"
DIST_DIR = ROOT / "dist"
MAX_SYNC_FILE_BYTES = 1 * 1024 * 1024
PACKAGE_NAME_PREFIX = "fenjiu_project_sync_pack"

# 这些文件是同步包唯一允许复制的源文件。业务原件只在事实源地图中被定位，
# 不被默认复制到新会话，避免意外披露和上下文膨胀。
ALLOWLIST = (
    "AGENTS.md",
    "README.md",
    "PROJECT_ENTRY.md",
    "docs/project/PROJECT_GOAL.md",
    "docs/project/CURRENT_STATUS.md",
    "docs/project/SCOPE_AND_BOUNDARIES.md",
    "docs/project/DECISIONS.md",
    "docs/project/OPEN_QUESTIONS.md",
    "docs/project/RISKS_AND_BLOCKERS.md",
    "docs/project/NEXT_ACTIONS.md",
    "docs/project/SOURCE_OF_TRUTH.md",
    "docs/collaboration/CHATGPT_CODEX_WORKFLOW.md",
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
    "CURRENT_STATUS.md",
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
HIGH_CONFIDENCE_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,})\b"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|passwd|access[_-]?token|auth[_-]?token)\b\s*[:=]\s*[\"']?([A-Za-z0-9_./+=-]{16,})"
    ),
)
SAFE_PLACEHOLDERS = {"example", "placeholder", "your_key", "your-api-key", "replace_me", "changeme", "<redacted>"}


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
    """空输出是干净状态，不应被误报为 Git 不可用。"""

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
    return completed.stdout.strip() or "clean"


def git_state() -> dict[str, str]:
    return {
        "repository_root": str(ROOT),
        "branch": git_value("branch", "--show-current"),
        "commit": git_value("rev-parse", "HEAD"),
        "short_commit": git_value("rev-parse", "--short", "HEAD"),
        "worktree_status": git_worktree_status(),
        "remote_origin": git_value("remote", "get-url", "origin"),
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
        files.append(path)
    if failures:
        raise SyncPackError("同步包未生成：\n- " + "\n- ".join(failures))
    return files


def exclusion_reason(relative: Path, size: int) -> str | None:
    """用于索引/manifest 的工作区排除说明，不读取被排除文件内容。"""

    lowered = relative.as_posix().lower()
    parts = set(relative.parts)
    name = relative.name.lower()
    if ".git" in parts:
        return "Git 内部目录"
    if any(part in EXCLUDED_DIR_PARTS for part in parts):
        return "缓存、派生产物或本地运行目录"
    if any(part.startswith("_qa") or "render" in part.lower() or "contact_sheet" in part.lower() for part in relative.parts):
        return "QA、渲染或联系表派生产物"
    if name == "research_channels.json":
        return "线索库含联系方式，仅限本地受控使用"
    if name.startswith("._") or name == ".ds_store":
        return "系统元数据"
    if any(token in name for token in SECRET_FILENAME_PARTS):
        return "可能含凭据或恢复信息"
    if relative.suffix.lower() in EXCLUDED_SUFFIXES:
        return "媒体、二进制产物或压缩包"
    if size > MAX_SYNC_FILE_BYTES:
        return f"超过同步包单文件限制（{MAX_SYNC_FILE_BYTES // 1024 // 1024} MiB）"
    if lowered.startswith("dist/"):
        return "历史同步/分发产物"
    return None


def iter_workspace_files() -> Iterable[Path]:
    for path in ROOT.rglob("*"):
        if path.is_file():
            yield path


def workspace_inventory() -> tuple[Counter[str], list[dict[str, object]], dict[str, dict[str, int]]]:
    reasons: Counter[str] = Counter()
    examples: list[dict[str, object]] = []
    top_level: dict[str, dict[str, int]] = {}
    for path in iter_workspace_files():
        relative = path.relative_to(ROOT)
        try:
            size = path.stat().st_size
        except OSError:
            continue
        top = relative.parts[0] if len(relative.parts) > 1 else "(root files)"
        bucket = top_level.setdefault(top, {"files": 0, "bytes": 0})
        bucket["files"] += 1
        bucket["bytes"] += size
        reason = exclusion_reason(relative, size)
        if reason:
            reasons[reason] += 1
            if len(examples) < 80:
                examples.append({"path": relative.as_posix(), "bytes": size, "reason": reason})
    return reasons, examples, top_level


def human_size(size: int) -> str:
    units = ("B", "KiB", "MiB", "GiB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def render_project_context() -> str:
    sections = (
        ("项目入口", ROOT / "PROJECT_ENTRY.md"),
        ("项目目标", ROOT / "docs/project/PROJECT_GOAL.md"),
        ("当前状态", ROOT / "docs/project/CURRENT_STATUS.md"),
        ("范围与边界", ROOT / "docs/project/SCOPE_AND_BOUNDARIES.md"),
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
            f"- 生成时 commit：`{state['commit']}`",
            f"- 远端：`{state['remote_origin']}`",
            f"- 生成时工作区：`{dirty}`",
            "",
            "说明：同步包中的 Git 信息是生成瞬间的快照。新会话开始写入前必须重新运行 `git status --short --branch`。",
            "",
        )
    )


def render_file_index(top_level: dict[str, dict[str, int]], reasons: Counter[str]) -> str:
    lines = [
        "# 文件索引｜FILE_INDEX",
        "",
        "本索引帮助新会话定向读取。它不代表所有文件都应上传或进入同步包。业务原件仍以 `SOURCE_OF_TRUTH.md` 的优先级为准。",
        "",
        "## 主要工作区概览",
        "",
        "| 目录/类别 | 文件数 | 大小 | 建议读取方式 |",
        "|---|---:|---:|---|",
    ]
    for name in sorted(top_level):
        item = top_level[name]
        if name in {"docs", "scripts", "project_sync"}:
            guidance = "先读；同步包已收录必要上下文"
        elif name in {"outputs", "qa"} or name.startswith("_qa"):
            guidance = "派生产物；按需本地查看，不作默认事实源"
        elif name == "research_channels.json":
            guidance = "本地线索资料；不可上传或默认共享"
        elif name == "(root files)":
            guidance = "按事实源地图定向读取研究 JSON 与生成脚本"
        else:
            guidance = "业务资料；按任务和事实源地图定向读取"
        lines.append(f"| `{name}` | {item['files']} | {human_size(item['bytes'])} | {guidance} |")

    lines.extend(["", "## 默认排除统计", ""])
    for reason, count in reasons.most_common():
        lines.append(f"- {reason}：{count} 个文件")
    lines.extend(
        [
            "",
            "## 主要原始资料入口",
            "",
            "- 汾酒研究：`research_root.json`、`research_execution.json`、`research_culture_compliance.json`。",
            "- 线索资料：`research_channels.json`（本地受控，不打包）。",
            "- 供应链/合作方资料：`供应链启动文件_最终版/`、`汾酒海鲜_尼泊尔线上销售_供应链协同与资料交付体系/`。",
            "- 尼泊尔海鲜资料线：`尼泊尔海鲜AI线上销售系统/`（独立于汾酒主线）。",
            "- 生成逻辑：根目录 `build_*.py`、`*_data.py`，以及 `scripts/`。",
            "",
        ]
    )
    return "\n".join(lines)


def render_sync_readme(timestamp: str, state: dict[str, str]) -> str:
    return "\n".join(
        (
            "# 汾酒项目同步包｜PROJECT_SYNC_README",
            "",
            f"- 生成时间：`{timestamp}`",
            f"- 来源分支：`{state['branch']}`",
            f"- 来源 commit：`{state['commit']}`",
            "",
            "## 建议阅读顺序",
            "",
            "1. `AGENTS.md`",
            "2. `PROJECT_ENTRY.md`",
            "3. `CURRENT_STATUS.md`",
            "4. `SOURCE_OF_TRUTH.md`",
            "5. `PROJECT_CONTEXT.md`、`RISKS_AND_BLOCKERS.md`、`NEXT_ACTIONS.md`",
            "6. 仅在任务需要时，按 `FILE_INDEX.md` 回到原仓库读取原始资料。",
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
        "docs/project/DECISIONS.md",
        "docs/project/OPEN_QUESTIONS.md",
        "docs/project/RISKS_AND_BLOCKERS.md",
        "docs/project/NEXT_ACTIONS.md",
        "docs/project/SOURCE_OF_TRUTH.md",
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


def archive_destination(timestamp_for_name: str) -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    archive_base = DIST_DIR / f"{PACKAGE_NAME_PREFIX}_{timestamp_for_name}"
    archive_path = archive_base.with_suffix(".zip")
    if archive_path.exists():
        raise SyncPackError(f"为避免覆盖历史同步包，已存在同名 ZIP：{archive_path}")
    return archive_path


def make_archive(package_dir: Path, archive_path: Path) -> Path:
    shutil.make_archive(str(archive_path.with_suffix("")), "zip", root_dir=package_dir.parent, base_dir=package_dir.name)
    return archive_path


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
            for record in manifest.get("files", []):
                if not isinstance(record, dict):
                    failures.append("manifest 包含无效文件记录")
                    continue
                path = package_dir / str(record.get("path", ""))
                if not path.is_file():
                    failures.append(f"manifest 指向缺失文件：{record.get('path')}")
                elif record.get("sha256") != sha256(path):
                    failures.append(f"文件校验和不匹配：{record.get('path')}")
    elif not missing:
        failures.append("缺少 manifest")
    if archive_path is not None:
        if not archive_path.is_file():
            failures.append(f"ZIP 不存在：{archive_path}")
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
    reasons, excluded_examples, top_level = workspace_inventory()

    SYNC_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fenjiu-sync-", dir=SYNC_ROOT) as temporary:
        temporary_root = Path(temporary)
        package_dir = temporary_root / f"{PACKAGE_NAME_PREFIX}_{timestamp_for_name}"
        package_dir.mkdir()
        copy_allowlist(source_files, package_dir)
        (package_dir / "PROJECT_CONTEXT.md").write_text(render_project_context(), encoding="utf-8")
        (package_dir / "GIT_STATE.md").write_text(render_git_state(state), encoding="utf-8")
        (package_dir / "FILE_INDEX.md").write_text(render_file_index(top_level, reasons), encoding="utf-8")
        (package_dir / "PROJECT_SYNC_README.md").write_text(render_sync_readme(timestamp, state), encoding="utf-8")

        remove_system_metadata(package_dir)
        archive_path = archive_destination(timestamp_for_name)
        manifest: dict[str, object] = {
            "schema_version": 1,
            "project": "fenjiu_nepal",
            "generated_at": timestamp,
            "source_git": state,
            "sync_strategy": "strict_allowlist",
            "max_file_bytes": MAX_SYNC_FILE_BYTES,
            "archive_path": str(archive_path),
            "files": package_file_records(package_dir),
            "excluded_summary": dict(reasons.most_common()),
            "excluded_examples": excluded_examples,
            "notes": [
                "同步包只包含协作上下文和文件地图，不复制业务原件。",
                "发现疑似秘密时构建会失败，不会生成或更新同步包。",
                "线索库、媒体、QA、渲染、缓存、环境文件和 ZIP 默认排除。",
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
    archive_text = manifest.get("archive_path")
    archive_path = Path(archive_text) if isinstance(archive_text, str) else None
    verify_package(LATEST_DIR, archive_path)
    return archive_path or Path(""), manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="生成或验证汾酒项目同步包")
    parser.add_argument("--verify", action="store_true", help="只验证 project_sync/latest/ 和其 ZIP")
    args = parser.parse_args()
    try:
        if args.verify:
            archive_path, manifest = verify_existing()
            print(f"同步包验证通过：{LATEST_DIR}")
            print(f"ZIP：{archive_path}")
            print(f"文件数：{len(manifest.get('files', []))}")
        else:
            latest, archive_path, manifest = build()
            print("同步包生成成功。")
            print(f"最新目录：{latest}")
            print(f"ZIP：{archive_path}")
            print(f"来源分支：{manifest['source_git']['branch']}")
            print(f"来源 commit：{manifest['source_git']['commit']}")
            print(f"文件数：{len(manifest['files'])}")
    except SyncPackError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
