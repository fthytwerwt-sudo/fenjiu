"""P03-03 synthetic approval, publication, and refresh contracts.

This module intentionally does not import or write the P02 truth repository.
It proves an isolated synthetic approval publication path whose records remain
fixtures with external execution disabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
from typing import Optional, Tuple
from uuid import UUID, NAMESPACE_URL, uuid5

from core.contracts import DataState, ScopeRef
from modules.ingestion.contracts import (
    IngestionBoundaryError,
    _reject_sensitive_text,
    _require_aware_time,
    _require_hash,
    _require_identifier,
)
from modules.ingestion.mapping import (
    MappedCandidate,
    MappingEvidenceLineage,
    MappingReport,
    MappingRunState,
)


class ApprovalBoundaryError(IngestionBoundaryError):
    """Stable, value-free P03-03 boundary error."""


class ApprovalAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"
    SUPERSEDE = "supersede"
    REVOKE = "revoke"


class ApprovalRequestState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"
    EXPIRED = "expired"


class RiskLevel(str, Enum):
    LOW = "low"
    HIGH = "high"


class SyntheticTruthStatus(str, Enum):
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


class RefreshConsumer(str, Enum):
    CUSTOMER_SERVICE = "customer_service"
    CONTENT_VIDEO = "content_video"
    CRM = "crm"


def _digest(*parts: object) -> str:
    material = "\x1f".join(str(part) for part in parts)
    return sha256(material.encode("utf-8")).hexdigest()


def _boundary(code: str) -> ApprovalBoundaryError:
    return ApprovalBoundaryError(code)


def _checked_identifier(value: object, code: str) -> str:
    try:
        result = _require_identifier(value, code)
        _reject_sensitive_text(result)
    except IngestionBoundaryError as exc:
        raise ApprovalBoundaryError(exc.code) from exc
    return result


def _checked_hash(value: object, code: str) -> str:
    try:
        return _require_hash(value, code)
    except IngestionBoundaryError as exc:
        raise ApprovalBoundaryError(exc.code) from exc


def _checked_time(value: object, code: str) -> datetime:
    try:
        return _require_aware_time(value, code)
    except IngestionBoundaryError as exc:
        raise ApprovalBoundaryError(exc.code) from exc


def _checked_uuid(value: object, code: str) -> UUID:
    if not isinstance(value, UUID) or value.int == 0:
        raise ApprovalBoundaryError(code)
    return value


def _checked_scope(value: object) -> ScopeRef:
    if not isinstance(value, ScopeRef):
        raise ApprovalBoundaryError("scope_required")
    _checked_identifier(value.correlation_id, "correlation_id_required")
    return value


def _checked_version_no(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ApprovalBoundaryError("version_number_required")
    return value


def _same_scope(expected: ScopeRef, actual: ScopeRef) -> None:
    if actual != expected:
        raise ApprovalBoundaryError("cross_scope_forbidden")


@dataclass(frozen=True)
class _LogicalScopeKey:
    tenant_id: UUID
    project_id: UUID
    business_line_id: UUID


def _logical_scope_key(scope: ScopeRef) -> _LogicalScopeKey:
    return _LogicalScopeKey(
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        business_line_id=scope.business_line_id,
    )


def _id(prefix: str, *parts: object) -> UUID:
    return uuid5(NAMESPACE_URL, "|".join((prefix, *(str(part) for part in parts))))


@dataclass(frozen=True)
class ReviewRequestCommand:
    scope: ScopeRef
    candidate: MappedCandidate
    mapping_report: MappingReport
    subject_ref: str
    fact_type: str
    creator_actor_ref: str
    requested_version_no: int
    risk_level: RiskLevel
    correlation_id: str
    idempotency_key: str
    requested_at: datetime
    expires_at: datetime
    supersedes_version_id: UUID | None = None

    def __post_init__(self) -> None:
        _checked_scope(self.scope)
        if not isinstance(self.candidate, MappedCandidate):
            raise ApprovalBoundaryError("mapped_candidate_required")
        if not isinstance(self.mapping_report, MappingReport):
            raise ApprovalBoundaryError("mapping_report_required")
        _same_scope(self.scope, self.candidate.scope)
        _same_scope(self.scope, self.mapping_report.scope)
        _checked_identifier(self.subject_ref, "subject_ref_required")
        _checked_identifier(self.fact_type, "fact_type_required")
        _checked_identifier(self.creator_actor_ref, "actor_ref_required")
        _checked_version_no(self.requested_version_no)
        if not isinstance(self.risk_level, RiskLevel):
            raise ApprovalBoundaryError("risk_level_required")
        _checked_identifier(self.correlation_id, "correlation_id_required")
        if self.correlation_id != self.scope.correlation_id:
            raise ApprovalBoundaryError("correlation_mismatch")
        _checked_identifier(self.idempotency_key, "idempotency_key_required")
        requested_at = _checked_time(self.requested_at, "requested_at_required")
        expires_at = _checked_time(self.expires_at, "expires_at_required")
        if expires_at <= requested_at:
            raise ApprovalBoundaryError("approval_request_expired")
        if self.supersedes_version_id is not None:
            _checked_uuid(self.supersedes_version_id, "supersedes_version_id_required")


@dataclass(frozen=True)
class HumanDecisionCommand:
    request_id: UUID
    action: ApprovalAction
    actor_ref: str
    decided_at: datetime
    evidence_ref: str
    policy_version: str
    correlation_id: str
    idempotency_key: str
    revision_ref: str | None = None

    def __post_init__(self) -> None:
        _checked_uuid(self.request_id, "approval_request_id_required")
        if not isinstance(self.action, ApprovalAction):
            raise ApprovalBoundaryError("approval_action_required")
        _checked_identifier(self.actor_ref, "actor_ref_required")
        _checked_time(self.decided_at, "decided_at_required")
        _checked_identifier(self.evidence_ref, "approval_evidence_ref_required")
        _checked_identifier(self.policy_version, "approval_policy_version_required")
        _checked_identifier(self.correlation_id, "correlation_id_required")
        _checked_identifier(self.idempotency_key, "idempotency_key_required")
        if self.revision_ref is not None:
            _checked_identifier(self.revision_ref, "revision_ref_required")


@dataclass(frozen=True)
class ApprovalRequest:
    id: UUID
    scope: ScopeRef
    candidate_id: UUID
    source_file_id: UUID
    ingestion_job_id: UUID
    extraction_result_id: UUID
    staging_candidate_id: UUID
    subject_ref: str
    fact_type: str
    target_field: str
    creator_actor_ref: str
    requested_version_no: int
    risk_level: RiskLevel
    state: ApprovalRequestState
    mapping_report_fingerprint: str
    mapping_profile_fingerprint: str
    source_content_hash: str
    normalized_value_hash: str
    profile_id: str
    profile_version: str
    rule_id: str
    correlation_id: str
    idempotency_key: str
    requested_at: datetime
    expires_at: datetime
    supersedes_version_id: UUID | None = None
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _checked_uuid(self.id, "approval_request_id_required")
        _checked_scope(self.scope)
        for value in (
            self.candidate_id,
            self.source_file_id,
            self.ingestion_job_id,
            self.extraction_result_id,
            self.staging_candidate_id,
        ):
            _checked_uuid(value, "mapping_evidence_required")
        for value, code in (
            (self.subject_ref, "subject_ref_required"),
            (self.fact_type, "fact_type_required"),
            (self.target_field, "target_field_required"),
            (self.creator_actor_ref, "actor_ref_required"),
            (self.profile_id, "mapping_profile_required"),
            (self.profile_version, "mapping_profile_required"),
            (self.rule_id, "mapping_rule_required"),
            (self.correlation_id, "correlation_id_required"),
            (self.idempotency_key, "idempotency_key_required"),
        ):
            _checked_identifier(value, code)
        _checked_version_no(self.requested_version_no)
        if not isinstance(self.risk_level, RiskLevel):
            raise ApprovalBoundaryError("risk_level_required")
        if not isinstance(self.state, ApprovalRequestState):
            raise ApprovalBoundaryError("approval_request_state_required")
        _checked_hash(self.mapping_report_fingerprint, "mapping_report_fingerprint_required")
        _checked_hash(self.mapping_profile_fingerprint, "mapping_profile_fingerprint_required")
        _checked_hash(self.source_content_hash, "source_content_hash_required")
        _checked_hash(self.normalized_value_hash, "normalized_value_hash_required")
        _checked_time(self.requested_at, "requested_at_required")
        _checked_time(self.expires_at, "expires_at_required")
        if self.expires_at <= self.requested_at:
            raise ApprovalBoundaryError("approval_request_expired")
        if self.supersedes_version_id is not None:
            _checked_uuid(self.supersedes_version_id, "supersedes_version_id_required")
        if (
            self.is_synthetic is not True
            or self.external_execution_allowed is not False
            or self.business_external_ready is not False
        ):
            raise ApprovalBoundaryError("synthetic_approval_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "state": self.state.value,
            "candidate_id": str(self.candidate_id),
            "version_no": self.requested_version_no,
            "correlation_id": self.correlation_id,
            "is_synthetic": True,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


@dataclass(frozen=True)
class ApprovalDecision:
    id: UUID
    request_id: UUID | None
    action: ApprovalAction
    scope: ScopeRef
    candidate_id: UUID | None
    actor_ref: str
    decided_at: datetime
    evidence_ref: str
    policy_version: str
    requested_version_no: int
    correlation_id: str
    idempotency_key: str
    mapping_report_fingerprint: str | None
    mapping_profile_fingerprint: str | None
    source_file_id: UUID | None
    ingestion_job_id: UUID | None
    extraction_result_id: UUID | None
    staging_candidate_id: UUID | None
    published_version_id: UUID | None = None
    revision_ref: str | None = None
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _checked_uuid(self.id, "approval_decision_id_required")
        if self.request_id is not None:
            _checked_uuid(self.request_id, "approval_request_id_required")
        if not isinstance(self.action, ApprovalAction):
            raise ApprovalBoundaryError("approval_action_required")
        _checked_scope(self.scope)
        if self.candidate_id is not None:
            _checked_uuid(self.candidate_id, "mapped_candidate_required")
        _checked_identifier(self.actor_ref, "actor_ref_required")
        _checked_time(self.decided_at, "decided_at_required")
        _checked_identifier(self.evidence_ref, "approval_evidence_ref_required")
        _checked_identifier(self.policy_version, "approval_policy_version_required")
        _checked_version_no(self.requested_version_no)
        _checked_identifier(self.correlation_id, "correlation_id_required")
        _checked_identifier(self.idempotency_key, "idempotency_key_required")
        if self.mapping_report_fingerprint is not None:
            _checked_hash(self.mapping_report_fingerprint, "mapping_report_fingerprint_required")
        if self.mapping_profile_fingerprint is not None:
            _checked_hash(self.mapping_profile_fingerprint, "mapping_profile_fingerprint_required")
        for value in (
            self.source_file_id,
            self.ingestion_job_id,
            self.extraction_result_id,
            self.staging_candidate_id,
            self.published_version_id,
        ):
            if value is not None:
                _checked_uuid(value, "mapping_evidence_required")
        if self.revision_ref is not None:
            _checked_identifier(self.revision_ref, "revision_ref_required")
        if (
            self.is_synthetic is not True
            or self.external_execution_allowed is not False
            or self.business_external_ready is not False
        ):
            raise ApprovalBoundaryError("synthetic_approval_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "request_id": str(self.request_id) if self.request_id else None,
            "action": self.action.value,
            "published_version_id": str(self.published_version_id) if self.published_version_id else None,
            "version_no": self.requested_version_no,
            "correlation_id": self.correlation_id,
            "is_synthetic": True,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


@dataclass(frozen=True)
class ApprovedSyntheticTruthVersion:
    id: UUID
    scope: ScopeRef
    fact_type: str
    subject_ref: str
    target_field: str
    version_no: int
    parent_version_id: UUID | None
    decision_id: UUID
    candidate_id: UUID
    source_file_id: UUID
    ingestion_job_id: UUID
    extraction_result_id: UUID
    staging_candidate_id: UUID
    mapping_report_fingerprint: str
    mapping_profile_fingerprint: str
    source_content_hash: str
    normalized_value_hash: str
    profile_id: str
    profile_version: str
    rule_id: str
    status: SyntheticTruthStatus
    data_state: DataState
    published_at: datetime
    actor_ref: str
    evidence_ref: str
    policy_version: str
    correlation_id: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _checked_uuid(self.id, "synthetic_truth_version_id_required")
        _checked_scope(self.scope)
        for value in (
            self.decision_id,
            self.candidate_id,
            self.source_file_id,
            self.ingestion_job_id,
            self.extraction_result_id,
            self.staging_candidate_id,
        ):
            _checked_uuid(value, "mapping_evidence_required")
        for value, code in (
            (self.fact_type, "fact_type_required"),
            (self.subject_ref, "subject_ref_required"),
            (self.target_field, "target_field_required"),
            (self.profile_id, "mapping_profile_required"),
            (self.profile_version, "mapping_profile_required"),
            (self.rule_id, "mapping_rule_required"),
            (self.actor_ref, "actor_ref_required"),
            (self.evidence_ref, "approval_evidence_ref_required"),
            (self.policy_version, "approval_policy_version_required"),
            (self.correlation_id, "correlation_id_required"),
        ):
            _checked_identifier(value, code)
        _checked_version_no(self.version_no)
        if self.parent_version_id is not None:
            _checked_uuid(self.parent_version_id, "parent_version_id_required")
        _checked_hash(self.mapping_report_fingerprint, "mapping_report_fingerprint_required")
        _checked_hash(self.mapping_profile_fingerprint, "mapping_profile_fingerprint_required")
        _checked_hash(self.source_content_hash, "source_content_hash_required")
        _checked_hash(self.normalized_value_hash, "normalized_value_hash_required")
        if self.status is not SyntheticTruthStatus.APPROVED:
            raise ApprovalBoundaryError("synthetic_truth_status_required")
        if self.data_state is not DataState.FIXTURE:
            raise ApprovalBoundaryError("p02_truth_isolation_required")
        _checked_time(self.published_at, "published_at_required")
        if (
            self.is_synthetic is not True
            or self.external_execution_allowed is not False
            or self.business_external_ready is not False
        ):
            raise ApprovalBoundaryError("synthetic_truth_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "status": self.status.value,
            "data_state": self.data_state.value,
            "version_no": self.version_no,
            "parent_version_id": str(self.parent_version_id) if self.parent_version_id else None,
            "correlation_id": self.correlation_id,
            "is_synthetic": True,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


@dataclass(frozen=True)
class TruthFactsChanged:
    id: UUID
    scope: ScopeRef
    fact_type: str
    subject_ref: str
    changed_version_id: UUID | None
    invalidated_version_ids: Tuple[UUID, ...]
    consumers: Tuple[RefreshConsumer, ...]
    correlation_id: str
    emitted_at: datetime
    event_type: str = "TruthFactsChanged"
    internal_invalidation_only: bool = True
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _checked_uuid(self.id, "refresh_event_id_required")
        _checked_scope(self.scope)
        _checked_identifier(self.fact_type, "fact_type_required")
        _checked_identifier(self.subject_ref, "subject_ref_required")
        if self.changed_version_id is not None:
            _checked_uuid(self.changed_version_id, "synthetic_truth_version_id_required")
        if not isinstance(self.invalidated_version_ids, tuple):
            raise ApprovalBoundaryError("invalidated_versions_required")
        for value in self.invalidated_version_ids:
            _checked_uuid(value, "invalidated_versions_required")
        if set(self.consumers) != {
            RefreshConsumer.CUSTOMER_SERVICE,
            RefreshConsumer.CONTENT_VIDEO,
            RefreshConsumer.CRM,
        }:
            raise ApprovalBoundaryError("refresh_consumers_required")
        _checked_identifier(self.correlation_id, "correlation_id_required")
        _checked_time(self.emitted_at, "refresh_emitted_at_required")
        if self.event_type != "TruthFactsChanged":
            raise ApprovalBoundaryError("refresh_event_type_required")
        if (
            self.internal_invalidation_only is not True
            or self.is_synthetic is not True
            or self.external_execution_allowed is not False
            or self.business_external_ready is not False
        ):
            raise ApprovalBoundaryError("internal_refresh_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "event_type": self.event_type,
            "changed_version_id": str(self.changed_version_id) if self.changed_version_id else None,
            "invalidated_count": len(self.invalidated_version_ids),
            "consumers": [consumer.value for consumer in self.consumers],
            "correlation_id": self.correlation_id,
            "internal_invalidation_only": True,
            "is_synthetic": True,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


@dataclass(frozen=True)
class ApprovalAuditEvent:
    id: UUID
    sequence: int
    scope: ScopeRef
    event_kind: str
    actor_ref: str
    target_ref: str
    correlation_id: str
    occurred_at: datetime
    decision_id: UUID | None = None
    request_id: UUID | None = None
    data_version_id: UUID | None = None
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _checked_uuid(self.id, "audit_event_id_required")
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 1:
            raise ApprovalBoundaryError("audit_sequence_required")
        _checked_scope(self.scope)
        _checked_identifier(self.event_kind, "audit_event_kind_required")
        _checked_identifier(self.actor_ref, "actor_ref_required")
        _checked_identifier(self.target_ref, "audit_target_ref_required")
        _checked_identifier(self.correlation_id, "correlation_id_required")
        _checked_time(self.occurred_at, "audit_occurred_at_required")
        for value in (self.decision_id, self.request_id, self.data_version_id):
            if value is not None:
                _checked_uuid(value, "audit_ref_required")
        if (
            self.is_synthetic is not True
            or self.external_execution_allowed is not False
            or self.business_external_ready is not False
        ):
            raise ApprovalBoundaryError("synthetic_audit_required")


class SyntheticApprovalPublisher:
    """In-memory synthetic approval publisher with append-only evidence."""

    def __init__(self, *, now=None) -> None:
        self._now = now
        self._requests: list[ApprovalRequest] = []
        self._request_state: dict[UUID, ApprovalRequestState] = {}
        self._request_by_id: dict[UUID, ApprovalRequest] = {}
        self._request_by_idempotency: dict[str, ApprovalRequest] = {}
        self._decisions: list[ApprovalDecision] = []
        self._decision_by_idempotency: dict[str, ApprovalDecision] = {}
        self._decision_by_request: dict[UUID, ApprovalDecision] = {}
        self._versions: list[ApprovedSyntheticTruthVersion] = []
        self._version_by_id: dict[UUID, ApprovedSyntheticTruthVersion] = {}
        self._status_by_version: dict[UUID, SyntheticTruthStatus] = {}
        self._current_by_key: dict[tuple[_LogicalScopeKey, str, str], UUID] = {}
        self._refresh_events: list[TruthFactsChanged] = []
        self._audit_events: list[ApprovalAuditEvent] = []

    @property
    def requests(self) -> tuple[ApprovalRequest, ...]:
        return tuple(self._requests)

    @property
    def decisions(self) -> tuple[ApprovalDecision, ...]:
        return tuple(self._decisions)

    @property
    def approved_versions(self) -> tuple[ApprovedSyntheticTruthVersion, ...]:
        return tuple(self._versions)

    @property
    def refresh_events(self) -> tuple[TruthFactsChanged, ...]:
        return tuple(self._refresh_events)

    @property
    def audit_events(self) -> tuple[ApprovalAuditEvent, ...]:
        return tuple(self._audit_events)

    def snapshot_counts(self) -> dict[str, int]:
        return {
            "requests": len(self._requests),
            "decisions": len(self._decisions),
            "versions": len(self._versions),
            "refresh_events": len(self._refresh_events),
            "audit_events": len(self._audit_events),
        }

    def request_review(self, command: ReviewRequestCommand) -> ApprovalRequest:
        if not isinstance(command, ReviewRequestCommand):
            raise ApprovalBoundaryError("approval_request_command_required")
        existing = self._request_by_idempotency.get(command.idempotency_key)
        if existing is not None:
            self._assert_quality_passed(command)
            rerun = self._request_from(command)
            if rerun != existing:
                raise ApprovalBoundaryError("idempotency_conflict")
            return existing
        self._assert_quality_passed(command)
        request = self._request_from(command)
        audit = self._audit(
            scope=request.scope,
            actor_ref=request.creator_actor_ref,
            event_kind="approval_request_created",
            target_ref=request.subject_ref,
            occurred_at=request.requested_at,
            request_id=request.id,
            correlation_id=request.correlation_id,
        )
        self._requests.append(request)
        self._request_by_id[request.id] = request
        self._request_state[request.id] = request.state
        self._request_by_idempotency[request.idempotency_key] = request
        self._audit_events.append(audit)
        return request

    def decide(self, command: HumanDecisionCommand) -> ApprovalDecision:
        if not isinstance(command, HumanDecisionCommand):
            raise ApprovalBoundaryError("human_decision_command_required")
        existing = self._decision_by_idempotency.get(command.idempotency_key)
        if existing is not None:
            self._assert_decision_rerun(existing, command)
            return existing
        request = self._request_by_id.get(command.request_id)
        if request is None:
            raise ApprovalBoundaryError("approval_request_not_found")
        if command.correlation_id != request.correlation_id:
            raise ApprovalBoundaryError("correlation_mismatch")
        state = self._request_state.get(request.id)
        if state is ApprovalRequestState.EXPIRED:
            raise ApprovalBoundaryError("approval_request_expired")
        if state is not ApprovalRequestState.PENDING:
            raise ApprovalBoundaryError("duplicate_decision")
        if command.decided_at >= request.expires_at:
            self._expire_request(
                request=request,
                actor_ref=command.actor_ref,
                occurred_at=command.decided_at,
            )
            raise ApprovalBoundaryError("approval_request_expired")
        if command.action is ApprovalAction.REVOKE:
            raise ApprovalBoundaryError("revoke_uses_version_command")

        if command.action in {ApprovalAction.APPROVE, ApprovalAction.SUPERSEDE}:
            return self._publish_decision(request, command)
        return self._non_publish_decision(request, command)

    def revoke(
        self,
        *,
        version_id: UUID,
        actor_ref: str,
        decided_at: datetime,
        evidence_ref: str,
        policy_version: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> ApprovalDecision:
        _checked_uuid(version_id, "synthetic_truth_version_id_required")
        actor = _checked_identifier(actor_ref, "actor_ref_required")
        decided = _checked_time(decided_at, "decided_at_required")
        evidence = _checked_identifier(evidence_ref, "approval_evidence_ref_required")
        policy = _checked_identifier(policy_version, "approval_policy_version_required")
        correlation = _checked_identifier(correlation_id, "correlation_id_required")
        key = _checked_identifier(idempotency_key, "idempotency_key_required")
        existing = self._decision_by_idempotency.get(key)
        if existing is not None:
            if (
                existing.action is not ApprovalAction.REVOKE
                or existing.published_version_id != version_id
                or existing.actor_ref != actor
                or existing.decided_at != decided
                or existing.evidence_ref != evidence
                or existing.policy_version != policy
                or existing.correlation_id != correlation
            ):
                raise ApprovalBoundaryError("idempotency_conflict")
            return existing
        version = self._version_by_id.get(version_id)
        if version is None:
            raise ApprovalBoundaryError("synthetic_truth_version_not_found")
        if correlation != version.correlation_id:
            raise ApprovalBoundaryError("correlation_mismatch")
        if self._status_by_version.get(version_id) is not SyntheticTruthStatus.APPROVED:
            raise ApprovalBoundaryError("synthetic_truth_version_not_current")

        decision = ApprovalDecision(
            id=_id("p03-03-decision", key),
            request_id=None,
            action=ApprovalAction.REVOKE,
            scope=version.scope,
            candidate_id=version.candidate_id,
            actor_ref=actor,
            decided_at=decided,
            evidence_ref=evidence,
            policy_version=policy,
            requested_version_no=version.version_no,
            correlation_id=correlation,
            idempotency_key=key,
            mapping_report_fingerprint=version.mapping_report_fingerprint,
            mapping_profile_fingerprint=version.mapping_profile_fingerprint,
            source_file_id=version.source_file_id,
            ingestion_job_id=version.ingestion_job_id,
            extraction_result_id=version.extraction_result_id,
            staging_candidate_id=version.staging_candidate_id,
            published_version_id=version.id,
        )
        refresh = self._refresh(
            scope=version.scope,
            fact_type=version.fact_type,
            subject_ref=version.subject_ref,
            changed_version_id=None,
            invalidated_version_ids=(version.id,),
            correlation_id=correlation,
            emitted_at=decided,
            key=key,
        )
        audit = self._audit(
            scope=version.scope,
            actor_ref=actor,
            event_kind="synthetic_truth_revoked",
            target_ref=version.subject_ref,
            occurred_at=decided,
            decision_id=decision.id,
            data_version_id=version.id,
            correlation_id=correlation,
        )
        self._decisions.append(decision)
        self._decision_by_idempotency[key] = decision
        self._status_by_version[version.id] = SyntheticTruthStatus.REVOKED
        self._current_by_key.pop(
            (_logical_scope_key(version.scope), version.fact_type, version.subject_ref),
            None,
        )
        self._refresh_events.append(refresh)
        self._audit_events.append(audit)
        return decision

    def current(
        self,
        scope: ScopeRef,
        fact_type: str,
        subject_ref: str,
    ) -> ApprovedSyntheticTruthVersion | None:
        scoped = _checked_scope(scope)
        fact = _checked_identifier(fact_type, "fact_type_required")
        subject = _checked_identifier(subject_ref, "subject_ref_required")
        version_id = self._current_by_key.get((_logical_scope_key(scoped), fact, subject))
        if version_id is None:
            return None
        version = self._version_by_id[version_id]
        if self._status_by_version.get(version_id) is not SyntheticTruthStatus.APPROVED:
            return None
        return version

    def read_version(self, version_id: UUID) -> ApprovedSyntheticTruthVersion | None:
        _checked_uuid(version_id, "synthetic_truth_version_id_required")
        version = self._version_by_id.get(version_id)
        if version is None:
            return None
        current = self.current(version.scope, version.fact_type, version.subject_ref)
        if current is None or current.id != version.id:
            return None
        return current

    def current_candidate(self, scope: ScopeRef, candidate_id: UUID) -> None:
        _checked_scope(scope)
        _checked_uuid(candidate_id, "mapped_candidate_required")
        return None

    def request_state(self, request_id: UUID) -> ApprovalRequestState:
        _checked_uuid(request_id, "approval_request_id_required")
        state = self._request_state.get(request_id)
        if state is None:
            raise ApprovalBoundaryError("approval_request_not_found")
        return state

    def version_status(self, version_id: UUID) -> SyntheticTruthStatus:
        _checked_uuid(version_id, "synthetic_truth_version_id_required")
        status = self._status_by_version.get(version_id)
        if status is None:
            raise ApprovalBoundaryError("synthetic_truth_version_not_found")
        return status

    def _assert_quality_passed(self, command: ReviewRequestCommand) -> None:
        report = command.mapping_report
        candidate = command.candidate
        if report.state is not MappingRunState.MAPPED or report.findings:
            raise ApprovalBoundaryError("quality_not_passed")
        if candidate.state is not MappingRunState.MAPPED:
            raise ApprovalBoundaryError("quality_not_passed")
        if (
            candidate.data_state is not DataState.FIXTURE
            or candidate.is_synthetic is not True
            or candidate.external_execution_allowed is not False
            or candidate.business_external_ready is not False
        ):
            raise ApprovalBoundaryError("synthetic_candidate_required")
        if candidate not in report.candidates:
            raise ApprovalBoundaryError("mapped_candidate_required")
        if report.profile_fingerprint is None:
            raise ApprovalBoundaryError("mapping_profile_required")
        if not any(self._lineage_matches(lineage, candidate) for lineage in report.input_evidence_ids):
            raise ApprovalBoundaryError("mapping_evidence_required")

    @staticmethod
    def _lineage_matches(lineage: MappingEvidenceLineage, candidate: MappedCandidate) -> bool:
        return (
            lineage.source_file_id == candidate.source_file_id
            and lineage.ingestion_job_id == candidate.ingestion_job_id
            and lineage.extraction_result_id == candidate.extraction_result_id
            and lineage.staging_candidate_id == candidate.staging_candidate_id
            and lineage.locator == candidate.locator
        )

    def _request_from(self, command: ReviewRequestCommand) -> ApprovalRequest:
        candidate = command.candidate
        return ApprovalRequest(
            id=_id("p03-03-request", command.scope, command.idempotency_key),
            scope=command.scope,
            candidate_id=candidate.id,
            source_file_id=candidate.source_file_id,
            ingestion_job_id=candidate.ingestion_job_id,
            extraction_result_id=candidate.extraction_result_id,
            staging_candidate_id=candidate.staging_candidate_id,
            subject_ref=command.subject_ref,
            fact_type=command.fact_type,
            target_field=candidate.target_field,
            creator_actor_ref=command.creator_actor_ref,
            requested_version_no=command.requested_version_no,
            risk_level=command.risk_level,
            state=ApprovalRequestState.PENDING,
            mapping_report_fingerprint=command.mapping_report.run_fingerprint,
            mapping_profile_fingerprint=command.mapping_report.profile_fingerprint or "",
            source_content_hash=candidate.source_content_hash,
            normalized_value_hash=candidate.normalized_value_hash,
            profile_id=candidate.profile_id,
            profile_version=candidate.profile_version,
            rule_id=candidate.rule_id,
            correlation_id=command.correlation_id,
            idempotency_key=command.idempotency_key,
            requested_at=command.requested_at,
            expires_at=command.expires_at,
            supersedes_version_id=command.supersedes_version_id,
        )

    def _publish_decision(
        self,
        request: ApprovalRequest,
        command: HumanDecisionCommand,
    ) -> ApprovalDecision:
        if request.risk_level is RiskLevel.HIGH and command.actor_ref == request.creator_actor_ref:
            raise ApprovalBoundaryError("self_approval_forbidden")
        key = (_logical_scope_key(request.scope), request.fact_type, request.subject_ref)
        current_id = self._current_by_key.get(key)
        parent_version_id = None
        invalidated_version_ids: tuple[UUID, ...] = ()
        if command.action is ApprovalAction.APPROVE:
            if request.supersedes_version_id is not None or current_id is not None:
                raise ApprovalBoundaryError("publication_supersede_required")
            expected_version_no = 1
        elif command.action is ApprovalAction.SUPERSEDE:
            if request.supersedes_version_id is None:
                raise ApprovalBoundaryError("supersedes_version_id_required")
            if current_id != request.supersedes_version_id:
                raise ApprovalBoundaryError("version_conflict")
            current = self._version_by_id.get(current_id)
            if current is None or self._status_by_version.get(current.id) is not SyntheticTruthStatus.APPROVED:
                raise ApprovalBoundaryError("version_conflict")
            expected_version_no = current.version_no + 1
            parent_version_id = current.id
            invalidated_version_ids = (current.id,)
        else:
            raise ApprovalBoundaryError("approval_action_required")
        if request.requested_version_no != expected_version_no:
            raise ApprovalBoundaryError("version_conflict")

        decision_id = _id("p03-03-decision", command.idempotency_key)
        version_id = _id("p03-03-version", request.id, command.idempotency_key)
        decision = self._decision(
            request=request,
            command=command,
            decision_id=decision_id,
            published_version_id=version_id,
        )
        version = ApprovedSyntheticTruthVersion(
            id=version_id,
            scope=request.scope,
            fact_type=request.fact_type,
            subject_ref=request.subject_ref,
            target_field=request.target_field,
            version_no=request.requested_version_no,
            parent_version_id=parent_version_id,
            decision_id=decision.id,
            candidate_id=request.candidate_id,
            source_file_id=request.source_file_id,
            ingestion_job_id=request.ingestion_job_id,
            extraction_result_id=request.extraction_result_id,
            staging_candidate_id=request.staging_candidate_id,
            mapping_report_fingerprint=request.mapping_report_fingerprint,
            mapping_profile_fingerprint=request.mapping_profile_fingerprint,
            source_content_hash=request.source_content_hash,
            normalized_value_hash=request.normalized_value_hash,
            profile_id=request.profile_id,
            profile_version=request.profile_version,
            rule_id=request.rule_id,
            status=SyntheticTruthStatus.APPROVED,
            data_state=DataState.FIXTURE,
            published_at=command.decided_at,
            actor_ref=command.actor_ref,
            evidence_ref=command.evidence_ref,
            policy_version=command.policy_version,
            correlation_id=command.correlation_id,
        )
        refresh = self._refresh(
            scope=request.scope,
            fact_type=request.fact_type,
            subject_ref=request.subject_ref,
            changed_version_id=version.id,
            invalidated_version_ids=invalidated_version_ids,
            correlation_id=command.correlation_id,
            emitted_at=command.decided_at,
            key=command.idempotency_key,
        )
        decision_audit = self._audit(
            scope=request.scope,
            actor_ref=command.actor_ref,
            event_kind="approval_decision_appended",
            target_ref=request.subject_ref,
            occurred_at=command.decided_at,
            request_id=request.id,
            decision_id=decision.id,
            correlation_id=command.correlation_id,
            sequence_offset=1,
        )
        publish_audit = self._audit(
            scope=request.scope,
            actor_ref=command.actor_ref,
            event_kind="synthetic_truth_published",
            target_ref=request.subject_ref,
            occurred_at=command.decided_at,
            request_id=request.id,
            decision_id=decision.id,
            data_version_id=version.id,
            correlation_id=command.correlation_id,
            sequence_offset=2,
        )

        self._decisions.append(decision)
        self._decision_by_idempotency[command.idempotency_key] = decision
        self._decision_by_request[request.id] = decision
        self._request_state[request.id] = ApprovalRequestState.APPROVED
        self._versions.append(version)
        self._version_by_id[version.id] = version
        self._status_by_version[version.id] = SyntheticTruthStatus.APPROVED
        for invalidated in invalidated_version_ids:
            self._status_by_version[invalidated] = SyntheticTruthStatus.SUPERSEDED
        self._current_by_key[key] = version.id
        self._refresh_events.append(refresh)
        self._audit_events.extend((decision_audit, publish_audit))
        return decision

    def _non_publish_decision(
        self,
        request: ApprovalRequest,
        command: HumanDecisionCommand,
    ) -> ApprovalDecision:
        if command.action is ApprovalAction.REVISE and command.revision_ref is None:
            raise ApprovalBoundaryError("revision_ref_required")
        if command.action not in {ApprovalAction.REJECT, ApprovalAction.REVISE}:
            raise ApprovalBoundaryError("approval_action_required")
        decision = self._decision(
            request=request,
            command=command,
            decision_id=_id("p03-03-decision", command.idempotency_key),
            published_version_id=None,
        )
        audit = self._audit(
            scope=request.scope,
            actor_ref=command.actor_ref,
            event_kind="approval_decision_appended",
            target_ref=request.subject_ref,
            occurred_at=command.decided_at,
            request_id=request.id,
            decision_id=decision.id,
            correlation_id=command.correlation_id,
        )
        self._decisions.append(decision)
        self._decision_by_idempotency[command.idempotency_key] = decision
        self._decision_by_request[request.id] = decision
        self._request_state[request.id] = (
            ApprovalRequestState.REJECTED
            if command.action is ApprovalAction.REJECT
            else ApprovalRequestState.REVISED
        )
        self._audit_events.append(audit)
        return decision

    def _expire_request(
        self,
        *,
        request: ApprovalRequest,
        actor_ref: str,
        occurred_at: datetime,
    ) -> None:
        if self._request_state.get(request.id) is ApprovalRequestState.EXPIRED:
            return
        audit = self._audit(
            scope=request.scope,
            actor_ref=actor_ref,
            event_kind="approval_request_expired",
            target_ref=request.subject_ref,
            occurred_at=occurred_at,
            request_id=request.id,
            correlation_id=request.correlation_id,
        )
        self._request_state[request.id] = ApprovalRequestState.EXPIRED
        self._audit_events.append(audit)

    @staticmethod
    def _decision(
        *,
        request: ApprovalRequest,
        command: HumanDecisionCommand,
        decision_id: UUID,
        published_version_id: UUID | None,
    ) -> ApprovalDecision:
        return ApprovalDecision(
            id=decision_id,
            request_id=request.id,
            action=command.action,
            scope=request.scope,
            candidate_id=request.candidate_id,
            actor_ref=command.actor_ref,
            decided_at=command.decided_at,
            evidence_ref=command.evidence_ref,
            policy_version=command.policy_version,
            requested_version_no=request.requested_version_no,
            correlation_id=command.correlation_id,
            idempotency_key=command.idempotency_key,
            mapping_report_fingerprint=request.mapping_report_fingerprint,
            mapping_profile_fingerprint=request.mapping_profile_fingerprint,
            source_file_id=request.source_file_id,
            ingestion_job_id=request.ingestion_job_id,
            extraction_result_id=request.extraction_result_id,
            staging_candidate_id=request.staging_candidate_id,
            published_version_id=published_version_id,
            revision_ref=command.revision_ref,
        )

    @staticmethod
    def _assert_decision_rerun(
        existing: ApprovalDecision,
        command: HumanDecisionCommand,
    ) -> None:
        if (
            existing.request_id != command.request_id
            or existing.action is not command.action
            or existing.actor_ref != command.actor_ref
            or existing.decided_at != command.decided_at
            or existing.evidence_ref != command.evidence_ref
            or existing.policy_version != command.policy_version
            or existing.correlation_id != command.correlation_id
            or existing.revision_ref != command.revision_ref
        ):
            raise ApprovalBoundaryError("idempotency_conflict")

    def _refresh(
        self,
        *,
        scope: ScopeRef,
        fact_type: str,
        subject_ref: str,
        changed_version_id: UUID | None,
        invalidated_version_ids: tuple[UUID, ...],
        correlation_id: str,
        emitted_at: datetime,
        key: str,
    ) -> TruthFactsChanged:
        return TruthFactsChanged(
            id=_id("p03-03-refresh", key),
            scope=scope,
            fact_type=fact_type,
            subject_ref=subject_ref,
            changed_version_id=changed_version_id,
            invalidated_version_ids=invalidated_version_ids,
            consumers=(
                RefreshConsumer.CUSTOMER_SERVICE,
                RefreshConsumer.CONTENT_VIDEO,
                RefreshConsumer.CRM,
            ),
            correlation_id=correlation_id,
            emitted_at=emitted_at,
        )

    def _audit(
        self,
        *,
        scope: ScopeRef,
        actor_ref: str,
        event_kind: str,
        target_ref: str,
        occurred_at: datetime,
        correlation_id: str,
        decision_id: UUID | None = None,
        request_id: UUID | None = None,
        data_version_id: UUID | None = None,
        sequence_offset: int = 1,
    ) -> ApprovalAuditEvent:
        sequence = len(self._audit_events) + sequence_offset
        return ApprovalAuditEvent(
            id=_id("p03-03-audit", correlation_id, sequence),
            sequence=sequence,
            scope=scope,
            event_kind=event_kind,
            actor_ref=actor_ref,
            target_ref=target_ref,
            correlation_id=correlation_id,
            occurred_at=occurred_at,
            decision_id=decision_id,
            request_id=request_id,
            data_version_id=data_version_id,
        )


__all__ = [
    "ApprovalAction",
    "ApprovalAuditEvent",
    "ApprovalBoundaryError",
    "ApprovalDecision",
    "ApprovalRequest",
    "ApprovalRequestState",
    "ApprovedSyntheticTruthVersion",
    "HumanDecisionCommand",
    "RefreshConsumer",
    "ReviewRequestCommand",
    "RiskLevel",
    "SyntheticApprovalPublisher",
    "SyntheticTruthStatus",
    "TruthFactsChanged",
]
