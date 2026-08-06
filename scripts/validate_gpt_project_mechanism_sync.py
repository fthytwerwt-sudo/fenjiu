#!/usr/bin/env python3
"""Validate the Fenjiu GPT Project mechanism sync package."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "GPT项目资料同步包_gpt_project_mechanism_sync"
MANIFEST = PACKAGE / "上传清单_manifest.md"
REPORT = ROOT / "docs/collaboration/GPT_Project同步包验证报告_gpt_project_package_validation_report.md"
ROOT_AGENTS = ROOT / "AGENTS.md"
AGENTS_MIRROR = PACKAGE / "project_entry/AGENTS.md"

REQUIRED_FILES = [
    "00_GPT_Project上传说明_readme.md",
    "上传清单_manifest.md",
    "01_汾酒项目系统提示词_fenjiu_project_system_prompt.md",
    "02_项目身份与长期业务边界_project_identity_stable_scope.md",
    "03_三层架构与事实源边界_three_layer_source_boundary.md",
    "04_P0-P1-P2锚点与抗漂移机制_anchor_priority_anti_drift.md",
    "05_GitHub事实源读取机制_github_fact_source_protocol.md",
    "06_Codex执行落库机制_codex_execution_to_repo_protocol.md",
    "07_供应链启动与资料缺口判断机制_supplier_readiness_gap_protocol.md",
    "08_TikTok主线与渠道边界_tiktok_channel_scope_protocol.md",
    "09_酒类合规与外部执行闸门_alcohol_compliance_execution_gate.md",
    "10_汾酒与海鲜业务线隔离机制_business_line_isolation.md",
    "11_外部资料保真与执行桥接_external_evidence_bridge.md",
    "12_方向型输入到可执行任务机制_direction_to_execution_protocol.md",
    "13_六层需求确认与实现设计闸门_six_layer_requirement_gate.md",
    "14_Codex长期执行单模板_codex_task_template.md",
    "15_Codex结果复审与完成度边界_codex_result_review.md",
    "16_输出硬规则与中文语义对齐_output_hard_rules.md",
    "17_Git提交推送与远端验证_git_completion_gate.md",
    "18_AGENTS与GPTProject边界_agents_project_boundary.md",
    "19_用户上传后验证清单_post_upload_validation_checklist.md",
    "20_同步包维护与更新机制_package_maintenance_protocol.md",
    "project_entry/AGENTS.md",
]

INSTRUCTIONS_FILE = "01_汾酒项目系统提示词_fenjiu_project_system_prompt.md"
KNOWLEDGE_SKIP = {INSTRUCTIONS_FILE}
PACKAGE_REQUIRED_KEYWORDS = ["汾酒", "尼泊尔", "TikTok", "供应链", "商品", "价格", "海鲜", "GitHub", "Codex"]
AGENTS_REQUIRED_KEYWORDS = {
    "四层结构": ["账号记忆", "GPT Project", "GitHub `main`", "Codex"],
    "P0/P1/P2": ["P0", "P1", "P2", "P0 > P1 > P2"],
    "六层需求确认": ["六层需求确认", "目标层", "机制层", "实现设计层", "流程层", "判断标准层", "反馈层"],
    "实现设计字段": [
        "primary_route",
        "fallback_route",
        "capability_status",
        "probe_required",
        "allowed_codex_autonomy",
        "forbidden_codex_guessing",
    ],
    "workspace_remote_gate": ["pwd", "git rev-parse --show-toplevel", "git remote -v", "blocked_wrong_remote", "blocked_wrong_workspace_root"],
    "git_completion_gate": ["git add .", "commit 已创建", "push 已成功", "remote HEAD 已验证"],
    "mechanism_missing_gate": ["blocked_gpt_project_mechanism_missing"],
    "sync_package_boundary": ["project_sync/latest", "GPT项目资料同步包_gpt_project_mechanism_sync"],
}
SOURCE_PRIORITY_DEFINITIONS = [
    "P0 = 用户本轮明确输入",
    "P1 = GitHub main 当前事实、当前书面证据和当前验证证据",
    "P2 = 历史聊天、账号记忆、旧项目机制、外部资料和通用建议",
]
SOURCE_PRIORITY_FILES = {
    "AGENTS.md": ROOT_AGENTS,
    INSTRUCTIONS_FILE: PACKAGE / INSTRUCTIONS_FILE,
    "04_P0-P1-P2锚点与抗漂移机制_anchor_priority_anti_drift.md": PACKAGE
    / "04_P0-P1-P2锚点与抗漂移机制_anchor_priority_anti_drift.md",
    "14_Codex长期执行单模板_codex_task_template.md": PACKAGE / "14_Codex长期执行单模板_codex_task_template.md",
    "19_用户上传后验证清单_post_upload_validation_checklist.md": PACKAGE
    / "19_用户上传后验证清单_post_upload_validation_checklist.md",
}
FORBIDDEN_BUSINESS_P0_TERMS = [
    "P0 缺口",
    "P0 证据",
    "P0 阻断",
    "P0 条件",
    "P0 输入齐全",
    "价格和库存是 P0",
]
FORBIDDEN_STATUS_TERMS = [
    "blocked_need_requirement_design",
    "partial_completed",
]
REQUIRED_STATUS_TERMS = [
    "blocked_need_implementation_design_layer",
    "blocked_push_failed",
    "local_only_not_completed",
    "no_file_change_completed_readonly",
]
SYSTEM_REQUIRED_KEYWORDS = [
    "汾酒",
    "尼泊尔",
    "TikTok",
    "供应链",
    "商品",
    "价格",
    "海鲜",
    "P0",
    "六层",
    "Codex",
    "GitHub",
]
PROMPT_GOVERNANCE_REQUIRED_TERMS = [
    "repository hygiene check（仓库卫生检查）",
    "configuration validation（配置验证）",
    "data safety check（数据安全检查）",
    "dependency compatibility check（依赖兼容检查）",
]
PROMPT_GOVERNANCE_FORBIDDEN_PHRASES = [
    "security scan",
    "scan network",
    "penetration test",
    "port scan",
    "exploit",
]
PROMPT_GOVERNANCE_TEMPLATE_FILES = [
    INSTRUCTIONS_FILE,
    "14_Codex长期执行单模板_codex_task_template.md",
]
FORBIDDEN_REFERENCE_TERMS = [
    "视频工厂",
    "OPC",
    "一人公司",
    "API 生成真人",
    "API生成真人",
    "用户录制素材",
    "少量 PPT",
    "少量PPT",
    "云端剪辑",
    "MiniMax",
    "FocuSee",
    "DashVector",
    "澜心社",
    "直播切片",
]
PLACEHOLDER_TERMS = ["待补充", "TODO", "TBD", "占位", "lorem ipsum"]
MEDIA_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov", ".mp3", ".wav", ".zip"}
ABSOLUTE_PATH_RE = re.compile(r"(?<![`\\w])/(Users|Volumes|tmp|private|var)/|[A-Za-z]:\\\\")
SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|cookie|authorization)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"
)


@dataclass
class FileInfo:
    name: str
    chars: int
    sha256: str
    upload_location: str
    dynamic_facts: str
    sensitive_scan: str
    read_order: int


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_value(args: list[str], fallback: str = "unknown") -> str:
    try:
        result = subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        return fallback
    return result.stdout.strip() or fallback


def git_show_text(commit: str, file_path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{file_path}"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout


def rel(path: Path) -> str:
    return path.relative_to(PACKAGE).as_posix()


def all_markdown_files() -> list[Path]:
    return sorted(path for path in PACKAGE.rglob("*.md") if not path.name.startswith("._"))


def remove_appledouble_files() -> None:
    for path in PACKAGE.rglob("._*"):
        if path.is_file():
            path.unlink()


def collect_infos() -> list[FileInfo]:
    infos: list[FileInfo] = []
    for index, name in enumerate(REQUIRED_FILES, start=1):
        path = PACKAGE / name
        if name == MANIFEST.name and path.exists():
            text = read_text(path)
        elif name == MANIFEST.name:
            text = ""
        else:
            text = read_text(path)
        if name == INSTRUCTIONS_FILE:
            upload_location = "Project Instructions"
        elif name == MANIFEST.name:
            upload_location = "Project Knowledge"
        else:
            upload_location = "Project Knowledge"
        infos.append(
            FileInfo(
                name=name,
                chars=len(text),
                sha256=sha256_text(text),
                upload_location=upload_location,
                dynamic_facts="否",
                sensitive_scan="通过",
                read_order=index,
            )
        )
    return infos


def render_manifest(infos: list[FileInfo]) -> str:
    source_commit = git_value(["rev-parse", "HEAD"])
    source_agents_text = git_show_text(source_commit, "AGENTS.md")
    source_agents_sha = sha256_text(source_agents_text) if source_agents_text is not None else "missing"
    mirror_agents_sha = sha256_text(read_text(AGENTS_MIRROR)) if AGENTS_MIRROR.exists() else "missing"
    lines = [
        "# GPT Project 配合机制上传清单",
        "",
        "`package_ready_for_manual_upload = true`",
        "",
        "`user_uploaded_to_gpt_project_ui = false`",
        "",
        "## AGENTS 镜像来源",
        "",
        f"- `source_repository`: `fthytwerwt-sudo/fenjiu`",
        f"- `source_branch`: `{git_value(['branch', '--show-current'])}`",
        f"- `source_commit`: `{source_commit}`",
        f"- `source_file`: `AGENTS.md`",
        f"- `source_sha256`: `{source_agents_sha}`",
        f"- `mirror_file`: `project_entry/AGENTS.md`",
        f"- `mirror_sha256`: `{mirror_agents_sha}`",
        f"- `mirror_generated_at_utc`: `{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}`",
        "",
        "本清单由验证脚本根据实际文件生成。字符数和 SHA-256 以当前目录内容为准。",
        "",
        "| 文件路径 | 中文用途 | 上传位置 | 字符数 | SHA-256 | 是否包含动态项目事实 | 敏感扫描 | 推荐读取顺序 |",
        "|---|---|---|---:|---|---|---|---:|",
    ]
    purpose_map = {
        "00_GPT_Project上传说明_readme.md": "说明上传方式、状态边界和禁止上传内容",
        "上传清单_manifest.md": "列出文件、用途、上传位置、字符数和哈希",
        INSTRUCTIONS_FILE: "复制到 Project Instructions 的汾酒专用系统提示词",
        "02_项目身份与长期业务边界_project_identity_stable_scope.md": "固定汾酒尼泊尔 TikTok 主线和业务边界",
        "03_三层架构与事实源边界_three_layer_source_boundary.md": "区分 GPT Project、GitHub、Codex 和账号记忆",
        "04_P0-P1-P2锚点与抗漂移机制_anchor_priority_anti_drift.md": "规定来源优先级和抗漂移检查",
        "05_GitHub事实源读取机制_github_fact_source_protocol.md": "规定何时回读 GitHub 当前事实源",
        "06_Codex执行落库机制_codex_execution_to_repo_protocol.md": "规定 Codex 执行、验证、提交和推送",
        "07_供应链启动与资料缺口判断机制_supplier_readiness_gap_protocol.md": "判断商品、价格、库存、资质和履约业务闸门缺口",
        "08_TikTok主线与渠道边界_tiktok_channel_scope_protocol.md": "限定 TikTok 主线和辅助渠道边界",
        "09_酒类合规与外部执行闸门_alcohol_compliance_execution_gate.md": "规定公开发布、投放、收款和履约的前置条件",
        "10_汾酒与海鲜业务线隔离机制_business_line_isolation.md": "防止海鲜资料污染汾酒主线",
        "11_外部资料保真与执行桥接_external_evidence_bridge.md": "把外部资料保真转为待验证输入或任务",
        "12_方向型输入到可执行任务机制_direction_to_execution_protocol.md": "把模糊输入转为可执行任务单",
        "13_六层需求确认与实现设计闸门_six_layer_requirement_gate.md": "定义目标、机制、实现设计、流程、标准和反馈六层",
        "14_Codex长期执行单模板_codex_task_template.md": "提供长期复用的 Codex 下发模板",
        "15_Codex结果复审与完成度边界_codex_result_review.md": "复审 Codex 结果和完成度边界",
        "16_输出硬规则与中文语义对齐_output_hard_rules.md": "规定中文状态词和禁止夸大表达",
        "17_Git提交推送与远端验证_git_completion_gate.md": "规定 commit、push 和 remote readback 闸门",
        "18_AGENTS与GPTProject边界_agents_project_boundary.md": "区分仓库 AGENTS 与 GPT Project 机制包",
        "19_用户上传后验证清单_post_upload_validation_checklist.md": "提供上传后测试问题和合格回答要点",
        "20_同步包维护与更新机制_package_maintenance_protocol.md": "规定后续何时更新机制包和如何更新",
        "project_entry/AGENTS.md": "根目录 AGENTS 的生成时只读镜像",
    }
    for info in infos:
        lines.append(
            f"| `{info.name}` | {purpose_map[info.name]} | {info.upload_location} | {info.chars} | `{info.sha256}` | {info.dynamic_facts} | {info.sensitive_scan} | {info.read_order} |"
        )
    lines.extend(
        [
            "",
            "## 上传建议",
            "",
            "- `01_汾酒项目系统提示词_fenjiu_project_system_prompt.md`：复制到 Project Instructions。",
            "- 其他 Markdown：上传为 Project Knowledge。",
            "- 本清单也上传为 Knowledge，方便新聊天框核对读取顺序。",
            "- `project_entry/AGENTS.md` 是生成时镜像；根目录当前 AGENTS 始终是权威版本。",
            "",
            "## 禁止上传",
            "",
            "不得上传密码、Token、API Key、Cookie、验证码、私人联系方式、实时价格、实时库存、本地配置、媒体文件、缓存或运行输出。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_manifest_with_stable_self_row(infos: list[FileInfo]) -> str:
    """Render manifest with a stable char count for the manifest row.

    A file cannot contain its own final SHA-256 without changing that SHA-256.
    The manifest row therefore uses an explicit self-reference marker; the
    validation report records the manifest file's actual hash after generation.
    """
    manifest_info = next(info for info in infos if info.name == MANIFEST.name)
    manifest_info.sha256 = "self-referential-see-validation-report"
    previous = -1
    text = render_manifest(infos)
    while len(text) != previous:
        previous = len(text)
        manifest_info.chars = len(text)
        text = render_manifest(infos)
    return text


def parse_manifest(text: str) -> dict[str, tuple[int, str]]:
    result: dict[str, tuple[int, str]] = {}
    for line in text.splitlines():
        if not line.startswith("| `"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 5:
            continue
        name = parts[0].strip("`")
        try:
            chars = int(parts[3])
        except ValueError:
            continue
        sha = parts[4].strip("`")
        result[name] = (chars, sha)
    return result


def parse_manifest_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"- `([^`]+)`: `([^`]*)`", line)
        if match:
            metadata[match.group(1)] = match.group(2)
    return metadata


def validate_source_priority_semantics(errors: list[str], metrics: dict[str, object]) -> None:
    missing_by_file: dict[str, list[str]] = {}
    for label, path in SOURCE_PRIORITY_FILES.items():
        if not path.exists():
            missing_by_file[label] = ["file_missing"]
            continue
        text = read_text(path)
        missing = [definition for definition in SOURCE_PRIORITY_DEFINITIONS if definition not in text]
        if missing:
            missing_by_file[label] = missing
    metrics["source_priority_semantics"] = "passed" if not missing_by_file else "failed"
    if missing_by_file:
        errors.append(f"source priority semantic mismatch: {missing_by_file}")


def validate_business_gate_semantics(
    texts: dict[str, str],
    errors: list[str],
    metrics: dict[str, object],
) -> None:
    package_text = "\n".join(texts.values())
    forbidden_hits = [term for term in FORBIDDEN_BUSINESS_P0_TERMS if term in package_text]
    required_terms = ["business_gates", "业务闸门", "hard_constraints", "硬约束"]
    missing_required = [term for term in required_terms if term not in package_text]
    passed = not forbidden_hits and not missing_required
    metrics["business_gate_semantics"] = "passed" if passed else "failed"
    if forbidden_hits:
        errors.append(f"business gates still named as P0: {forbidden_hits}")
    if missing_required:
        errors.append(f"business gate terminology missing: {missing_required}")


def validate_status_terms(
    texts: dict[str, str],
    errors: list[str],
    metrics: dict[str, object],
) -> None:
    active_texts = [
        "\n".join(texts.values()),
        read_text(ROOT_AGENTS) if ROOT_AGENTS.exists() else "",
        read_text(ROOT / "PROJECT_ENTRY.md") if (ROOT / "PROJECT_ENTRY.md").exists() else "",
        read_text(ROOT / "docs/collaboration/EXECUTION_REPORT_TEMPLATE.md")
        if (ROOT / "docs/collaboration/EXECUTION_REPORT_TEMPLATE.md").exists()
        else "",
    ]
    active_text = "\n".join(active_texts)
    forbidden_hits = [term for term in FORBIDDEN_STATUS_TERMS if term in active_text]
    missing_required = [term for term in REQUIRED_STATUS_TERMS if term not in active_text]
    metrics["blocked_status_consistency"] = (
        "passed" if "blocked_need_implementation_design_layer" in active_text and "blocked_need_requirement_design" not in active_text else "failed"
    )
    metrics["git_status_consistency"] = "passed" if not forbidden_hits and not missing_required else "failed"
    if forbidden_hits:
        errors.append(f"forbidden status terms found: {forbidden_hits}")
    if missing_required:
        errors.append(f"required status terms missing: {missing_required}")


def validate_prompt_governance_language(
    texts: dict[str, str],
    errors: list[str],
    metrics: dict[str, object],
) -> None:
    missing_by_file: dict[str, list[str]] = {}
    forbidden_by_file: dict[str, list[str]] = {}
    for name in PROMPT_GOVERNANCE_TEMPLATE_FILES:
        text = texts.get(name, "")
        missing = [term for term in PROMPT_GOVERNANCE_REQUIRED_TERMS if term not in text]
        if missing:
            missing_by_file[name] = missing
        forbidden = [
            phrase
            for phrase in PROMPT_GOVERNANCE_FORBIDDEN_PHRASES
            if phrase.casefold() in text.casefold()
        ]
        if forbidden:
            forbidden_by_file[name] = forbidden
    passed = not missing_by_file and not forbidden_by_file
    metrics["prompt_governance_language"] = "passed" if passed else "failed"
    if missing_by_file:
        errors.append(f"prompt governance terms missing: {missing_by_file}")
    if forbidden_by_file:
        errors.append(f"prompt governance execution phrases found: {forbidden_by_file}")


def validate_agents_provenance(
    errors: list[str],
    metrics: dict[str, object],
) -> None:
    if not MANIFEST.exists():
        errors.append("blocked_manifest_mismatch: manifest file is missing")
        metrics["agents_source_commit_verified"] = False
        metrics["agents_provenance_verified"] = False
        return

    metadata = parse_manifest_metadata(read_text(MANIFEST))
    source_commit = metadata.get("source_commit", "")
    manifest_source_sha = metadata.get("source_sha256", "")
    manifest_mirror_sha = metadata.get("mirror_sha256", "")
    metrics["agents_source_commit"] = source_commit or "missing"
    if not source_commit:
        errors.append("blocked_manifest_mismatch: source_commit missing from manifest")
        metrics["agents_source_commit_verified"] = False
        metrics["agents_provenance_verified"] = False
        return

    source_agents_text = git_show_text(source_commit, "AGENTS.md")
    if source_agents_text is None:
        errors.append("blocked_agents_provenance_mismatch: source commit AGENTS.md is unreadable")
        metrics["agents_source_commit_verified"] = False
        metrics["agents_provenance_verified"] = False
        return

    source_sha = sha256_text(source_agents_text)
    mirror_text = read_text(AGENTS_MIRROR) if AGENTS_MIRROR.exists() else ""
    mirror_sha = sha256_text(mirror_text) if mirror_text else "missing"
    metrics["agents_source_commit_verified"] = True
    metrics["agents_source_commit_exists"] = True
    metrics["source_commit_agents_sha256"] = source_sha
    metrics["mirror_agents_sha256"] = mirror_sha

    provenance_errors: list[str] = []
    if source_sha != manifest_source_sha:
        provenance_errors.append("source_sha256 does not match git show source commit")
    if mirror_sha != manifest_mirror_sha:
        provenance_errors.append("mirror_sha256 does not match mirror file")
    if source_agents_text != mirror_text:
        provenance_errors.append("source commit AGENTS.md content does not match mirror")
    if provenance_errors:
        errors.append(f"blocked_agents_provenance_mismatch: {provenance_errors}")
        metrics["agents_provenance_verified"] = False
    else:
        metrics["agents_provenance_verified"] = True


def validate(write_manifest: bool) -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []
    metrics: dict[str, object] = {}
    if not PACKAGE.is_dir():
        return [f"missing package directory: {PACKAGE.relative_to(ROOT)}"], metrics

    texts: dict[str, str] = {}
    for name in REQUIRED_FILES:
        path = PACKAGE / name
        if path.exists():
            texts[name] = read_text(path)

    if write_manifest:
        infos = collect_infos()
        MANIFEST.write_text(render_manifest_with_stable_self_row(infos), encoding="utf-8")
        texts[MANIFEST.name] = read_text(MANIFEST)

    remove_appledouble_files()

    existing = {rel(path) for path in all_markdown_files()}
    required = set(REQUIRED_FILES)
    missing = sorted(required - existing)
    extra = sorted(existing - required)
    if missing:
        errors.append(f"missing required files: {missing}")
    if extra:
        errors.append(f"unexpected markdown files: {extra}")

    empty = [name for name, text in texts.items() if not text.strip()]
    if empty:
        errors.append(f"empty files: {empty}")

    placeholders = [name for name, text in texts.items() if any(term in text for term in PLACEHOLDER_TERMS)]
    if placeholders:
        errors.append(f"placeholder terms found: {placeholders}")

    system_text = texts.get(INSTRUCTIONS_FILE, "")
    system_chars = len(system_text)
    metrics["system_prompt_chars"] = system_chars
    if system_chars > 8000:
        errors.append(f"system prompt over 8000 chars: {system_chars}")
    missing_system_keywords = [word for word in SYSTEM_REQUIRED_KEYWORDS if word not in system_text]
    if missing_system_keywords:
        errors.append(f"system prompt missing keywords: {missing_system_keywords}")

    package_text = "\n".join(texts.values())
    missing_package_keywords = [word for word in PACKAGE_REQUIRED_KEYWORDS if word not in package_text]
    if missing_package_keywords:
        errors.append(f"package missing Fenjiu keywords: {missing_package_keywords}")

    validate_source_priority_semantics(errors, metrics)
    validate_business_gate_semantics(texts, errors, metrics)
    validate_status_terms(texts, errors, metrics)
    validate_prompt_governance_language(texts, errors, metrics)

    forbidden_hits = [term for term in FORBIDDEN_REFERENCE_TERMS if term in package_text]
    if forbidden_hits:
        errors.append(f"reference project pollution terms found: {forbidden_hits}")

    absolute_path_hits = [name for name, text in texts.items() if ABSOLUTE_PATH_RE.search(text)]
    if absolute_path_hits:
        errors.append(f"absolute local path found: {absolute_path_hits}")

    secret_hits = [name for name, text in texts.items() if SECRET_RE.search(text)]
    if secret_hits:
        errors.append(f"possible secret found: {secret_hits}")

    media_files = [str(path.relative_to(PACKAGE)) for path in PACKAGE.rglob("*") if path.suffix.lower() in MEDIA_SUFFIXES]
    if media_files:
        errors.append(f"media/archive files found: {media_files}")

    content_hashes: dict[str, list[str]] = {}
    for name, text in texts.items():
        if name == MANIFEST.name:
            continue
        content_hashes.setdefault(sha256_text(text), []).append(name)
    duplicates = [names for names in content_hashes.values() if len(names) > 1]
    if duplicates:
        errors.append(f"duplicate file contents found: {duplicates}")

    upload_readme = texts.get("00_GPT_Project上传说明_readme.md", "")
    if "project_sync/latest" not in upload_readme or "user_uploaded_to_gpt_project_ui = false" not in upload_readme:
        errors.append("upload readme does not clearly distinguish project_sync/latest or UI upload status")

    if "user_uploaded_to_gpt_project_ui = false" not in package_text:
        errors.append("user upload status false is missing")
    if "package_ready_for_manual_upload = true" not in package_text:
        errors.append("package ready status true is missing")

    if MANIFEST.exists():
        manifest_entries = parse_manifest(read_text(MANIFEST))
        missing_manifest_entries = sorted(required - set(manifest_entries))
        if missing_manifest_entries:
            errors.append(f"manifest missing entries: {missing_manifest_entries}")
        for name in REQUIRED_FILES:
            if name not in texts or name not in manifest_entries:
                continue
            chars, sha = manifest_entries[name]
            actual_text = texts[name]
            if chars != len(actual_text):
                errors.append(f"manifest char mismatch for {name}: {chars} != {len(actual_text)}")
            if name == MANIFEST.name and sha == "self-referential-see-validation-report":
                continue
            if sha != sha256_text(actual_text):
                errors.append(f"manifest sha mismatch for {name}")
    else:
        errors.append("manifest file is missing")

    if not ROOT_AGENTS.exists():
        errors.append("root AGENTS.md missing")
    if not AGENTS_MIRROR.exists():
        errors.append("GPT Project AGENTS mirror missing")
    if ROOT_AGENTS.exists() and AGENTS_MIRROR.exists():
        root_agents_text = read_text(ROOT_AGENTS)
        mirror_text = read_text(AGENTS_MIRROR)
        root_agents_sha = sha256_text(root_agents_text)
        mirror_agents_sha = sha256_text(mirror_text)
        metrics["root_agents_sha256"] = root_agents_sha
        metrics["mirror_agents_sha256"] = mirror_agents_sha
        metrics["agents_mirror_consistent"] = root_agents_sha == mirror_agents_sha
        if root_agents_sha != mirror_agents_sha:
            errors.append("AGENTS mirror sha mismatch")
        for label, words in AGENTS_REQUIRED_KEYWORDS.items():
            missing_words = [word for word in words if word not in root_agents_text]
            if missing_words:
                errors.append(f"AGENTS missing {label}: {missing_words}")
    else:
        metrics["agents_mirror_consistent"] = False

    conflict_texts = {
        "system_prompt": texts.get(INSTRUCTIONS_FILE, ""),
        "upload_readme": texts.get("00_GPT_Project上传说明_readme.md", ""),
        "agents_boundary": texts.get("18_AGENTS与GPTProject边界_agents_project_boundary.md", ""),
        "manifest": texts.get(MANIFEST.name, ""),
    }
    if "project_entry/AGENTS.md" not in conflict_texts["manifest"]:
        errors.append("manifest does not list AGENTS mirror")
    if "project_entry/AGENTS.md" not in conflict_texts["upload_readme"]:
        errors.append("upload readme does not explain AGENTS mirror")
    if "根目录当前 `AGENTS.md` 永远高于" not in conflict_texts["agents_boundary"]:
        errors.append("AGENTS boundary file does not state root AGENTS authority")

    validate_agents_provenance(errors, metrics)

    metrics["file_count"] = len(existing)
    metrics["required_file_count"] = len(REQUIRED_FILES)
    metrics["non_empty_file_count"] = len([text for text in texts.values() if text.strip()])
    metrics["manifest_consistent"] = not any("manifest" in error for error in errors)
    metrics["hash_verified"] = not any("sha mismatch" in error for error in errors)
    metrics["sensitive_scan"] = "passed" if not secret_hits else "failed"
    metrics["absolute_path_scan"] = "passed" if not absolute_path_hits else "failed"
    metrics["reference_pollution_scan"] = "passed" if not forbidden_hits else "failed"
    metrics["media_scan"] = "passed" if not media_files else "failed"
    if MANIFEST.exists():
        metrics["manifest_actual_sha256"] = sha256_text(read_text(MANIFEST))
    return errors, metrics


def write_report(errors: list[str], metrics: dict[str, object]) -> None:
    status = "passed" if not errors else "failed"
    lines = [
        "# GPT Project 同步包验证报告",
        "",
        f"- **验证状态**：`{status}`",
        f"- **文件数量**：{metrics.get('file_count', 0)}",
        f"- **非空文件数量**：{metrics.get('non_empty_file_count', 0)}",
        f"- **系统提示词字符数**：{metrics.get('system_prompt_chars', 0)}",
        f"- **Manifest 一致性**：{metrics.get('manifest_consistent', False)}",
        f"- **SHA-256**：{metrics.get('hash_verified', False)}",
        f"- **汾酒项目专属性验证**：{'passed' if not errors else 'see findings'}",
        f"- **参考项目污染扫描**：{metrics.get('reference_pollution_scan', 'unknown')}",
        f"- **敏感信息扫描**：{metrics.get('sensitive_scan', 'unknown')}",
        f"- **绝对路径扫描**：{metrics.get('absolute_path_scan', 'unknown')}",
        f"- **媒体排除**：{metrics.get('media_scan', 'unknown')}",
        f"- **Manifest 文件实际 SHA-256**：`{metrics.get('manifest_actual_sha256', 'not_generated')}`",
        f"- **根 AGENTS SHA-256**：`{metrics.get('root_agents_sha256', 'not_checked')}`",
        f"- **source commit AGENTS SHA-256**：`{metrics.get('source_commit_agents_sha256', 'not_checked')}`",
        f"- **GPT Project AGENTS 镜像 SHA-256**：`{metrics.get('mirror_agents_sha256', 'not_checked')}`",
        f"- **AGENTS 镜像一致性**：{metrics.get('agents_mirror_consistent', False)}",
        f"- `source_priority_semantics = {metrics.get('source_priority_semantics', 'unknown')}`",
        f"- `business_gate_semantics = {metrics.get('business_gate_semantics', 'unknown')}`",
        f"- `blocked_status_consistency = {metrics.get('blocked_status_consistency', 'unknown')}`",
        f"- `git_status_consistency = {metrics.get('git_status_consistency', 'unknown')}`",
        f"- **Prompt 表达治理**：`prompt_governance_language = {metrics.get('prompt_governance_language', 'unknown')}`",
        f"- `agents_source_commit_verified = {str(metrics.get('agents_source_commit_verified', False)).lower()}`",
        f"- `agents_source_commit = {metrics.get('agents_source_commit', 'unknown')}`",
        f"- `agents_provenance_verified = {str(metrics.get('agents_provenance_verified', False)).lower()}`",
        "- **用户上传状态**：`user_uploaded_to_gpt_project_ui = false`",
        "",
        "## Findings",
        "",
    ]
    if errors:
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("- 未发现阻断项。")
    lines.extend(
        [
            "",
            "## 状态边界",
            "",
            "本报告只证明仓库内 GPT Project 配合机制同步包通过本地完整性检查，不表示用户已上传 ChatGPT GPT Project UI，也不表示供应链、平台、合规、上线、销售或履约已完成。",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()

    errors, metrics = validate(write_manifest=args.write_manifest)
    if not args.no_report:
        write_report(errors, metrics)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("GPT Project mechanism sync package validation passed.")
    print(f"files={metrics.get('file_count')} system_prompt_chars={metrics.get('system_prompt_chars')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
