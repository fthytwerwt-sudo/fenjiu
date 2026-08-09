"""P07-02 provider-neutral video manifest and legacy adapter contracts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import re
from typing import Protocol
from uuid import UUID

from core.contracts import ContractValidationError, ScopeRef


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)

_LEGACY_SCRIPT_CAPABILITIES: tuple[tuple[str, "LegacyCapability"], ...] = (
    ("generate_happyhorse_shots.py", "happyhorse_dashscope"),
    ("generate_happyhorse_video_edit_once.py", "happyhorse_dashscope"),
    ("prepare_video_assets.py", "ffmpeg_post_process"),
    ("assemble_final_video.py", "ffmpeg_post_process"),
    ("build_video_execution_report.py", "qc_report_reference"),
)


class VideoPortBoundaryError(ContractValidationError):
    """Stable, value-free P07-02 boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _boundary(code: str) -> VideoPortBoundaryError:
    return VideoPortBoundaryError(code)


class LegacyVideoOperation(str, Enum):
    SHOT_GENERATION = "shot_generation"
    VIDEO_EDIT = "video_edit"
    POST_PROCESS = "post_process"
    QC_REPORT = "qc_report"


class LegacyCapability(str, Enum):
    HAPPYHORSE_DASHSCOPE = "happyhorse_dashscope"
    FFMPEG_POST_PROCESS = "ffmpeg_post_process"
    QC_REPORT_REFERENCE = "qc_report_reference"


class LegacyProbeState(str, Enum):
    BLOCKED_NOT_LOCATED = "blocked_not_located"
    HASH_CLI_HELP_ONLY = "hash_cli_help_only"


class ProviderRunState(str, Enum):
    SUBMITTED = "submitted"
    RUNNING = "running"
    DOWNLOADED = "downloaded"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class QualityControlState(str, Enum):
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


def _reject_sensitive_text(value: object, code: str) -> None:
    if not isinstance(value, str):
        raise _boundary(code)
    lowered = value.lower()
    if (
        value.startswith("/")
        or "\\" in value
        or "/users/" in lowered
        or "/volumes/" in lowered
        or ".env" in lowered
        or "outputs/" in lowered
        or "media/" in lowered
        or _SENSITIVE.search(value) is not None
    ):
        raise _boundary(code)


def _require_identifier(value: object, code: str) -> str:
    _reject_sensitive_text(value, code)
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _boundary(code)
    return value


def _require_hash(value: object, code: str) -> str:
    _reject_sensitive_text(value, code)
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise _boundary(code)
    return value


def _require_script_name(value: object) -> str:
    if not isinstance(value, str) or "/" in value or "\\" in value or value.startswith("."):
        raise _boundary("legacy_script_name_required")
    if not value.endswith(".py"):
        raise _boundary("legacy_script_name_required")
    _reject_sensitive_text(value, "legacy_script_name_required")
    return value


def _require_scope(value: object) -> ScopeRef:
    if not isinstance(value, ScopeRef):
        raise _boundary("scope_required")
    _require_identifier(value.correlation_id, "correlation_id_required")
    return value


def _require_uuid(value: object, code: str) -> UUID:
    if not isinstance(value, UUID) or value.int == 0:
        raise _boundary(code)
    return value


def _require_uuid_tuple(value: object, code: str) -> tuple[UUID, ...]:
    if not isinstance(value, tuple) or not value:
        raise _boundary(code)
    for item in value:
        _require_uuid(item, code)
    if len(set(value)) != len(value):
        raise _boundary(code)
    return value


def _require_hash_tuple(value: object, code: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise _boundary(code)
    for item in value:
        _require_hash(item, code)
    if len(set(value)) != len(value):
        raise _boundary(code)
    return value


def _require_ref_tuple(value: object, code: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise _boundary(code)
    for item in value:
        _require_identifier(item, code)
    if len(set(value)) != len(value):
        raise _boundary(code)
    return value


def _require_time(value: object, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _boundary(code)
    return value


def _require_manifest_version(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise _boundary("manifest_version_required")
    return value


def _require_internal_synthetic(
    *,
    is_synthetic: object,
    external_execution_allowed: object,
    code: str,
) -> None:
    if is_synthetic is not True or external_execution_allowed is not False:
        raise _boundary(code)


def _stable_ref(prefix: str, *parts: object) -> str:
    digest = sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    return f"{prefix}:{digest[:32]}"


@dataclass(frozen=True)
class LegacyScriptProbe:
    """Hash/CLI-only legacy script probe result; never authorizes execution."""

    script_name: str
    capability: LegacyCapability
    state: LegacyProbeState
    sha256: str
    cli_help_checked: bool
    execution_allowed: bool = False
    env_read_allowed: bool = False
    output_write_allowed: bool = False

    def __post_init__(self) -> None:
        _require_script_name(self.script_name)
        if not isinstance(self.capability, LegacyCapability):
            raise _boundary("legacy_capability_required")
        if not isinstance(self.state, LegacyProbeState):
            raise _boundary("legacy_probe_state_required")
        if self.state is LegacyProbeState.BLOCKED_NOT_LOCATED:
            if self.sha256 != "UNKNOWN" or self.cli_help_checked is not False:
                raise _boundary("legacy_probe_blocked_required")
        else:
            _require_hash(self.sha256, "legacy_hash_required")
            if self.cli_help_checked is not True:
                raise _boundary("legacy_cli_help_required")
        if (
            self.execution_allowed is not False
            or self.env_read_allowed is not False
            or self.output_write_allowed is not False
        ):
            raise _boundary("legacy_execution_forbidden")

    def safe_summary(self) -> dict[str, object]:
        return {
            "script_name": self.script_name,
            "capability": self.capability.value,
            "state": self.state.value,
            "sha256": self.sha256,
            "cli_help_checked": self.cli_help_checked,
            "execution_allowed": False,
            "env_read_allowed": False,
            "output_write_allowed": False,
        }


@dataclass(frozen=True)
class LegacyVideoAdapterSpec:
    """Provider-neutral mapping from a video manifest to legacy input/output refs."""

    provider_alias: str
    operation: LegacyVideoOperation
    capability: LegacyCapability
    legacy_script: str
    legacy_input_refs: tuple[str, ...]
    legacy_output_ref: str
    no_auto_retry: bool
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.provider_alias, "provider_alias_required")
        if not isinstance(self.operation, LegacyVideoOperation):
            raise _boundary("legacy_operation_required")
        if not isinstance(self.capability, LegacyCapability):
            raise _boundary("legacy_capability_required")
        _require_script_name(self.legacy_script)
        _require_ref_tuple(self.legacy_input_refs, "video_input_ref_forbidden")
        _require_identifier(self.legacy_output_ref, "video_output_ref_forbidden")
        if not isinstance(self.no_auto_retry, bool):
            raise _boundary("retry_flag_required")
        if self.operation is LegacyVideoOperation.VIDEO_EDIT and self.no_auto_retry is not True:
            raise _boundary("video_edit_no_auto_retry_required")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_legacy_adapter_required",
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "provider_alias": self.provider_alias,
            "operation": self.operation.value,
            "capability": self.capability.value,
            "legacy_script": self.legacy_script,
            "legacy_input_refs": list(self.legacy_input_refs),
            "legacy_output_ref": self.legacy_output_ref,
            "no_auto_retry": self.no_auto_retry,
            "is_synthetic": True,
            "external_execution_allowed": False,
        }


@dataclass(frozen=True)
class VideoManifest:
    """Versioned provider-neutral manifest with only hashes and references."""

    schema_version: str
    manifest_id: UUID
    scope: ScopeRef
    video_task_id: UUID
    content_task_id: UUID
    locked_fact_versions: tuple[UUID, ...]
    locked_asset_versions: tuple[UUID, ...]
    policy_version: str
    manifest_version: int
    idempotency_key: str
    prompt_hash: str
    input_asset_hashes: tuple[str, ...]
    cost_approval_ref: str
    legacy_adapter: LegacyVideoAdapterSpec
    created_at: datetime
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    provider_call_requested: bool = False
    internal_export_allowed: bool = False
    public_publish_allowed: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != "video_manifest.v1":
            raise _boundary("manifest_schema_required")
        _require_uuid(self.manifest_id, "manifest_id_required")
        _require_scope(self.scope)
        _require_uuid(self.video_task_id, "video_task_id_required")
        _require_uuid(self.content_task_id, "content_task_id_required")
        _require_uuid_tuple(self.locked_fact_versions, "fact_lock_required")
        _require_uuid_tuple(self.locked_asset_versions, "asset_rights_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_manifest_version(self.manifest_version)
        _require_identifier(self.idempotency_key, "idempotency_key_required")
        _require_hash(self.prompt_hash, "prompt_hash_required")
        _require_hash_tuple(self.input_asset_hashes, "video_input_ref_forbidden")
        _require_identifier(self.cost_approval_ref, "cost_approval_ref_required")
        if not isinstance(self.legacy_adapter, LegacyVideoAdapterSpec):
            raise _boundary("legacy_adapter_required")
        _require_time(self.created_at, "created_at_required")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="external_execution_forbidden",
        )
        if self.provider_call_requested is not False:
            raise _boundary("video_call_forbidden")
        if self.internal_export_allowed is not False:
            raise _boundary("internal_export_forbidden")
        if self.public_publish_allowed is not False:
            raise _boundary("public_publish_forbidden")

    @classmethod
    def from_video_task(
        cls,
        *,
        manifest_id: UUID,
        video_task: object,
        manifest_version: int,
        idempotency_key: str,
        prompt_hash: str,
        input_asset_hashes: tuple[str, ...],
        cost_approval_ref: str,
        legacy_adapter: LegacyVideoAdapterSpec,
        created_at: datetime,
    ) -> "VideoManifest":
        if getattr(getattr(video_task, "state", None), "value", None) != "qc_pending":
            raise _boundary("video_task_state_required")
        if getattr(video_task, "provider_call_requested", True) is not False:
            raise _boundary("video_call_forbidden")
        if getattr(video_task, "internal_export_allowed", True) is not False:
            raise _boundary("internal_export_forbidden")
        if getattr(video_task, "public_publish_allowed", True) is not False:
            raise _boundary("public_publish_forbidden")
        if getattr(video_task, "external_execution_allowed", True) is not False:
            raise _boundary("external_execution_forbidden")

        return cls(
            schema_version="video_manifest.v1",
            manifest_id=manifest_id,
            scope=getattr(video_task, "scope"),
            video_task_id=getattr(video_task, "id"),
            content_task_id=getattr(video_task, "content_task_id"),
            locked_fact_versions=getattr(video_task, "locked_fact_versions"),
            locked_asset_versions=getattr(video_task, "locked_asset_versions"),
            policy_version=getattr(video_task, "policy_version"),
            manifest_version=manifest_version,
            idempotency_key=idempotency_key,
            prompt_hash=prompt_hash,
            input_asset_hashes=input_asset_hashes,
            cost_approval_ref=cost_approval_ref,
            legacy_adapter=legacy_adapter,
            created_at=created_at,
            is_synthetic=True,
            external_execution_allowed=False,
            provider_call_requested=False,
            internal_export_allowed=False,
            public_publish_allowed=False,
        )

    @property
    def provider_task_ref(self) -> str:
        return _stable_ref("provider_ref", self.scope.correlation_id, self.idempotency_key, self.manifest_id)

    def safe_summary(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "manifest_id": str(self.manifest_id),
            "video_task_id": str(self.video_task_id),
            "content_task_id": str(self.content_task_id),
            "locked_fact_versions": [str(value) for value in self.locked_fact_versions],
            "locked_asset_versions": [str(value) for value in self.locked_asset_versions],
            "policy_version": self.policy_version,
            "manifest_version": self.manifest_version,
            "idempotency_key": self.idempotency_key,
            "prompt_hash": self.prompt_hash,
            "input_asset_hashes": list(self.input_asset_hashes),
            "cost_approval_ref": self.cost_approval_ref,
            "legacy_adapter": self.legacy_adapter.safe_summary(),
            "provider_task_ref": self.provider_task_ref,
            "is_synthetic": True,
            "external_execution_allowed": False,
            "provider_call_requested": False,
            "internal_export_allowed": False,
            "public_publish_allowed": False,
        }


@dataclass(frozen=True)
class ProviderRunRef:
    """Fake provider state reference with no raw provider identifier."""

    provider_task_ref: str
    manifest_id: UUID
    manifest_version: int
    state: ProviderRunState
    idempotency_key: str
    external_call_count: int
    may_auto_retry: bool
    manual_review_required: bool
    checked_at: datetime
    error_code: str | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.provider_task_ref, "provider_task_ref_required")
        _require_uuid(self.manifest_id, "manifest_id_required")
        _require_manifest_version(self.manifest_version)
        if not isinstance(self.state, ProviderRunState):
            raise _boundary("provider_state_required")
        _require_identifier(self.idempotency_key, "idempotency_key_required")
        if self.external_call_count != 0:
            raise _boundary("external_execution_forbidden")
        if not isinstance(self.may_auto_retry, bool):
            raise _boundary("retry_flag_required")
        if not isinstance(self.manual_review_required, bool):
            raise _boundary("manual_flag_required")
        _require_time(self.checked_at, "checked_at_required")
        if self.error_code is not None:
            _require_identifier(self.error_code, "error_code_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "provider_task_ref": self.provider_task_ref,
            "manifest_id": str(self.manifest_id),
            "manifest_version": self.manifest_version,
            "state": self.state.value,
            "idempotency_key": self.idempotency_key,
            "external_call_count": 0,
            "may_auto_retry": self.may_auto_retry,
            "manual_review_required": self.manual_review_required,
            "error_code": self.error_code,
        }


@dataclass(frozen=True)
class VideoArtifactRef:
    """Reference-only fake artifact; no media path or file is produced."""

    artifact_ref: str
    provider_task_ref: str
    manifest_id: UUID
    state: ProviderRunState
    content_hash: str
    created_at: datetime

    def __post_init__(self) -> None:
        _require_identifier(self.artifact_ref, "artifact_ref_required")
        _require_identifier(self.provider_task_ref, "provider_task_ref_required")
        _require_uuid(self.manifest_id, "manifest_id_required")
        if self.state is not ProviderRunState.DOWNLOADED:
            raise _boundary("artifact_state_required")
        _require_hash(self.content_hash, "artifact_hash_required")
        _require_time(self.created_at, "created_at_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "artifact_ref": self.artifact_ref,
            "provider_task_ref": self.provider_task_ref,
            "manifest_id": str(self.manifest_id),
            "state": self.state.value,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True)
class QualityControlRef:
    """QC handoff reference; it records no pass/fail quality conclusion."""

    qc_ref: str
    artifact_ref: str
    state: QualityControlState
    quality_approved: bool
    manual_review_required: bool
    checked_at: datetime

    def __post_init__(self) -> None:
        _require_identifier(self.qc_ref, "qc_ref_required")
        _require_identifier(self.artifact_ref, "artifact_ref_required")
        if self.state is not QualityControlState.MANUAL_REVIEW_REQUIRED:
            raise _boundary("qc_state_required")
        if self.quality_approved is not False:
            raise _boundary("quality_result_forbidden")
        if self.manual_review_required is not True:
            raise _boundary("manual_review_required")
        _require_time(self.checked_at, "checked_at_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "qc_ref": self.qc_ref,
            "artifact_ref": self.artifact_ref,
            "state": self.state.value,
            "quality_approved": False,
            "manual_review_required": True,
        }


class VideoPort(Protocol):
    """Provider-neutral fake-first video port."""

    external_call_count: int

    def submit(self, manifest: VideoManifest) -> ProviderRunRef:
        """Submit a manifest to a fake provider and return a reference."""

    def poll(self, provider_task_ref: str) -> ProviderRunRef:
        """Poll a fake provider task reference without network IO."""

    def download_artifact_ref(self, provider_task_ref: str) -> VideoArtifactRef:
        """Return a reference-only artifact handle."""

    def create_qc_ref(self, artifact_ref: str) -> QualityControlRef:
        """Create a manual-review QC reference."""


def build_legacy_probe_baseline(git_files: Iterable[str]) -> tuple[LegacyScriptProbe, ...]:
    """Build the P00/P07 legacy baseline without reading env or running media code."""

    visible_names = {item.rsplit("/", 1)[-1] for item in git_files}
    probes: list[LegacyScriptProbe] = []
    for script_name, capability in _LEGACY_SCRIPT_CAPABILITIES:
        if script_name in visible_names:
            probes.append(
                LegacyScriptProbe(
                    script_name=script_name,
                    capability=LegacyCapability(capability),
                    state=LegacyProbeState.HASH_CLI_HELP_ONLY,
                    sha256="0" * 64,
                    cli_help_checked=True,
                    execution_allowed=False,
                    env_read_allowed=False,
                    output_write_allowed=False,
                )
            )
            continue
        probes.append(
            LegacyScriptProbe(
                script_name=script_name,
                capability=LegacyCapability(capability),
                state=LegacyProbeState.BLOCKED_NOT_LOCATED,
                sha256="UNKNOWN",
                cli_help_checked=False,
                execution_allowed=False,
                env_read_allowed=False,
                output_write_allowed=False,
            )
        )
    return tuple(probes)
