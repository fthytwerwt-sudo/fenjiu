"""P03-03 synthetic approval and internal publication proof contracts.

This module deliberately does not import or write the P02 truth center.  A
synthetic internal publication is an immutable local proof that a quality-passed
candidate completed the approval workflow; it is not P02 current truth and it is
not externally executable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Callable, Dict, Optional, Tuple
from uuid import UUID, NAMESPACE_URL, uuid5

from core.contracts import DataState, ScopeRef
from modules.ingestion.contracts import (
    IngestionBoundaryError,
    _reject_sensitive_text,
    _require_aware_time,
    _require_hash,
    _require_identifier,
)
from modules.ingestion.mapping import MappedCandidate, MappingRunState


class ApprovalBoundaryError(IngestionBoundaryError):
    """Stable fail-closed P03-03 boundary error."""


class ApprovalRequestState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVISION_REQUESTED = "revision_requested"
    CONFLICT = "conflict"


class ApprovalDecisionKind(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    EXPIRE = "expire"
    REVISE = "revise"
    MARK_CONFLICT = "mark_conflict"


class InternalPublicationState(str, Enum):
    APPROVED_INTERNAL = "approved_internal"
    SUPERSEDED_INTERNAL = "superseded_internal"


_DECISION_TO_STATE = {
    ApprovalDecisionKind.APPROVE: ApprovalRequestState.APPROVED,
    ApprovalDecisionKind.REJECT: ApprovalRequestState.REJECTED,
    ApprovalDecisionKind.EXPIRE: ApprovalRequestState.EXPIRED,
    ApprovalDecisionKind.REVISE: ApprovalRequestState.REVISION_REQUESTED,
    ApprovalDecisionKind.MARK_CONFLICT: ApprovalRequestState.CONFLICT,
}
_PUBLICATION_TRANSITIONS = {
    InternalPublicationState.APPROVED_INTERNAL: frozenset(
        {InternalPublicationState.SUPERSEDED_INTERNAL}
    ),
    InternalPublicationState.SUPERSEDED_INTERNAL: frozenset(
        {InternalPublicationState.APPROVED_INTERNAL}
    ),
}


def _digest(*parts: object) -> str:
    material = "\x1f".join(str(part) for part in parts)
    return sha256(material.encode("utf-8")).hexdigest()


def _uuid_for(*parts: object) -> UUID:
    return uuid5(NAMESPACE_URL, _digest(*parts))


def _require_uuid(value: object, code: str) -> None:
    if not isinstance(value, UUID) or value.int == 0:
        raise ApprovalBoundaryError(code)


def _require_scope(value: object, code: str) -> ScopeRef:
    if not isinstance(value, ScopeRef):
        raise ApprovalBoundaryError(code)
    try:
        _reject_sensitive_text(value.correlation_id)
    except IngestionBoundaryError as exc:
        raise ApprovalBoundaryError(code) from exc
    return value


def _require_safe_identifier(value: object, code: str) -> str:
    try:
        result = _require_identifier(value, code)
        _reject_sensitive_text(result)
    except IngestionBoundaryError as exc:
        raise ApprovalBoundaryError(code) from exc
    return result


def _require_safe_hash(value: object, code: str) -> str:
    try:
        return _require_hash(value, code)
    except IngestionBoundaryError as exc:
        raise ApprovalBoundaryError(code) from exc


def _require_safe_time(value: object, code: str) -> datetime:
    try:
        checked = _require_aware_time(value, code)
    except IngestionBoundaryError as exc:
        raise ApprovalBoundaryError(code) from exc
    return checked


def _require_quality_passed_candidate(candidate: object) -> MappedCandidate:
    if not isinstance(candidate, MappedCandidate):
        raise ApprovalBoundaryError("quality_passed_candidate_required")
    if candidate.state is not MappingRunState.MAPPED:
        raise ApprovalBoundaryError("quality_passed_candidate_required")
    if candidate.data_state is not DataState.FIXTURE or candidate.is_synthetic is not True:
        raise ApprovalBoundaryError("synthetic_input_required")
    if candidate.external_execution_allowed is not False:
        raise ApprovalBoundaryError("external_execution_forbidden")
    if candidate.business_external_ready is not False:
        raise ApprovalBoundaryError("business_external_ready_forbidden")
    _require_safe_hash(candidate.source_content_hash, "candidate_lineage_invalid")
    _require_safe_hash(candidate.normalized_value_hash, "candidate_lineage_invalid")
    _require_safe_identifier(candidate.target_field, "candidate_lineage_invalid")
    _require_safe_identifier(candidate.profile_id, "candidate_lineage_invalid")
    _require_safe_identifier(candidate.profile_version, "candidate_lineage_invalid")
    _require_safe_identifier(candidate.rule_id, "candidate_lineage_invalid")
    if not candidate.locator.has_traceable_location:
        raise ApprovalBoundaryError("candidate_lineage_invalid")
    return candidate


@dataclass(frozen=True)
class ApprovalAuditEvent:
    id: UUID
    scope: ScopeRef
    request_id: UUID
    sequence: int
    actor_ref: str
    action: str
    state: ApprovalRequestState
    policy_version: str
    evidence_ref: str
    recorded_at: datetime
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "approval_audit_id_required")
        _require_scope(self.scope, "scope_required")
        _require_uuid(self.request_id, "approval_request_id_required")
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 1:
            raise ApprovalBoundaryError("approval_audit_sequence_required")
        for value, code in (
            (self.actor_ref, "approval_actor_ref_required"),
            (self.action, "approval_audit_action_required"),
            (self.policy_version, "approval_policy_version_required"),
            (self.evidence_ref, "approval_evidence_ref_required"),
        ):
            _require_safe_identifier(value, code)
        if not isinstance(self.state, ApprovalRequestState):
            raise ApprovalBoundaryError("approval_state_required")
        _require_safe_time(self.recorded_at, "approval_audit_time_required")
        _require_internal_markers(
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "request_id": str(self.request_id),
            "sequence": self.sequence,
            "action": self.action,
            "state": self.state.value,
            "policy_version": self.policy_version,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


@dataclass(frozen=True)
class ApprovalRequest:
    id: UUID
    scope: ScopeRef
    candidate: MappedCandidate
    subject_ref: str
    requested_by: str
    evidence_ref: str
    policy_version: str
    requested_at: datetime
    expires_at: datetime
    idempotency_key: str
    request_fingerprint: str
    state: ApprovalRequestState = ApprovalRequestState.PENDING
    version_no: int = 1
    decision_id: Optional[UUID] = None
    decision_kind: Optional[ApprovalDecisionKind] = None
    decision_actor_ref: Optional[str] = None
    decision_evidence_ref: Optional[str] = None
    decided_at: Optional[datetime] = None
    is_synthetic: bool = True
    p02_current_truth_readable: bool = False
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "approval_request_id_required")
        _require_scope(self.scope, "scope_required")
        candidate = _require_quality_passed_candidate(self.candidate)
        if candidate.scope != self.scope:
            raise ApprovalBoundaryError("cross_scope_forbidden")
        for value, code in (
            (self.subject_ref, "approval_subject_ref_required"),
            (self.requested_by, "approval_request_actor_required"),
            (self.evidence_ref, "approval_evidence_ref_required"),
            (self.policy_version, "approval_policy_version_required"),
            (self.idempotency_key, "approval_idempotency_key_required"),
        ):
            _require_safe_identifier(value, code)
        _require_safe_hash(self.request_fingerprint, "approval_request_fingerprint_required")
        requested_at = _require_safe_time(self.requested_at, "approval_requested_at_required")
        expires_at = _require_safe_time(self.expires_at, "approval_expires_at_required")
        if expires_at <= requested_at:
            raise ApprovalBoundaryError("approval_expiry_window_invalid")
        if not isinstance(self.state, ApprovalRequestState):
            raise ApprovalBoundaryError("approval_state_required")
        if not isinstance(self.version_no, int) or isinstance(self.version_no, bool) or self.version_no < 1:
            raise ApprovalBoundaryError("approval_request_version_required")
        decision_fields = (
            self.decision_id,
            self.decision_kind,
            self.decision_actor_ref,
            self.decision_evidence_ref,
            self.decided_at,
        )
        if self.state is ApprovalRequestState.PENDING:
            if any(value is not None for value in decision_fields):
                raise ApprovalBoundaryError("approval_pending_decision_forbidden")
        else:
            if any(value is None for value in decision_fields):
                raise ApprovalBoundaryError("approval_decision_required")
            _require_uuid(self.decision_id, "approval_decision_id_required")
            if not isinstance(self.decision_kind, ApprovalDecisionKind):
                raise ApprovalBoundaryError("approval_decision_required")
            if _DECISION_TO_STATE[self.decision_kind] is not self.state:
                raise ApprovalBoundaryError("approval_decision_state_mismatch")
            _require_safe_identifier(
                self.decision_actor_ref,
                "approval_decision_actor_required",
            )
            _require_safe_identifier(
                self.decision_evidence_ref,
                "approval_decision_evidence_required",
            )
            _require_safe_time(self.decided_at, "approval_decided_at_required")
            if (
                self.decision_kind is ApprovalDecisionKind.APPROVE
                and self.decision_actor_ref == self.requested_by
            ):
                raise ApprovalBoundaryError("self_approval_forbidden")
        _require_internal_markers(
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )
        if self.p02_current_truth_readable is not False:
            raise ApprovalBoundaryError("p02_current_truth_forbidden")

    @property
    def decision_ref(self) -> str:
        if self.decision_id is None:
            raise ApprovalBoundaryError("approval_decision_required")
        return f"decision:{self.decision_id.hex}"

    def safe_summary(self) -> dict[str, object]:
        return {
            "request_id": str(self.id),
            "state": self.state.value,
            "version_no": self.version_no,
            "subject_ref": self.subject_ref,
            "target_field": self.candidate.target_field,
            "profile_id": self.candidate.profile_id,
            "profile_version": self.candidate.profile_version,
            "p02_current_truth_readable": False,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


@dataclass(frozen=True)
class InternalPublicationRecord:
    id: UUID
    scope: ScopeRef
    request_id: UUID
    decision_id: UUID
    candidate_id: UUID
    subject_ref: str
    target_field: str
    version_no: int
    state: InternalPublicationState
    payload_hash: str
    source_content_hash: str
    source_file_id: UUID
    ingestion_job_id: UUID
    extraction_result_id: UUID
    staging_candidate_id: UUID
    locator_fingerprint: str
    profile_id: str
    profile_version: str
    rule_id: str
    actor_ref: str
    evidence_ref: str
    policy_version: str
    published_at: datetime
    parent_record_id: Optional[UUID] = None
    superseded_record_id: Optional[UUID] = None
    is_synthetic: bool = True
    p02_current_truth_readable: bool = False
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        for value, code in (
            (self.id, "internal_publication_id_required"),
            (self.request_id, "approval_request_id_required"),
            (self.decision_id, "approval_decision_id_required"),
            (self.candidate_id, "mapped_candidate_id_required"),
            (self.source_file_id, "source_file_id_required"),
            (self.ingestion_job_id, "ingestion_job_id_required"),
            (self.extraction_result_id, "extraction_result_id_required"),
            (self.staging_candidate_id, "staging_candidate_id_required"),
        ):
            _require_uuid(value, code)
        _require_scope(self.scope, "scope_required")
        for value, code in (
            (self.subject_ref, "approval_subject_ref_required"),
            (self.target_field, "target_field_required"),
            (self.profile_id, "profile_id_required"),
            (self.profile_version, "profile_version_required"),
            (self.rule_id, "mapping_rule_required"),
            (self.actor_ref, "approval_decision_actor_required"),
            (self.evidence_ref, "approval_decision_evidence_required"),
            (self.policy_version, "approval_policy_version_required"),
        ):
            _require_safe_identifier(value, code)
        _require_safe_hash(self.locator_fingerprint, "locator_lineage_required")
        if not isinstance(self.version_no, int) or isinstance(self.version_no, bool) or self.version_no < 1:
            raise ApprovalBoundaryError("internal_publication_version_required")
        if not isinstance(self.state, InternalPublicationState):
            raise ApprovalBoundaryError("internal_publication_state_required")
        _require_safe_hash(self.payload_hash, "publication_payload_hash_required")
        _require_safe_hash(self.source_content_hash, "publication_source_hash_required")
        _require_safe_time(self.published_at, "publication_time_required")
        if self.parent_record_id is not None:
            _require_uuid(self.parent_record_id, "parent_publication_id_required")
            if self.parent_record_id == self.id:
                raise ApprovalBoundaryError("self_parent_forbidden")
        if self.superseded_record_id is not None:
            _require_uuid(
                self.superseded_record_id,
                "superseded_publication_id_required",
            )
        _require_internal_markers(
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )
        if self.p02_current_truth_readable is not False:
            raise ApprovalBoundaryError("p02_current_truth_forbidden")

    @property
    def series_key(self) -> tuple[ScopeRef, str, str]:
        return (self.scope, self.subject_ref, self.target_field)

    @property
    def fingerprint(self) -> str:
        return _digest(
            self.id,
            self.scope.tenant_id,
            self.scope.project_id,
            self.scope.business_line_id,
            self.request_id,
            self.decision_id,
            self.candidate_id,
            self.subject_ref,
            self.target_field,
            self.version_no,
            self.state.value,
            self.payload_hash,
            self.parent_record_id,
            self.superseded_record_id,
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "publication_id": str(self.id),
            "state": self.state.value,
            "version_no": self.version_no,
            "subject_ref": self.subject_ref,
            "target_field": self.target_field,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "p02_current_truth_readable": False,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


@dataclass(frozen=True)
class InternalInvalidationEvent:
    id: UUID
    scope: ScopeRef
    publication_id: UUID
    event_type: str
    destination: str
    subject_ref: str
    target_field: str
    version_no: int
    correlation_id: str
    occurred_at: datetime
    superseded_publication_id: Optional[UUID] = None
    is_synthetic: bool = True
    p02_current_truth_readable: bool = False
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "invalidation_event_id_required")
        _require_scope(self.scope, "scope_required")
        _require_uuid(self.publication_id, "internal_publication_id_required")
        if self.event_type != "TruthFactsChanged":
            raise ApprovalBoundaryError("invalidation_event_type_required")
        if self.destination != "internal_invalidation_outbox":
            raise ApprovalBoundaryError("internal_invalidation_destination_required")
        for value, code in (
            (self.subject_ref, "approval_subject_ref_required"),
            (self.target_field, "target_field_required"),
            (self.correlation_id, "correlation_id_required"),
        ):
            _require_safe_identifier(value, code)
        if not isinstance(self.version_no, int) or isinstance(self.version_no, bool) or self.version_no < 1:
            raise ApprovalBoundaryError("internal_publication_version_required")
        _require_safe_time(self.occurred_at, "invalidation_event_time_required")
        if self.superseded_publication_id is not None:
            _require_uuid(
                self.superseded_publication_id,
                "superseded_publication_id_required",
            )
        _require_internal_markers(
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )
        if self.p02_current_truth_readable is not False:
            raise ApprovalBoundaryError("p02_current_truth_forbidden")

    @property
    def fingerprint(self) -> str:
        return _digest(
            self.id,
            self.publication_id,
            self.subject_ref,
            self.target_field,
            self.version_no,
            self.destination,
            self.superseded_publication_id,
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "event_id": str(self.id),
            "event_type": self.event_type,
            "destination": self.destination,
            "publication_id": str(self.publication_id),
            "subject_ref": self.subject_ref,
            "target_field": self.target_field,
            "version_no": self.version_no,
            "p02_current_truth_readable": False,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


@dataclass(frozen=True)
class InternalPublicationResult:
    approved_record: InternalPublicationRecord
    event: InternalInvalidationEvent
    superseded_record: Optional[InternalPublicationRecord] = None

    def __post_init__(self) -> None:
        if not isinstance(self.approved_record, InternalPublicationRecord):
            raise ApprovalBoundaryError("internal_publication_required")
        if self.approved_record.state is not InternalPublicationState.APPROVED_INTERNAL:
            raise ApprovalBoundaryError("internal_approved_publication_required")
        if not isinstance(self.event, InternalInvalidationEvent):
            raise ApprovalBoundaryError("invalidation_event_required")
        if self.superseded_record is not None:
            if not isinstance(self.superseded_record, InternalPublicationRecord):
                raise ApprovalBoundaryError("internal_publication_required")
            if self.superseded_record.state is not InternalPublicationState.SUPERSEDED_INTERNAL:
                raise ApprovalBoundaryError("internal_superseded_publication_required")
        if self.event.publication_id != self.approved_record.id:
            raise ApprovalBoundaryError("invalidation_publication_mismatch")

    def safe_summary(self) -> dict[str, object]:
        return {
            "approved": self.approved_record.safe_summary(),
            "superseded": (
                self.superseded_record.safe_summary()
                if self.superseded_record is not None
                else None
            ),
            "event": self.event.safe_summary(),
            "p02_current_truth_readable": False,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


def _require_internal_markers(
    is_synthetic: object,
    external_execution_allowed: object,
    business_external_ready: object,
) -> None:
    if is_synthetic is not True:
        raise ApprovalBoundaryError("synthetic_input_required")
    if external_execution_allowed is not False:
        raise ApprovalBoundaryError("external_execution_forbidden")
    if business_external_ready is not False:
        raise ApprovalBoundaryError("business_external_ready_forbidden")


class InMemoryApprovalRequestStore:
    """Append-only approval request and decision store for local contract probes."""

    def __init__(self, now: Optional[Callable[[], datetime]] = None) -> None:
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._initial_by_key: dict[str, ApprovalRequest] = {}
        self._current_by_id: dict[UUID, ApprovalRequest] = {}
        self._versions_by_id: dict[UUID, Tuple[ApprovalRequest, ...]] = {}
        self._request_fingerprint_by_key: dict[str, str] = {}
        self._decision_by_key: dict[str, ApprovalRequest] = {}
        self._decision_fingerprint_by_key: dict[str, str] = {}
        self._audit_events: Tuple[ApprovalAuditEvent, ...] = ()

    def create_request(
        self,
        *,
        candidate: MappedCandidate,
        subject_ref: str,
        requested_by: str,
        evidence_ref: str,
        policy_version: str,
        requested_at: datetime,
        expires_at: datetime,
        idempotency_key: str,
        scope: Optional[ScopeRef] = None,
    ) -> ApprovalRequest:
        candidate = _require_quality_passed_candidate(candidate)
        request_scope = candidate.scope if scope is None else _require_scope(scope, "scope_required")
        if request_scope != candidate.scope:
            raise ApprovalBoundaryError("cross_scope_forbidden")
        for value, code in (
            (subject_ref, "approval_subject_ref_required"),
            (requested_by, "approval_request_actor_required"),
            (evidence_ref, "approval_evidence_ref_required"),
            (policy_version, "approval_policy_version_required"),
            (idempotency_key, "approval_idempotency_key_required"),
        ):
            _require_safe_identifier(value, code)
        requested_at = _require_safe_time(requested_at, "approval_requested_at_required")
        expires_at = _require_safe_time(expires_at, "approval_expires_at_required")
        fingerprint = _digest(
            request_scope,
            candidate.fingerprint,
            subject_ref,
            requested_by,
            evidence_ref,
            policy_version,
            requested_at.isoformat(),
            expires_at.isoformat(),
        )
        existing_fingerprint = self._request_fingerprint_by_key.get(idempotency_key)
        if existing_fingerprint is not None:
            if existing_fingerprint != fingerprint:
                raise ApprovalBoundaryError("approval_request_idempotency_conflict")
            return self._initial_by_key[idempotency_key]
        request = ApprovalRequest(
            id=_uuid_for("approval-request", idempotency_key, fingerprint),
            scope=request_scope,
            candidate=candidate,
            subject_ref=subject_ref,
            requested_by=requested_by,
            evidence_ref=evidence_ref,
            policy_version=policy_version,
            requested_at=requested_at,
            expires_at=expires_at,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
        )
        self._request_fingerprint_by_key[idempotency_key] = fingerprint
        self._initial_by_key[idempotency_key] = request
        self._append_request_version(request)
        self._append_audit(
            request=request,
            actor_ref=requested_by,
            action="create_request",
            state=request.state,
            evidence_ref=evidence_ref,
            recorded_at=requested_at,
        )
        return request

    def record_decision(
        self,
        *,
        request_id: UUID,
        decision: ApprovalDecisionKind,
        actor_ref: str,
        evidence_ref: str,
        policy_version: str,
        decided_at: datetime,
        idempotency_key: str,
    ) -> ApprovalRequest:
        _require_uuid(request_id, "approval_request_id_required")
        if not isinstance(decision, ApprovalDecisionKind):
            raise ApprovalBoundaryError("approval_decision_required")
        for value, code in (
            (actor_ref, "approval_decision_actor_required"),
            (evidence_ref, "approval_decision_evidence_required"),
            (policy_version, "approval_policy_version_required"),
            (idempotency_key, "approval_idempotency_key_required"),
        ):
            _require_safe_identifier(value, code)
        decided_at = _require_safe_time(decided_at, "approval_decided_at_required")
        current = self._current_by_id.get(request_id)
        if current is None:
            raise ApprovalBoundaryError("approval_request_not_found")
        fingerprint = _digest(
            request_id,
            decision.value,
            actor_ref,
            evidence_ref,
            policy_version,
            decided_at.isoformat(),
        )
        existing_fingerprint = self._decision_fingerprint_by_key.get(idempotency_key)
        if existing_fingerprint is not None:
            if existing_fingerprint != fingerprint:
                raise ApprovalBoundaryError("approval_decision_idempotency_conflict")
            return self._decision_by_key[idempotency_key]
        if current.state is not ApprovalRequestState.PENDING:
            raise ApprovalBoundaryError("approval_decision_already_recorded")
        if policy_version != current.policy_version:
            raise ApprovalBoundaryError("approval_policy_mismatch")
        if decision is not ApprovalDecisionKind.EXPIRE and decided_at > current.expires_at:
            raise ApprovalBoundaryError("approval_request_expired")
        if decision is ApprovalDecisionKind.APPROVE and actor_ref == current.requested_by:
            raise ApprovalBoundaryError("self_approval_forbidden")
        decided = ApprovalRequest(
            id=current.id,
            scope=current.scope,
            candidate=current.candidate,
            subject_ref=current.subject_ref,
            requested_by=current.requested_by,
            evidence_ref=current.evidence_ref,
            policy_version=current.policy_version,
            requested_at=current.requested_at,
            expires_at=current.expires_at,
            idempotency_key=current.idempotency_key,
            request_fingerprint=current.request_fingerprint,
            state=_DECISION_TO_STATE[decision],
            version_no=current.version_no + 1,
            decision_id=_uuid_for("approval-decision", idempotency_key, fingerprint),
            decision_kind=decision,
            decision_actor_ref=actor_ref,
            decision_evidence_ref=evidence_ref,
            decided_at=decided_at,
        )
        self._decision_fingerprint_by_key[idempotency_key] = fingerprint
        self._decision_by_key[idempotency_key] = decided
        self._append_request_version(decided)
        self._append_audit(
            request=decided,
            actor_ref=actor_ref,
            action=f"decision_{decision.value}",
            state=decided.state,
            evidence_ref=evidence_ref,
            recorded_at=decided_at,
        )
        return decided

    def request_version_count(self, request_id: UUID) -> int:
        _require_uuid(request_id, "approval_request_id_required")
        return len(self._versions_by_id.get(request_id, ()))

    @property
    def audit_event_count(self) -> int:
        return len(self._audit_events)

    def safe_audit_summary(self) -> tuple[dict[str, object], ...]:
        return tuple(event.safe_summary() for event in self._audit_events)

    def _append_request_version(self, request: ApprovalRequest) -> None:
        versions = self._versions_by_id.get(request.id, ())
        if versions and request.version_no != versions[-1].version_no + 1:
            raise ApprovalBoundaryError("approval_request_version_sequence_invalid")
        self._versions_by_id[request.id] = (*versions, request)
        self._current_by_id[request.id] = request

    def _append_audit(
        self,
        *,
        request: ApprovalRequest,
        actor_ref: str,
        action: str,
        state: ApprovalRequestState,
        evidence_ref: str,
        recorded_at: datetime,
    ) -> None:
        sequence = len(self._audit_events) + 1
        event = ApprovalAuditEvent(
            id=_uuid_for("approval-audit", request.id, sequence, action, state.value),
            scope=request.scope,
            request_id=request.id,
            sequence=sequence,
            actor_ref=actor_ref,
            action=action,
            state=state,
            policy_version=request.policy_version,
            evidence_ref=evidence_ref,
            recorded_at=recorded_at,
        )
        self._audit_events = (*self._audit_events, event)


class SyntheticInternalPublicationLedger:
    """Append-only ledger for P03 internal publication proofs."""

    def __init__(self) -> None:
        self._records_by_id: dict[UUID, InternalPublicationRecord] = {}
        self._series_versions: set[tuple[ScopeRef, str, str, int]] = set()
        self._child_by_parent: dict[UUID, UUID] = {}

    @property
    def appended_record_count(self) -> int:
        return len(self._records_by_id)

    def is_head(self, record: InternalPublicationRecord) -> bool:
        if not isinstance(record, InternalPublicationRecord):
            raise ApprovalBoundaryError("internal_publication_required")
        stored = self._records_by_id.get(record.id)
        if stored != record:
            raise ApprovalBoundaryError("internal_publication_not_found")
        return record.id not in self._child_by_parent

    def next_version_no(self, scope: ScopeRef, subject_ref: str, target_field: str) -> int:
        _require_scope(scope, "scope_required")
        _require_safe_identifier(subject_ref, "approval_subject_ref_required")
        _require_safe_identifier(target_field, "target_field_required")
        versions = [
            version_no
            for item_scope, item_subject, item_target, version_no in self._series_versions
            if item_scope == scope and item_subject == subject_ref and item_target == target_field
        ]
        return (max(versions) + 1) if versions else 1

    def append_batch(self, records: Tuple[InternalPublicationRecord, ...]) -> None:
        if not isinstance(records, tuple) or not records:
            raise ApprovalBoundaryError("internal_publication_batch_required")
        if any(not isinstance(record, InternalPublicationRecord) for record in records):
            raise ApprovalBoundaryError("internal_publication_required")
        staged_records = dict(self._records_by_id)
        staged_series = set(self._series_versions)
        staged_children = dict(self._child_by_parent)
        for record in records:
            if record.id in staged_records:
                raise ApprovalBoundaryError("internal_publication_immutable")
            series_key = (*record.series_key, record.version_no)
            if series_key in staged_series:
                raise ApprovalBoundaryError("internal_publication_version_conflict")
            if record.parent_record_id is None:
                if record.version_no != 1:
                    raise ApprovalBoundaryError("initial_publication_version_required")
                if any(key[:3] == record.series_key for key in staged_series):
                    raise ApprovalBoundaryError("publication_supersede_required")
            else:
                parent = staged_records.get(record.parent_record_id)
                if parent is None:
                    raise ApprovalBoundaryError("parent_publication_not_found")
                if record.parent_record_id in staged_children:
                    raise ApprovalBoundaryError("publication_history_branch_forbidden")
                if record.series_key != parent.series_key:
                    raise ApprovalBoundaryError("publication_subject_mismatch")
                if record.version_no != parent.version_no + 1:
                    raise ApprovalBoundaryError("internal_publication_version_sequence_invalid")
                if record.state not in _PUBLICATION_TRANSITIONS[parent.state]:
                    raise ApprovalBoundaryError("internal_publication_transition_forbidden")
            staged_records[record.id] = record
            staged_series.add(series_key)
            if record.parent_record_id is not None:
                staged_children[record.parent_record_id] = record.id
        self._records_by_id = staged_records
        self._series_versions = staged_series
        self._child_by_parent = staged_children


class InMemoryInvalidationOutbox:
    """Internal-only fake outbox; it has no external adapter surface."""

    def __init__(self) -> None:
        self._events_by_id: Dict[UUID, InternalInvalidationEvent] = {}
        self._fingerprints_by_id: Dict[UUID, str] = {}

    @property
    def event_count(self) -> int:
        return len(self._events_by_id)

    def append(self, event: InternalInvalidationEvent) -> InternalInvalidationEvent:
        if not isinstance(event, InternalInvalidationEvent):
            raise ApprovalBoundaryError("invalidation_event_required")
        existing = self._events_by_id.get(event.id)
        if existing is not None:
            if self._fingerprints_by_id[event.id] != event.fingerprint:
                raise ApprovalBoundaryError("invalidation_event_idempotency_conflict")
            return existing
        self._events_by_id[event.id] = event
        self._fingerprints_by_id[event.id] = event.fingerprint
        return event

    def safe_summary(self) -> tuple[dict[str, object], ...]:
        return tuple(event.safe_summary() for event in self._events_by_id.values())


class SyntheticApprovalPublisher:
    """Publish approved requests into an internal synthetic proof ledger."""

    def __init__(
        self,
        *,
        ledger: SyntheticInternalPublicationLedger,
        outbox: InMemoryInvalidationOutbox,
        now: Optional[Callable[[], datetime]] = None,
    ) -> None:
        if not isinstance(ledger, SyntheticInternalPublicationLedger):
            raise ApprovalBoundaryError("internal_publication_ledger_required")
        if not isinstance(outbox, InMemoryInvalidationOutbox):
            raise ApprovalBoundaryError("invalidation_outbox_required")
        self._ledger = ledger
        self._outbox = outbox
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._publication_by_key: Dict[str, InternalPublicationResult] = {}

    def publish(
        self,
        request: ApprovalRequest,
        *,
        supersedes: Optional[InternalPublicationResult] = None,
    ) -> InternalPublicationResult:
        if not isinstance(request, ApprovalRequest):
            raise ApprovalBoundaryError("approval_request_required")
        if request.state is not ApprovalRequestState.APPROVED:
            raise ApprovalBoundaryError("approval_request_not_publishable")
        if request.decision_id is None or request.decision_actor_ref is None:
            raise ApprovalBoundaryError("approval_decision_required")
        candidate = _require_quality_passed_candidate(request.candidate)
        if candidate.scope != request.scope:
            raise ApprovalBoundaryError("cross_scope_forbidden")
        superseded_source: Optional[InternalPublicationRecord] = None
        if supersedes is not None:
            if not isinstance(supersedes, InternalPublicationResult):
                raise ApprovalBoundaryError("superseded_publication_required")
            superseded_source = supersedes.approved_record
            if (
                superseded_source.scope != request.scope
                or superseded_source.subject_ref != request.subject_ref
                or superseded_source.target_field != candidate.target_field
            ):
                raise ApprovalBoundaryError("publication_subject_mismatch")
            if not self._ledger.is_head(superseded_source):
                raise ApprovalBoundaryError("superseded_publication_not_current")
        publish_key = _digest(
            "publish",
            request.id,
            request.decision_id,
            superseded_source.id if superseded_source is not None else "root",
        )
        existing = self._publication_by_key.get(publish_key)
        if existing is not None:
            return existing

        published_at = _require_safe_time(self._now(), "publication_time_required")
        records: tuple[InternalPublicationRecord, ...]
        superseded_record = None
        if superseded_source is None:
            if self._ledger.next_version_no(request.scope, request.subject_ref, candidate.target_field) != 1:
                raise ApprovalBoundaryError("publication_supersede_required")
            approved_record = self._record_for(
                request=request,
                state=InternalPublicationState.APPROVED_INTERNAL,
                version_no=1,
                parent_record_id=None,
                superseded_record_id=None,
                published_at=published_at,
            )
            records = (approved_record,)
        else:
            superseded_record = self._record_for(
                request=request,
                state=InternalPublicationState.SUPERSEDED_INTERNAL,
                version_no=superseded_source.version_no + 1,
                parent_record_id=superseded_source.id,
                superseded_record_id=superseded_source.id,
                published_at=published_at,
                source_record=superseded_source,
            )
            approved_record = self._record_for(
                request=request,
                state=InternalPublicationState.APPROVED_INTERNAL,
                version_no=superseded_record.version_no + 1,
                parent_record_id=superseded_record.id,
                superseded_record_id=superseded_source.id,
                published_at=published_at,
            )
            records = (superseded_record, approved_record)

        event = InternalInvalidationEvent(
            id=_uuid_for(
                "internal-invalidation",
                approved_record.id,
                superseded_source.id if superseded_source is not None else "root",
            ),
            scope=request.scope,
            publication_id=approved_record.id,
            event_type="TruthFactsChanged",
            destination="internal_invalidation_outbox",
            subject_ref=request.subject_ref,
            target_field=candidate.target_field,
            version_no=approved_record.version_no,
            correlation_id=request.scope.correlation_id,
            occurred_at=published_at,
            superseded_publication_id=(
                superseded_source.id if superseded_source is not None else None
            ),
        )
        result = InternalPublicationResult(
            approved_record=approved_record,
            superseded_record=superseded_record,
            event=event,
        )
        self._ledger.append_batch(records)
        self._outbox.append(event)
        self._publication_by_key[publish_key] = result
        return result

    @staticmethod
    def _record_for(
        *,
        request: ApprovalRequest,
        state: InternalPublicationState,
        version_no: int,
        parent_record_id: Optional[UUID],
        superseded_record_id: Optional[UUID],
        published_at: datetime,
        source_record: Optional[InternalPublicationRecord] = None,
    ) -> InternalPublicationRecord:
        candidate = request.candidate
        payload_hash = (
            source_record.payload_hash
            if source_record is not None
            else candidate.normalized_value_hash
        )
        source_hash = (
            source_record.source_content_hash
            if source_record is not None
            else candidate.source_content_hash
        )
        candidate_id = source_record.candidate_id if source_record is not None else candidate.id
        return InternalPublicationRecord(
            id=_uuid_for(
                "internal-publication",
                request.id,
                request.decision_id,
                state.value,
                version_no,
                parent_record_id,
                superseded_record_id,
            ),
            scope=request.scope,
            request_id=request.id,
            decision_id=request.decision_id,
            candidate_id=candidate_id,
            subject_ref=request.subject_ref,
            target_field=candidate.target_field,
            version_no=version_no,
            state=state,
            payload_hash=payload_hash,
            source_content_hash=source_hash,
            source_file_id=(
                source_record.source_file_id
                if source_record is not None
                else candidate.source_file_id
            ),
            ingestion_job_id=(
                source_record.ingestion_job_id
                if source_record is not None
                else candidate.ingestion_job_id
            ),
            extraction_result_id=(
                source_record.extraction_result_id
                if source_record is not None
                else candidate.extraction_result_id
            ),
            staging_candidate_id=(
                source_record.staging_candidate_id
                if source_record is not None
                else candidate.staging_candidate_id
            ),
            locator_fingerprint=(
                source_record.locator_fingerprint
                if source_record is not None
                else _digest(
                    "locator",
                    candidate.locator.page,
                    candidate.locator.sheet,
                    candidate.locator.row,
                    candidate.locator.cell,
                    candidate.locator.bbox,
                    candidate.locator.export_record,
                    candidate.locator.member_relative_path,
                )
            ),
            profile_id=(
                source_record.profile_id if source_record is not None else candidate.profile_id
            ),
            profile_version=(
                source_record.profile_version
                if source_record is not None
                else candidate.profile_version
            ),
            rule_id=source_record.rule_id if source_record is not None else candidate.rule_id,
            actor_ref=request.decision_actor_ref,
            evidence_ref=request.decision_evidence_ref,
            policy_version=request.policy_version,
            published_at=published_at,
            parent_record_id=parent_record_id,
            superseded_record_id=superseded_record_id,
        )


__all__ = [
    "ApprovalBoundaryError",
    "ApprovalDecisionKind",
    "ApprovalRequest",
    "ApprovalRequestState",
    "InMemoryApprovalRequestStore",
    "InMemoryInvalidationOutbox",
    "InternalInvalidationEvent",
    "InternalPublicationRecord",
    "InternalPublicationResult",
    "InternalPublicationState",
    "SyntheticApprovalPublisher",
    "SyntheticInternalPublicationLedger",
]
