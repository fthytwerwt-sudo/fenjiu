"""P07-03 synthetic video QC, human approval, and internal export contracts.

This module consumes only safe references and hashes. It does not import
provider adapters, read media, write archives, publish externally, or decide
real-world video quality.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import re
from uuid import UUID

from core.contracts import DataState, ScopeRef
from modules.content_video.contracts import (
    AssetOrigin,
    AssetRightsState,
    AssetRightsVersionLock,
    ContentVideoBoundaryError,
    FactApprovalState,
    FactVersionLock,
    PolicyBoundaryState,
    PolicyVersionLock,
)


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)
_FORBIDDEN_REF_FRAGMENT = re.compile(
    r"(?i)(?:^|[./_:-])(?:outputs?|media|raw|archive|provider[-_]?raw[-_]?id)(?:$|[./_:-])"
    r"|\.mp4$|\.mov$|\.wav$|\.aac$"
)


class VideoQcState(str, Enum):
    PASSED = "passed"
    REVISION_REQUIRED = "revision_required"
    MANUAL_HOLD = "manual_hold"


class HumanVideoDecisionAction(str, Enum):
    APPROVE_INTERNAL_EXPORT = "approve_internal_export"
    REJECT = "reject"
    REVISE = "revise"


class HumanVideoDecisionState(str, Enum):
    APPROVED_INTERNAL = "approved_internal"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class InternalExportState(str, Enum):
    INTERNAL_REFERENCE_READY = "internal_reference_ready"


_MANUAL_HOLD_REASONS = {
    "artifact_missing",
    "artifact_manifest_mismatch",
    "artifact_provider_mismatch",
    "provider_qc_missing",
    "provider_qc_state_invalid",
    "qc_artifact_mismatch",
    "technical_qc_missing",
    "artifact_hash_mismatch",
    "fact_lock_required",
    "fact_lock_duplicate",
    "fact_lock_not_current",
    "fact_lock_expired",
    "fact_version_invalidated",
    "manifest_fact_lock_mismatch",
    "asset_rights_required",
    "asset_lock_duplicate",
    "asset_origin_unknown",
    "asset_rights_unknown",
    "asset_rights_expired",
    "asset_version_invalidated",
    "manifest_asset_lock_mismatch",
    "policy_boundary_unknown",
    "policy_lock_expired",
    "policy_version_invalidated",
    "external_publish_forbidden",
}


def _boundary(code: str) -> ContentVideoBoundaryError:
    return ContentVideoBoundaryError(code)


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
        or _SENSITIVE.search(value) is not None
        or _FORBIDDEN_REF_FRAGMENT.search(value) is not None
    ):
        raise _boundary(code)


def _require_identifier(value: object, code: str) -> str:
    _reject_sensitive_text(value, code)
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _boundary(code)
    return value


def _require_export_ref(value: object) -> str:
    return _require_identifier(value, "internal_export_ref_forbidden")


def _require_hash(value: object, code: str) -> str:
    _reject_sensitive_text(value, code)
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise _boundary(code)
    return value


def _coerce_uuid(value: object, code: str) -> UUID:
    if isinstance(value, UUID) and value.int != 0:
        return value
    if isinstance(value, str):
        try:
            parsed = UUID(value)
        except ValueError as exc:
            raise _boundary(code) from exc
        if parsed.int != 0:
            return parsed
    raise _boundary(code)


def _require_uuid(value: object, code: str) -> UUID:
    if not isinstance(value, UUID) or value.int == 0:
        raise _boundary(code)
    return value


def _coerce_uuid_tuple(value: object, code: str) -> tuple[UUID, ...]:
    if not isinstance(value, (tuple, list)) or not value:
        raise _boundary(code)
    result = tuple(_coerce_uuid(item, code) for item in value)
    if len(set(result)) != len(result):
        raise _boundary(code)
    return result


def _require_uuid_tuple(value: object, code: str) -> tuple[UUID, ...]:
    if not isinstance(value, tuple) or not value:
        raise _boundary(code)
    for item in value:
        _require_uuid(item, code)
    if len(set(value)) != len(value):
        raise _boundary(code)
    return value


def _require_time(value: object, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _boundary(code)
    return value


def _require_positive_int(value: object, code: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise _boundary(code)
    return value


def _require_scope(value: object) -> ScopeRef:
    if not isinstance(value, ScopeRef):
        raise _boundary("scope_required")
    _require_identifier(value.correlation_id, "correlation_id_required")
    return value


def _require_internal_synthetic(
    *,
    is_synthetic: object,
    external_execution_allowed: object,
    code: str,
) -> None:
    if is_synthetic is not True or external_execution_allowed is not False:
        raise _boundary(code)


def _digest(prefix: str, *parts: object) -> str:
    material = "\x1f".join(str(part) for part in parts)
    return f"{prefix}:{sha256(material.encode('utf-8')).hexdigest()[:32]}"


def _reason_tuple(reasons: list[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason not in seen:
            _require_identifier(reason, "reason_code_required")
            result.append(reason)
            seen.add(reason)
    return tuple(result)


def _state_for_reasons(reasons: tuple[str, ...]) -> VideoQcState:
    if not reasons:
        return VideoQcState.PASSED
    if any(reason in _MANUAL_HOLD_REASONS for reason in reasons):
        return VideoQcState.MANUAL_HOLD
    return VideoQcState.REVISION_REQUIRED


@dataclass(frozen=True)
class VideoManifestEvidence:
    """Safe P07-02 manifest summary reified for P07-03 QC."""

    schema_version: str
    manifest_id: UUID
    scope: ScopeRef
    video_task_id: UUID
    content_task_id: UUID
    locked_fact_versions: tuple[UUID, ...]
    locked_asset_versions: tuple[UUID, ...]
    policy_version: str
    manifest_version: int
    provider_task_ref: str
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
        _require_positive_int(self.manifest_version, "manifest_version_required")
        _require_identifier(self.provider_task_ref, "provider_task_ref_required")
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
    def from_summary(cls, summary: Mapping[str, object], *, scope: ScopeRef) -> "VideoManifestEvidence":
        if not isinstance(summary, Mapping):
            raise _boundary("manifest_summary_required")
        return cls(
            schema_version=str(summary.get("schema_version", "")),
            manifest_id=_coerce_uuid(summary.get("manifest_id"), "manifest_id_required"),
            scope=scope,
            video_task_id=_coerce_uuid(summary.get("video_task_id"), "video_task_id_required"),
            content_task_id=_coerce_uuid(summary.get("content_task_id"), "content_task_id_required"),
            locked_fact_versions=_coerce_uuid_tuple(
                summary.get("locked_fact_versions"),
                "fact_lock_required",
            ),
            locked_asset_versions=_coerce_uuid_tuple(
                summary.get("locked_asset_versions"),
                "asset_rights_required",
            ),
            policy_version=str(summary.get("policy_version", "")),
            manifest_version=_require_positive_int(
                summary.get("manifest_version"),
                "manifest_version_required",
            ),
            provider_task_ref=str(summary.get("provider_task_ref", "")),
            is_synthetic=summary.get("is_synthetic", False),
            external_execution_allowed=summary.get("external_execution_allowed", False),
            provider_call_requested=summary.get("provider_call_requested", False),
            internal_export_allowed=summary.get("internal_export_allowed", False),
            public_publish_allowed=summary.get("public_publish_allowed", False),
        )


@dataclass(frozen=True)
class VideoArtifactEvidence:
    """Reference-only fake artifact evidence from P07-02."""

    artifact_ref: str
    provider_task_ref: str
    manifest_id: UUID
    state: str
    content_hash: str

    def __post_init__(self) -> None:
        _require_identifier(self.artifact_ref, "artifact_ref_required")
        _require_identifier(self.provider_task_ref, "provider_task_ref_required")
        _require_uuid(self.manifest_id, "manifest_id_required")
        if self.state != "downloaded":
            raise _boundary("artifact_state_required")
        _require_hash(self.content_hash, "artifact_hash_required")

    @classmethod
    def from_summary(cls, summary: Mapping[str, object]) -> "VideoArtifactEvidence":
        if not isinstance(summary, Mapping):
            raise _boundary("artifact_summary_required")
        return cls(
            artifact_ref=str(summary.get("artifact_ref", "")),
            provider_task_ref=str(summary.get("provider_task_ref", "")),
            manifest_id=_coerce_uuid(summary.get("manifest_id"), "manifest_id_required"),
            state=str(summary.get("state", "")),
            content_hash=str(summary.get("content_hash", "")),
        )


@dataclass(frozen=True)
class ProviderQcEvidence:
    """Reference-only provider QC handoff from P07-02."""

    qc_ref: str
    artifact_ref: str
    state: str
    quality_approved: bool
    manual_review_required: bool

    def __post_init__(self) -> None:
        _require_identifier(self.qc_ref, "qc_ref_required")
        _require_identifier(self.artifact_ref, "artifact_ref_required")
        if self.state != "manual_review_required":
            raise _boundary("provider_qc_state_invalid")
        if self.quality_approved is not False:
            raise _boundary("quality_result_forbidden")
        if self.manual_review_required is not True:
            raise _boundary("manual_review_required")

    @classmethod
    def from_summary(cls, summary: Mapping[str, object]) -> "ProviderQcEvidence":
        if not isinstance(summary, Mapping):
            raise _boundary("provider_qc_summary_required")
        return cls(
            qc_ref=str(summary.get("qc_ref", "")),
            artifact_ref=str(summary.get("artifact_ref", "")),
            state=str(summary.get("state", "")),
            quality_approved=summary.get("quality_approved", False),
            manual_review_required=summary.get("manual_review_required", False),
        )


@dataclass(frozen=True)
class VideoTechnicalCheck:
    """Synthetic technical QC vector; no real media decoding is performed here."""

    artifact_ref: str
    artifact_hash: str
    decode_ok: bool
    format_ok: bool
    aspect_ratio: str
    duration_seconds: int
    subtitle_present: bool
    audio_track_present: bool
    origin_label_present: bool
    checked_at: datetime
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.artifact_ref, "artifact_ref_required")
        _require_hash(self.artifact_hash, "artifact_hash_required")
        for value in (
            self.decode_ok,
            self.format_ok,
            self.subtitle_present,
            self.audio_track_present,
            self.origin_label_present,
        ):
            if not isinstance(value, bool):
                raise _boundary("technical_qc_flag_required")
        _require_identifier(self.aspect_ratio, "format_ref_required")
        _require_positive_int(self.duration_seconds, "duration_required")
        _require_time(self.checked_at, "checked_at_required")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_qc_required",
        )


@dataclass(frozen=True)
class VideoQcReport:
    """Automated QC result for internal human review."""

    qc_report_ref: str
    scope: ScopeRef
    manifest_id: UUID
    manifest_version: int
    artifact_ref: str
    provider_qc_ref: str
    state: VideoQcState
    reason_codes: tuple[str, ...]
    locked_fact_versions: tuple[UUID, ...]
    locked_asset_versions: tuple[UUID, ...]
    policy_version: str
    artifact_hash: str
    checked_at: datetime
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    internal_export_allowed: bool = False
    public_publish_allowed: bool = False
    external_publish_attempts: int = 0
    publish_port_present: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.qc_report_ref, "qc_report_ref_required")
        _require_scope(self.scope)
        _require_uuid(self.manifest_id, "manifest_id_required")
        _require_positive_int(self.manifest_version, "manifest_version_required")
        _require_identifier(self.artifact_ref, "artifact_ref_required")
        _require_identifier(self.provider_qc_ref, "qc_ref_required")
        if not isinstance(self.state, VideoQcState):
            raise _boundary("qc_state_required")
        _reason_tuple(list(self.reason_codes))
        if self.state is VideoQcState.PASSED and self.reason_codes:
            raise _boundary("qc_reason_state_mismatch")
        if self.state is not VideoQcState.PASSED and not self.reason_codes:
            raise _boundary("qc_reason_required")
        _require_uuid_tuple(self.locked_fact_versions, "fact_lock_required")
        _require_uuid_tuple(self.locked_asset_versions, "asset_rights_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_hash(self.artifact_hash, "artifact_hash_required")
        _require_time(self.checked_at, "checked_at_required")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_qc_required",
        )
        if self.internal_export_allowed is not False:
            raise _boundary("internal_export_forbidden")
        if self.public_publish_allowed is not False:
            raise _boundary("public_publish_forbidden")
        if self.external_publish_attempts != 0 or self.publish_port_present is not False:
            raise _boundary("external_publish_forbidden")

    def audit_metadata(self) -> dict[str, object]:
        return {
            "qc_state": self.state.value,
            "reason_codes": self.reason_codes,
            "reason_count": len(self.reason_codes),
            "external_publish_attempts": 0,
            "publish_port_present": False,
        }

    def safe_summary(self) -> dict[str, object]:
        return {
            "qc_report_ref": self.qc_report_ref,
            "manifest_id": str(self.manifest_id),
            "manifest_version": self.manifest_version,
            "artifact_ref": self.artifact_ref,
            "provider_qc_ref": self.provider_qc_ref,
            "state": self.state.value,
            "reason_codes": list(self.reason_codes),
            "locked_fact_versions": [str(value) for value in self.locked_fact_versions],
            "locked_asset_versions": [str(value) for value in self.locked_asset_versions],
            "policy_version": self.policy_version,
            "artifact_hash": self.artifact_hash,
            "is_synthetic": True,
            "external_execution_allowed": False,
            "internal_export_allowed": False,
            "public_publish_allowed": False,
            "external_publish_attempts": 0,
            "publish_port_present": False,
        }


@dataclass(frozen=True)
class HumanVideoDecision:
    """Human approval/rejection/revision decision; never a publish action."""

    decision_ref: str
    qc_report_ref: str
    scope: ScopeRef
    action: HumanVideoDecisionAction
    state: HumanVideoDecisionState
    reviewer_ref: str
    decided_at: datetime
    policy_version: str
    revision_ref: str | None = None
    internal_export_approved: bool = False
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    public_publish_allowed: bool = False
    external_publish_attempts: int = 0

    def __post_init__(self) -> None:
        _require_identifier(self.decision_ref, "decision_ref_required")
        _require_identifier(self.qc_report_ref, "qc_report_ref_required")
        _require_scope(self.scope)
        if not isinstance(self.action, HumanVideoDecisionAction):
            raise _boundary("human_decision_action_required")
        if not isinstance(self.state, HumanVideoDecisionState):
            raise _boundary("human_decision_state_required")
        _require_identifier(self.reviewer_ref, "reviewer_ref_required")
        _require_time(self.decided_at, "decided_at_required")
        _require_identifier(self.policy_version, "policy_version_required")
        if self.action is HumanVideoDecisionAction.APPROVE_INTERNAL_EXPORT:
            if self.state is not HumanVideoDecisionState.APPROVED_INTERNAL:
                raise _boundary("human_decision_state_required")
            if self.internal_export_approved is not True:
                raise _boundary("human_approval_required")
        elif self.action is HumanVideoDecisionAction.REJECT:
            if self.state is not HumanVideoDecisionState.REJECTED or self.internal_export_approved is not False:
                raise _boundary("human_decision_state_required")
        elif self.action is HumanVideoDecisionAction.REVISE:
            if self.state is not HumanVideoDecisionState.REVISION_REQUESTED:
                raise _boundary("human_decision_state_required")
            if self.revision_ref is None:
                raise _boundary("revision_ref_required")
            _require_identifier(self.revision_ref, "revision_ref_required")
            if self.internal_export_approved is not False:
                raise _boundary("human_decision_state_required")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_human_decision_required",
        )
        if self.public_publish_allowed is not False or self.external_publish_attempts != 0:
            raise _boundary("external_publish_forbidden")

    def audit_metadata(self) -> dict[str, object]:
        return {
            "decision_state": self.state.value,
            "decision_action": self.action.value,
            "internal_export_approved": self.internal_export_approved,
            "external_publish_attempts": 0,
        }

    def safe_summary(self) -> dict[str, object]:
        return {
            "decision_ref": self.decision_ref,
            "qc_report_ref": self.qc_report_ref,
            "action": self.action.value,
            "state": self.state.value,
            "reviewer_ref": self.reviewer_ref,
            "policy_version": self.policy_version,
            "revision_ref": self.revision_ref,
            "internal_export_approved": self.internal_export_approved,
            "is_synthetic": True,
            "external_execution_allowed": False,
            "public_publish_allowed": False,
            "external_publish_attempts": 0,
        }


@dataclass(frozen=True)
class InternalVideoExportRef:
    """Internal-only reference for approved synthetic video artifacts."""

    export_ref: str
    storage_ref: str
    qc_report_ref: str
    decision_ref: str
    artifact_ref: str
    manifest_id: UUID
    manifest_version: int
    policy_version: str
    state: InternalExportState
    created_at: datetime
    internal_only: bool = True
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    public_publish_allowed: bool = False
    external_publish_attempts: int = 0
    publish_port_present: bool = False

    def __post_init__(self) -> None:
        _require_export_ref(self.export_ref)
        _require_export_ref(self.storage_ref)
        _require_identifier(self.qc_report_ref, "qc_report_ref_required")
        _require_identifier(self.decision_ref, "decision_ref_required")
        _require_identifier(self.artifact_ref, "artifact_ref_required")
        _require_uuid(self.manifest_id, "manifest_id_required")
        _require_positive_int(self.manifest_version, "manifest_version_required")
        _require_identifier(self.policy_version, "policy_version_required")
        if self.state is not InternalExportState.INTERNAL_REFERENCE_READY:
            raise _boundary("internal_export_state_required")
        _require_time(self.created_at, "created_at_required")
        if self.internal_only is not True:
            raise _boundary("internal_export_ref_forbidden")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_internal_export_required",
        )
        if self.public_publish_allowed is not False:
            raise _boundary("public_publish_forbidden")
        if self.external_publish_attempts != 0 or self.publish_port_present is not False:
            raise _boundary("external_publish_forbidden")

    def audit_metadata(self) -> dict[str, object]:
        return {
            "export_state": self.state.value,
            "internal_only": True,
            "external_publish_attempts": 0,
            "publish_port_present": False,
        }

    def safe_summary(self) -> dict[str, object]:
        return {
            "export_ref": self.export_ref,
            "storage_ref": self.storage_ref,
            "qc_report_ref": self.qc_report_ref,
            "decision_ref": self.decision_ref,
            "artifact_ref": self.artifact_ref,
            "manifest_id": str(self.manifest_id),
            "manifest_version": self.manifest_version,
            "policy_version": self.policy_version,
            "state": self.state.value,
            "internal_only": True,
            "is_synthetic": True,
            "external_execution_allowed": False,
            "public_publish_allowed": False,
            "external_publish_attempts": 0,
            "publish_port_present": False,
        }


class VideoQcApprovalWorkflow:
    """Reference-only P07-03 QC, human decision, and internal export workflow."""

    __slots__ = ()

    def run_qc(
        self,
        *,
        manifest: VideoManifestEvidence,
        artifact: VideoArtifactEvidence | None,
        provider_qc: ProviderQcEvidence | None,
        technical_check: VideoTechnicalCheck | None,
        fact_locks: tuple[FactVersionLock, ...],
        asset_locks: tuple[AssetRightsVersionLock, ...],
        policy_lock: PolicyVersionLock,
        current_fact_versions: Mapping[str, UUID],
        current_asset_versions: Mapping[str, UUID],
        current_policy_version: str,
        checked_at: datetime,
        external_publish_requested: bool = False,
    ) -> VideoQcReport:
        if not isinstance(manifest, VideoManifestEvidence):
            raise _boundary("manifest_summary_required")
        checked = _require_time(checked_at, "checked_at_required")
        reasons: list[str] = []
        if external_publish_requested is not False:
            reasons.append("external_publish_forbidden")

        artifact_ref = "artifact_ref:missing"
        provider_qc_ref = "qc_ref:missing"
        artifact_hash = "0" * 64
        if artifact is None:
            reasons.append("artifact_missing")
        elif not isinstance(artifact, VideoArtifactEvidence):
            raise _boundary("artifact_summary_required")
        else:
            artifact_ref = artifact.artifact_ref
            artifact_hash = artifact.content_hash
            if artifact.manifest_id != manifest.manifest_id:
                reasons.append("artifact_manifest_mismatch")
            if artifact.provider_task_ref != manifest.provider_task_ref:
                reasons.append("artifact_provider_mismatch")

        if provider_qc is None:
            reasons.append("provider_qc_missing")
        elif not isinstance(provider_qc, ProviderQcEvidence):
            raise _boundary("provider_qc_summary_required")
        else:
            provider_qc_ref = provider_qc.qc_ref
            if artifact is not None and provider_qc.artifact_ref != artifact.artifact_ref:
                reasons.append("qc_artifact_mismatch")

        if technical_check is None:
            reasons.append("technical_qc_missing")
        elif not isinstance(technical_check, VideoTechnicalCheck):
            raise _boundary("technical_qc_required")
        else:
            if artifact is not None and technical_check.artifact_ref != artifact.artifact_ref:
                reasons.append("qc_artifact_mismatch")
            if artifact is not None and technical_check.artifact_hash != artifact.content_hash:
                reasons.append("artifact_hash_mismatch")
            if technical_check.decode_ok is not True:
                reasons.append("decode_failed")
            if technical_check.format_ok is not True or technical_check.aspect_ratio != "9:16":
                reasons.append("format_invalid")
            if technical_check.subtitle_present is not True:
                reasons.append("subtitle_missing")
            if technical_check.audio_track_present is not True:
                reasons.append("audio_missing")
            if technical_check.origin_label_present is not True:
                reasons.append("origin_label_missing")

        self._validate_fact_locks(manifest, fact_locks, current_fact_versions, checked, reasons)
        self._validate_asset_locks(manifest, asset_locks, current_asset_versions, checked, reasons)
        self._validate_policy_lock(policy_lock, current_policy_version, checked, reasons)

        final_reasons = _reason_tuple(reasons)
        state = _state_for_reasons(final_reasons)
        return VideoQcReport(
            qc_report_ref=_digest("qc_report_ref", manifest.manifest_id, artifact_ref, checked.isoformat()),
            scope=manifest.scope,
            manifest_id=manifest.manifest_id,
            manifest_version=manifest.manifest_version,
            artifact_ref=artifact_ref,
            provider_qc_ref=provider_qc_ref,
            state=state,
            reason_codes=final_reasons,
            locked_fact_versions=manifest.locked_fact_versions,
            locked_asset_versions=manifest.locked_asset_versions,
            policy_version=manifest.policy_version,
            artifact_hash=artifact_hash,
            checked_at=checked,
            is_synthetic=True,
            external_execution_allowed=False,
            internal_export_allowed=False,
            public_publish_allowed=False,
            external_publish_attempts=0,
            publish_port_present=False,
        )

    def record_human_decision(
        self,
        *,
        report: VideoQcReport,
        decision_ref: str,
        action: HumanVideoDecisionAction,
        reviewer_ref: str,
        decided_at: datetime,
        revision_ref: str | None = None,
    ) -> HumanVideoDecision:
        if not isinstance(report, VideoQcReport):
            raise _boundary("qc_report_required")
        if not isinstance(action, HumanVideoDecisionAction):
            raise _boundary("human_decision_action_required")
        decided = _require_time(decided_at, "decided_at_required")
        state: HumanVideoDecisionState
        internal_export_approved = False
        if action is HumanVideoDecisionAction.APPROVE_INTERNAL_EXPORT:
            if report.state is not VideoQcState.PASSED:
                raise _boundary("qc_not_passed")
            state = HumanVideoDecisionState.APPROVED_INTERNAL
            internal_export_approved = True
        elif action is HumanVideoDecisionAction.REJECT:
            state = HumanVideoDecisionState.REJECTED
        else:
            if revision_ref is None:
                raise _boundary("revision_ref_required")
            state = HumanVideoDecisionState.REVISION_REQUESTED

        return HumanVideoDecision(
            decision_ref=decision_ref,
            qc_report_ref=report.qc_report_ref,
            scope=report.scope,
            action=action,
            state=state,
            reviewer_ref=reviewer_ref,
            decided_at=decided,
            policy_version=report.policy_version,
            revision_ref=revision_ref,
            internal_export_approved=internal_export_approved,
            is_synthetic=True,
            external_execution_allowed=False,
            public_publish_allowed=False,
            external_publish_attempts=0,
        )

    def create_internal_export_ref(
        self,
        *,
        report: VideoQcReport,
        decision: HumanVideoDecision,
        export_ref: str,
        storage_ref: str,
        created_at: datetime,
        publish_port_present: bool = False,
    ) -> InternalVideoExportRef:
        if not isinstance(report, VideoQcReport):
            raise _boundary("qc_report_required")
        if not isinstance(decision, HumanVideoDecision):
            raise _boundary("human_decision_required")
        if publish_port_present is not False:
            raise _boundary("external_publish_forbidden")
        if report.state is not VideoQcState.PASSED:
            raise _boundary("qc_not_passed")
        if decision.qc_report_ref != report.qc_report_ref:
            raise _boundary("human_decision_mismatch")
        if decision.state is not HumanVideoDecisionState.APPROVED_INTERNAL:
            raise _boundary("human_approval_required")
        if decision.internal_export_approved is not True:
            raise _boundary("human_approval_required")

        return InternalVideoExportRef(
            export_ref=export_ref,
            storage_ref=storage_ref,
            qc_report_ref=report.qc_report_ref,
            decision_ref=decision.decision_ref,
            artifact_ref=report.artifact_ref,
            manifest_id=report.manifest_id,
            manifest_version=report.manifest_version,
            policy_version=report.policy_version,
            state=InternalExportState.INTERNAL_REFERENCE_READY,
            created_at=_require_time(created_at, "created_at_required"),
            internal_only=True,
            is_synthetic=True,
            external_execution_allowed=False,
            public_publish_allowed=False,
            external_publish_attempts=0,
            publish_port_present=False,
        )

    def _validate_fact_locks(
        self,
        manifest: VideoManifestEvidence,
        locks: tuple[FactVersionLock, ...],
        current_versions: Mapping[str, UUID],
        checked_at: datetime,
        reasons: list[str],
    ) -> None:
        if not isinstance(locks, tuple) or not locks:
            reasons.append("fact_lock_required")
            return
        if not isinstance(current_versions, Mapping):
            raise _boundary("current_fact_versions_required")
        seen: set[str] = set()
        locked_versions: list[UUID] = []
        for lock in locks:
            if not isinstance(lock, FactVersionLock):
                reasons.append("fact_lock_required")
                continue
            if lock.scope != manifest.scope:
                reasons.append("manifest_fact_lock_mismatch")
            if lock.fact_ref in seen:
                reasons.append("fact_lock_duplicate")
            seen.add(lock.fact_ref)
            locked_versions.append(lock.version_id)
            if (
                lock.approval_state is not FactApprovalState.APPROVED
                or lock.data_state is not DataState.FIXTURE
                or lock.source_label != "approved_synthetic"
            ):
                reasons.append("fact_lock_not_current")
            if lock.expires_at <= checked_at:
                reasons.append("fact_lock_expired")
            current = current_versions.get(lock.fact_ref)
            if current is None or current != lock.version_id:
                reasons.append("fact_version_invalidated")
        if tuple(locked_versions) != manifest.locked_fact_versions:
            reasons.append("manifest_fact_lock_mismatch")

    def _validate_asset_locks(
        self,
        manifest: VideoManifestEvidence,
        locks: tuple[AssetRightsVersionLock, ...],
        current_versions: Mapping[str, UUID],
        checked_at: datetime,
        reasons: list[str],
    ) -> None:
        if not isinstance(locks, tuple) or not locks:
            reasons.append("asset_rights_required")
            return
        if not isinstance(current_versions, Mapping):
            raise _boundary("current_asset_versions_required")
        seen: set[str] = set()
        locked_versions: list[UUID] = []
        for lock in locks:
            if not isinstance(lock, AssetRightsVersionLock):
                reasons.append("asset_rights_required")
                continue
            if lock.scope != manifest.scope:
                reasons.append("manifest_asset_lock_mismatch")
            if lock.asset_ref in seen:
                reasons.append("asset_lock_duplicate")
            seen.add(lock.asset_ref)
            locked_versions.append(lock.version_id)
            if lock.origin is AssetOrigin.UNKNOWN:
                reasons.append("asset_origin_unknown")
            if lock.rights_state is AssetRightsState.UNKNOWN:
                reasons.append("asset_rights_unknown")
            if lock.rights_state is AssetRightsState.EXPIRED or lock.expires_at <= checked_at:
                reasons.append("asset_rights_expired")
            current = current_versions.get(lock.asset_ref)
            if current is None or current != lock.version_id:
                reasons.append("asset_version_invalidated")
        if tuple(locked_versions) != manifest.locked_asset_versions:
            reasons.append("manifest_asset_lock_mismatch")

    def _validate_policy_lock(
        self,
        lock: PolicyVersionLock,
        current_policy_version: str,
        checked_at: datetime,
        reasons: list[str],
    ) -> None:
        if not isinstance(lock, PolicyVersionLock):
            raise _boundary("policy_lock_required")
        _require_identifier(current_policy_version, "current_policy_version_required")
        if lock.policy_version != current_policy_version:
            reasons.append("policy_version_invalidated")
        if lock.boundary_state is PolicyBoundaryState.UNKNOWN:
            reasons.append("policy_boundary_unknown")
        if lock.boundary_state is PolicyBoundaryState.EXPIRED:
            reasons.append("policy_lock_expired")
        if lock.expires_at <= checked_at or lock.forbidden_policy.expires_at <= checked_at:
            reasons.append("policy_lock_expired")
