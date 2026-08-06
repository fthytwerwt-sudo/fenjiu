"""P03-03 synthetic approval and internal publication proof contracts.

This module intentionally stays inside the ingestion boundary.  It validates a
local, synthetic P03-01/P03-02 evidence chain and emits only immutable internal
publication proofs plus internal invalidation events.  It does not import or
write the P02 truth center, and these records are not P02 current truth.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Callable, Dict, Optional, Tuple
from uuid import UUID, NAMESPACE_URL, uuid5

from core.contracts import DataState, ScopeRef
from modules.ingestion.contracts import (
    ExtractionResultRecord,
    IngestionBoundaryError,
    IngestionJobRecord,
    IngestionWorkflowState,
    SourceDisposition,
    SourceFileRecord,
    StagingCandidateRecord,
    _reject_sensitive_text,
    _require_aware_time,
    _require_hash,
    _require_identifier,
)
from modules.ingestion.mapping import (
    MappedCandidate,
    MappingBatch,
    MappingEvidence,
    MappingEvidenceLineage,
    MappingProfile,
    MappingReport,
    MappingRunState,
    SyntheticMappingEngine,
)
from modules.ingestion.store import InMemoryIngestionStore


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
    REVOKED_INTERNAL = "revoked_internal"


class ReviewerRole(str, Enum):
    DATA_REVIEWER = "data_reviewer"


_DECISION_TO_STATE = {
    ApprovalDecisionKind.APPROVE: ApprovalRequestState.APPROVED,
    ApprovalDecisionKind.REJECT: ApprovalRequestState.REJECTED,
    ApprovalDecisionKind.EXPIRE: ApprovalRequestState.EXPIRED,
    ApprovalDecisionKind.REVISE: ApprovalRequestState.REVISION_REQUESTED,
    ApprovalDecisionKind.MARK_CONFLICT: ApprovalRequestState.CONFLICT,
}
_PUBLICATION_TRANSITIONS = {
    InternalPublicationState.APPROVED_INTERNAL: frozenset(
        {
            InternalPublicationState.SUPERSEDED_INTERNAL,
            InternalPublicationState.REVOKED_INTERNAL,
        }
    ),
    InternalPublicationState.SUPERSEDED_INTERNAL: frozenset(
        {InternalPublicationState.APPROVED_INTERNAL}
    ),
    InternalPublicationState.REVOKED_INTERNAL: frozenset(
        {InternalPublicationState.APPROVED_INTERNAL}
    ),
}


def _digest(*parts: object) -> str:
    material = "\x1f".join(str(part) for part in parts)
    return sha256(material.encode("utf-8")).hexdigest()


def _uuid_for(*parts: object) -> UUID:
    return uuid5(NAMESPACE_URL, _digest(*parts))


def _snapshot(value):
    return deepcopy(value)


def _scope_fingerprint_parts(scope: ScopeRef) -> tuple[object, ...]:
    _require_scope(scope, "scope_required")
    return (
        scope.tenant_id,
        scope.project_id,
        scope.business_line_id,
        scope.correlation_id,
    )


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


def _locator_fingerprint(candidate: MappedCandidate) -> str:
    return _digest(
        "locator",
        candidate.locator.page,
        candidate.locator.sheet,
        candidate.locator.row,
        candidate.locator.cell,
        candidate.locator.bbox,
        candidate.locator.export_record,
        candidate.locator.member_relative_path,
    )


def _approval_request_fingerprint(
    *,
    scope: ScopeRef,
    candidate_fingerprint: str,
    subject_ref: str,
    requested_by: str,
    evidence_ref: str,
    policy_version: str,
    requested_at: datetime,
    expires_at: datetime,
) -> str:
    return _digest(
        *_scope_fingerprint_parts(scope),
        candidate_fingerprint,
        subject_ref,
        requested_by,
        evidence_ref,
        policy_version,
        requested_at.isoformat(),
        expires_at.isoformat(),
    )


def _require_mapped_candidate(candidate: object) -> MappedCandidate:
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
    for value in (
        candidate.target_field,
        candidate.profile_id,
        candidate.profile_version,
        candidate.rule_id,
    ):
        _require_safe_identifier(value, "candidate_lineage_invalid")
    if not candidate.locator.has_traceable_location:
        raise ApprovalBoundaryError("candidate_lineage_invalid")
    return candidate


@dataclass(frozen=True)
class CanonicalMappedCandidate:
    """Candidate approved for request creation by a canonical local evidence gate."""

    id: UUID
    scope: ScopeRef
    candidate: MappedCandidate
    report_run_fingerprint: str
    report_input_fingerprint: str
    profile_fingerprint: str
    candidate_fingerprint: str
    locator_fingerprint: str
    quality_checked_at: datetime
    state: MappingRunState = MappingRunState.MAPPED
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "canonical_candidate_id_required")
        _require_scope(self.scope, "scope_required")
        candidate = _require_mapped_candidate(self.candidate)
        if candidate.scope != self.scope:
            raise ApprovalBoundaryError("cross_scope_forbidden")
        if self.state is not MappingRunState.MAPPED:
            raise ApprovalBoundaryError("canonical_candidate_required")
        for value in (
            self.report_run_fingerprint,
            self.report_input_fingerprint,
            self.profile_fingerprint,
            self.candidate_fingerprint,
            self.locator_fingerprint,
        ):
            _require_safe_hash(value, "canonical_candidate_fingerprint_required")
        if self.candidate_fingerprint != candidate.fingerprint:
            raise ApprovalBoundaryError("canonical_candidate_fingerprint_mismatch")
        if self.locator_fingerprint != _locator_fingerprint(candidate):
            raise ApprovalBoundaryError("locator_lineage_required")
        _require_safe_time(self.quality_checked_at, "quality_checked_at_required")
        _require_internal_markers(
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )

    @property
    def source_file_id(self) -> UUID:
        return self.candidate.source_file_id

    @property
    def ingestion_job_id(self) -> UUID:
        return self.candidate.ingestion_job_id

    @property
    def extraction_result_id(self) -> UUID:
        return self.candidate.extraction_result_id

    @property
    def staging_candidate_id(self) -> UUID:
        return self.candidate.staging_candidate_id

    @property
    def target_field(self) -> str:
        return self.candidate.target_field

    @property
    def profile_id(self) -> str:
        return self.candidate.profile_id

    @property
    def profile_version(self) -> str:
        return self.candidate.profile_version

    @property
    def rule_id(self) -> str:
        return self.candidate.rule_id

    @property
    def normalized_value_hash(self) -> str:
        return self.candidate.normalized_value_hash

    @property
    def source_content_hash(self) -> str:
        return self.candidate.source_content_hash

    @property
    def fingerprint(self) -> str:
        return _digest(
            self.id,
            self.scope,
            self.candidate_fingerprint,
            self.report_run_fingerprint,
            self.profile_fingerprint,
            self.locator_fingerprint,
        )


class CanonicalMappingCandidateGate:
    """Local authoritative P03-01/P03-02 gate for approval requests."""

    def __init__(
        self,
        *,
        ingestion_store: InMemoryIngestionStore,
        mapping_engine: Optional[SyntheticMappingEngine] = None,
    ) -> None:
        if not isinstance(ingestion_store, InMemoryIngestionStore):
            raise ApprovalBoundaryError("ingestion_store_required")
        if mapping_engine is not None and not isinstance(mapping_engine, SyntheticMappingEngine):
            raise ApprovalBoundaryError("mapping_engine_required")
        self._ingestion_store = ingestion_store
        self._mapping_engine = mapping_engine
        self._profile_fingerprint_by_key: Dict[
            Tuple[UUID, UUID, UUID, str, str, str],
            str,
        ] = {}
        self._canonical_by_id: Dict[UUID, CanonicalMappedCandidate] = {}
        self._fingerprint_by_id: Dict[UUID, str] = {}

    def register_profile(self, profile: MappingProfile) -> MappingProfile:
        if not isinstance(profile, MappingProfile):
            raise ApprovalBoundaryError("mapping_profile_required")
        profile = _snapshot(profile)
        profile.__post_init__()
        key = self._profile_key(profile)
        existing = self._profile_fingerprint_by_key.get(key)
        if existing is not None and existing != profile.fingerprint:
            raise ApprovalBoundaryError("mapping_profile_fingerprint_mismatch")
        self._profile_fingerprint_by_key[key] = profile.fingerprint
        return _snapshot(profile)

    def register_report(
        self,
        profile: MappingProfile,
        report: MappingReport,
        *,
        quality_checked_at: datetime,
    ) -> Tuple[CanonicalMappedCandidate, ...]:
        if not isinstance(profile, MappingProfile):
            raise ApprovalBoundaryError("mapping_profile_required")
        if not isinstance(report, MappingReport):
            raise ApprovalBoundaryError("mapping_report_required")
        profile = _snapshot(profile)
        report = _snapshot(report)
        profile.__post_init__()
        report.__post_init__()
        self._assert_registered_profile(profile)
        checked_at = _require_safe_time(quality_checked_at, "quality_checked_at_required")
        if report.state is not MappingRunState.MAPPED or report.findings:
            raise ApprovalBoundaryError("canonical_mapping_report_required")
        if (
            report.profile_id != profile.profile_id
            or report.profile_version != profile.version
            or report.profile_fingerprint != profile.fingerprint
            or report.scope != profile.scope
        ):
            raise ApprovalBoundaryError("mapping_report_profile_mismatch")
        candidate_by_staging = {
            candidate.staging_candidate_id: candidate for candidate in report.candidates
        }
        if len(candidate_by_staging) != len(report.candidates):
            raise ApprovalBoundaryError("mapping_report_lineage_mismatch")
        evidence: list[MappingEvidence] = []
        for lineage in report.input_evidence_ids:
            if not isinstance(lineage, MappingEvidenceLineage):
                raise ApprovalBoundaryError("mapping_report_lineage_mismatch")
            candidate = candidate_by_staging.get(lineage.staging_candidate_id)
            if candidate is None:
                raise ApprovalBoundaryError("mapping_report_lineage_mismatch")
            evidence.append(self._evidence_for(lineage, candidate, report.scope))
        replay_engine = SyntheticMappingEngine(now=lambda: checked_at)
        replay = replay_engine.map(
            profile,
            MappingBatch(
                scope=report.scope,
                source_signature=profile.source_signature,
                evidence=tuple(evidence),
            ),
        )
        if replay != report:
            raise ApprovalBoundaryError("mapping_report_replay_mismatch")

        canonical: list[CanonicalMappedCandidate] = []
        for candidate in report.candidates:
            record = CanonicalMappedCandidate(
                id=candidate.id,
                scope=candidate.scope,
                candidate=candidate,
                report_run_fingerprint=report.run_fingerprint,
                report_input_fingerprint=report.input_fingerprint,
                profile_fingerprint=profile.fingerprint,
                candidate_fingerprint=candidate.fingerprint,
                locator_fingerprint=_locator_fingerprint(candidate),
                quality_checked_at=checked_at,
            )
            existing_fingerprint = self._fingerprint_by_id.get(record.id)
            if existing_fingerprint is not None:
                if existing_fingerprint != record.fingerprint:
                    raise ApprovalBoundaryError("canonical_candidate_conflict")
                canonical.append(_snapshot(self._canonical_by_id[record.id]))
                continue
            stored = _snapshot(record)
            stored.__post_init__()
            self._canonical_by_id[record.id] = stored
            self._fingerprint_by_id[record.id] = record.fingerprint
            canonical.append(_snapshot(stored))
        return tuple(canonical)

    def assert_canonical(self, candidate: object) -> CanonicalMappedCandidate:
        if not isinstance(candidate, CanonicalMappedCandidate):
            raise ApprovalBoundaryError("canonical_candidate_required")
        try:
            candidate.__post_init__()
        except ApprovalBoundaryError as exc:
            raise ApprovalBoundaryError("canonical_candidate_required") from exc
        stored = self._canonical_by_id.get(candidate.id)
        if stored is None:
            raise ApprovalBoundaryError("canonical_candidate_required")
        try:
            stored.__post_init__()
        except ApprovalBoundaryError as exc:
            raise ApprovalBoundaryError("canonical_candidate_required") from exc
        if stored != candidate:
            raise ApprovalBoundaryError("canonical_candidate_required")
        if self._fingerprint_by_id.get(candidate.id) != candidate.fingerprint:
            raise ApprovalBoundaryError("canonical_candidate_required")
        if self._fingerprint_by_id.get(stored.id) != stored.fingerprint:
            raise ApprovalBoundaryError("canonical_candidate_required")
        return _snapshot(stored)

    def _evidence_for(
        self,
        lineage: MappingEvidenceLineage,
        candidate: MappedCandidate,
        scope: ScopeRef,
    ) -> MappingEvidence:
        source = self._source(scope, lineage.source_file_id)
        job = self._job(scope, lineage.ingestion_job_id)
        result = self._result(scope, lineage.extraction_result_id)
        staging = self._staging_candidate(scope, lineage.staging_candidate_id)
        if (
            source.disposition is not SourceDisposition.REGISTERED
            or job.workflow_state is not IngestionWorkflowState.STAGED
            or staging.workflow_state is not IngestionWorkflowState.STAGED
        ):
            raise ApprovalBoundaryError("canonical_ingestion_state_required")
        if (
            source.id != candidate.source_file_id
            or job.id != candidate.ingestion_job_id
            or result.id != candidate.extraction_result_id
            or staging.id != candidate.staging_candidate_id
            or result.content_hash != candidate.source_content_hash
            or staging.content_hash != candidate.source_content_hash
            or result.locator != candidate.locator
            or staging.locator != candidate.locator
        ):
            raise ApprovalBoundaryError("mapping_report_lineage_mismatch")
        return MappingEvidence(
            source_file=_snapshot(source),
            ingestion_job=_snapshot(job),
            extraction_result=_snapshot(result),
            staging_candidate=_snapshot(staging),
            descriptor=candidate.descriptor,
            observed_at=candidate.observed_at,
        )

    def _source(self, scope: ScopeRef, source_file_id: UUID) -> SourceFileRecord:
        try:
            return self._ingestion_store.get_source(scope, source_file_id)
        except IngestionBoundaryError as exc:
            raise ApprovalBoundaryError("canonical_ingestion_record_required") from exc

    def _job(self, scope: ScopeRef, job_id: UUID) -> IngestionJobRecord:
        for record in self._ingestion_store.ingestion_jobs:
            if record.id == job_id:
                if record.scope != scope:
                    raise ApprovalBoundaryError("cross_scope_forbidden")
                return record
        raise ApprovalBoundaryError("canonical_ingestion_record_required")

    @staticmethod
    def _profile_key(profile: MappingProfile) -> Tuple[UUID, UUID, UUID, str, str, str]:
        return (
            profile.scope.tenant_id,
            profile.scope.project_id,
            profile.scope.business_line_id,
            profile.scope.correlation_id,
            profile.profile_id,
            profile.version,
        )

    def _assert_registered_profile(self, profile: MappingProfile) -> None:
        key = self._profile_key(profile)
        existing = self._profile_fingerprint_by_key.get(key)
        if existing is None:
            raise ApprovalBoundaryError("canonical_mapping_profile_required")
        if existing != profile.fingerprint:
            raise ApprovalBoundaryError("mapping_profile_fingerprint_mismatch")

    def _result(self, scope: ScopeRef, result_id: UUID) -> ExtractionResultRecord:
        for record in self._ingestion_store.extraction_results:
            if record.id == result_id:
                if record.scope != scope:
                    raise ApprovalBoundaryError("cross_scope_forbidden")
                return record
        raise ApprovalBoundaryError("canonical_ingestion_record_required")

    def _staging_candidate(
        self,
        scope: ScopeRef,
        candidate_id: UUID,
    ) -> StagingCandidateRecord:
        for record in self._ingestion_store.staging_candidates:
            if record.id == candidate_id:
                if record.scope != scope:
                    raise ApprovalBoundaryError("cross_scope_forbidden")
                return record
        raise ApprovalBoundaryError("canonical_ingestion_record_required")


@dataclass(frozen=True)
class ReviewerCapabilityGrant:
    id: UUID
    scope: ScopeRef
    actor_ref: str
    role: ReviewerRole
    policy_version: str
    evidence_ref: str
    issued_at: datetime
    expires_at: datetime
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "reviewer_capability_id_required")
        _require_scope(self.scope, "scope_required")
        _require_safe_identifier(self.actor_ref, "reviewer_actor_ref_required")
        if not isinstance(self.role, ReviewerRole):
            raise ApprovalBoundaryError("reviewer_role_required")
        _require_safe_identifier(self.policy_version, "approval_policy_version_required")
        _require_safe_identifier(self.evidence_ref, "reviewer_capability_evidence_required")
        issued_at = _require_safe_time(self.issued_at, "reviewer_capability_issued_at_required")
        expires_at = _require_safe_time(self.expires_at, "reviewer_capability_expires_at_required")
        if expires_at <= issued_at:
            raise ApprovalBoundaryError("reviewer_capability_window_invalid")
        _require_internal_markers(
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )

    @property
    def fingerprint(self) -> str:
        return _digest(
            self.id,
            *_scope_fingerprint_parts(self.scope),
            self.actor_ref,
            self.role.value,
            self.policy_version,
            self.evidence_ref,
            self.issued_at.isoformat(),
            self.expires_at.isoformat(),
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )


class SyntheticReviewerCapabilityRegistry:
    """Synthetic local capability registry; not production auth or RBAC."""

    def __init__(self, now: Optional[Callable[[], datetime]] = None) -> None:
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._grants_by_id: Dict[UUID, ReviewerCapabilityGrant] = {}
        self._fingerprint_by_id: Dict[UUID, str] = {}
        self._fingerprint_by_key: Dict[str, str] = {}
        self._grant_by_key: Dict[str, ReviewerCapabilityGrant] = {}

    def grant_reviewer(
        self,
        *,
        actor_ref: str,
        role: ReviewerRole,
        scope: ScopeRef,
        policy_version: str,
        evidence_ref: str,
        issued_at: datetime,
        expires_at: datetime,
        idempotency_key: str,
    ) -> ReviewerCapabilityGrant:
        _require_safe_identifier(idempotency_key, "reviewer_capability_idempotency_required")
        _require_scope(scope, "scope_required")
        _require_safe_identifier(actor_ref, "reviewer_actor_ref_required")
        if not isinstance(role, ReviewerRole):
            raise ApprovalBoundaryError("reviewer_role_required")
        _require_safe_identifier(policy_version, "approval_policy_version_required")
        _require_safe_identifier(evidence_ref, "reviewer_capability_evidence_required")
        issued_at = _require_safe_time(issued_at, "reviewer_capability_issued_at_required")
        expires_at = _require_safe_time(expires_at, "reviewer_capability_expires_at_required")
        fingerprint = _digest(
            *_scope_fingerprint_parts(scope),
            actor_ref,
            role.value,
            policy_version,
            evidence_ref,
            issued_at.isoformat(),
            expires_at.isoformat(),
        )
        existing_fingerprint = self._fingerprint_by_key.get(idempotency_key)
        if existing_fingerprint is not None:
            if existing_fingerprint != fingerprint:
                raise ApprovalBoundaryError("reviewer_capability_idempotency_conflict")
            return _snapshot(self._grant_by_key[idempotency_key])
        grant = ReviewerCapabilityGrant(
            id=_uuid_for("reviewer-capability", idempotency_key, fingerprint),
            scope=scope,
            actor_ref=actor_ref,
            role=role,
            policy_version=policy_version,
            evidence_ref=evidence_ref,
            issued_at=issued_at,
            expires_at=expires_at,
        )
        stored = _snapshot(grant)
        stored.__post_init__()
        self._fingerprint_by_key[idempotency_key] = fingerprint
        self._grant_by_key[idempotency_key] = stored
        self._grants_by_id[grant.id] = stored
        self._fingerprint_by_id[grant.id] = stored.fingerprint
        return _snapshot(stored)

    def assert_grant(
        self,
        grant_id: UUID,
        *,
        scope: ScopeRef,
        policy_version: str,
        role: ReviewerRole,
        at: datetime,
    ) -> ReviewerCapabilityGrant:
        _require_uuid(grant_id, "reviewer_capability_id_required")
        at = _require_safe_time(at, "reviewer_capability_check_time_required")
        grant = self._grants_by_id.get(grant_id)
        if grant is None:
            raise ApprovalBoundaryError("reviewer_capability_not_found")
        grant.__post_init__()
        if self._fingerprint_by_id.get(grant.id) != grant.fingerprint:
            raise ApprovalBoundaryError("reviewer_capability_drift")
        if grant.scope != scope:
            raise ApprovalBoundaryError("cross_scope_forbidden")
        if grant.policy_version != policy_version:
            raise ApprovalBoundaryError("approval_policy_mismatch")
        if grant.role is not role:
            raise ApprovalBoundaryError("reviewer_role_forbidden")
        if at < grant.issued_at or at > grant.expires_at:
            raise ApprovalBoundaryError("reviewer_capability_expired")
        return _snapshot(grant)


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
    decision_id: Optional[UUID] = None
    reviewer_grant_id: Optional[UUID] = None
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
        if self.decision_id is not None:
            _require_uuid(self.decision_id, "approval_decision_id_required")
        if self.reviewer_grant_id is not None:
            _require_uuid(self.reviewer_grant_id, "reviewer_capability_id_required")
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

    @property
    def fingerprint(self) -> str:
        return _digest(
            self.id,
            *_scope_fingerprint_parts(self.scope),
            self.request_id,
            self.sequence,
            self.actor_ref,
            self.action,
            self.state.value,
            self.policy_version,
            self.evidence_ref,
            self.recorded_at.isoformat(),
            self.decision_id,
            self.reviewer_grant_id,
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )


@dataclass(frozen=True)
class ApprovalRequest:
    id: UUID
    scope: ScopeRef
    candidate: CanonicalMappedCandidate
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
    reviewer_grant_id: Optional[UUID] = None
    decided_at: Optional[datetime] = None
    is_synthetic: bool = True
    p02_current_truth_readable: bool = False
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "approval_request_id_required")
        _require_scope(self.scope, "scope_required")
        if not isinstance(self.candidate, CanonicalMappedCandidate):
            raise ApprovalBoundaryError("canonical_candidate_required")
        self.candidate.__post_init__()
        if self.candidate.scope != self.scope:
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
        expected_fingerprint = _approval_request_fingerprint(
            scope=self.scope,
            candidate_fingerprint=self.candidate.fingerprint,
            subject_ref=self.subject_ref,
            requested_by=self.requested_by,
            evidence_ref=self.evidence_ref,
            policy_version=self.policy_version,
            requested_at=requested_at,
            expires_at=expires_at,
        )
        if self.request_fingerprint != expected_fingerprint:
            raise ApprovalBoundaryError("approval_request_fingerprint_mismatch")
        if not isinstance(self.state, ApprovalRequestState):
            raise ApprovalBoundaryError("approval_state_required")
        if not isinstance(self.version_no, int) or isinstance(self.version_no, bool) or self.version_no < 1:
            raise ApprovalBoundaryError("approval_request_version_required")
        decision_fields = (
            self.decision_id,
            self.decision_kind,
            self.decision_actor_ref,
            self.decision_evidence_ref,
            self.reviewer_grant_id,
            self.decided_at,
        )
        if self.state is ApprovalRequestState.PENDING:
            if any(value is not None for value in decision_fields):
                raise ApprovalBoundaryError("approval_pending_decision_forbidden")
        else:
            if any(value is None for value in decision_fields):
                raise ApprovalBoundaryError("approval_decision_required")
            _require_uuid(self.decision_id, "approval_decision_id_required")
            _require_uuid(self.reviewer_grant_id, "reviewer_capability_id_required")
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

    @property
    def fingerprint(self) -> str:
        return _digest(
            self.id,
            *_scope_fingerprint_parts(self.scope),
            self.candidate.fingerprint,
            self.subject_ref,
            self.requested_by,
            self.evidence_ref,
            self.policy_version,
            self.requested_at.isoformat(),
            self.expires_at.isoformat(),
            self.idempotency_key,
            self.request_fingerprint,
            self.state.value,
            self.version_no,
            self.decision_id,
            self.decision_kind.value if self.decision_kind is not None else None,
            self.decision_actor_ref,
            self.decision_evidence_ref,
            self.reviewer_grant_id,
            self.decided_at.isoformat() if self.decided_at is not None else None,
            self.is_synthetic,
            self.p02_current_truth_readable,
            self.external_execution_allowed,
            self.business_external_ready,
        )


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
    revoked_record_id: Optional[UUID] = None
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
        if self.revoked_record_id is not None:
            _require_uuid(self.revoked_record_id, "revoked_publication_id_required")
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
            *_scope_fingerprint_parts(self.scope),
            self.request_id,
            self.decision_id,
            self.candidate_id,
            self.subject_ref,
            self.target_field,
            self.version_no,
            self.state.value,
            self.payload_hash,
            self.source_content_hash,
            self.source_file_id,
            self.ingestion_job_id,
            self.extraction_result_id,
            self.staging_candidate_id,
            self.locator_fingerprint,
            self.profile_id,
            self.profile_version,
            self.rule_id,
            self.actor_ref,
            self.evidence_ref,
            self.policy_version,
            self.published_at.isoformat(),
            self.parent_record_id,
            self.superseded_record_id,
            self.revoked_record_id,
            self.is_synthetic,
            self.p02_current_truth_readable,
            self.external_execution_allowed,
            self.business_external_ready,
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
    revoked_publication_id: Optional[UUID] = None
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
        if self.correlation_id != self.scope.correlation_id:
            raise ApprovalBoundaryError("invalidation_event_scope_mismatch")
        if not isinstance(self.version_no, int) or isinstance(self.version_no, bool) or self.version_no < 1:
            raise ApprovalBoundaryError("internal_publication_version_required")
        _require_safe_time(self.occurred_at, "invalidation_event_time_required")
        if self.superseded_publication_id is not None:
            _require_uuid(
                self.superseded_publication_id,
                "superseded_publication_id_required",
            )
        if self.revoked_publication_id is not None:
            _require_uuid(self.revoked_publication_id, "revoked_publication_id_required")
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
            *_scope_fingerprint_parts(self.scope),
            self.publication_id,
            self.event_type,
            self.destination,
            self.subject_ref,
            self.target_field,
            self.version_no,
            self.correlation_id,
            self.occurred_at.isoformat(),
            self.superseded_publication_id,
            self.revoked_publication_id,
            self.is_synthetic,
            self.p02_current_truth_readable,
            self.external_execution_allowed,
            self.business_external_ready,
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


@dataclass(frozen=True)
class InternalRevocationResult:
    revoked_record: InternalPublicationRecord
    event: InternalInvalidationEvent

    def __post_init__(self) -> None:
        if not isinstance(self.revoked_record, InternalPublicationRecord):
            raise ApprovalBoundaryError("internal_publication_required")
        if self.revoked_record.state is not InternalPublicationState.REVOKED_INTERNAL:
            raise ApprovalBoundaryError("internal_revoked_publication_required")
        if not isinstance(self.event, InternalInvalidationEvent):
            raise ApprovalBoundaryError("invalidation_event_required")
        if self.event.publication_id != self.revoked_record.id:
            raise ApprovalBoundaryError("invalidation_publication_mismatch")

    def safe_summary(self) -> dict[str, object]:
        return {
            "revoked": self.revoked_record.safe_summary(),
            "event": self.event.safe_summary(),
            "p02_current_truth_readable": False,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


class InMemoryApprovalRequestStore:
    """Append-only approval request and decision store for local contract probes."""

    def __init__(
        self,
        *,
        candidate_gate: CanonicalMappingCandidateGate,
        reviewer_registry: SyntheticReviewerCapabilityRegistry,
        now: Optional[Callable[[], datetime]] = None,
    ) -> None:
        if not isinstance(candidate_gate, CanonicalMappingCandidateGate):
            raise ApprovalBoundaryError("canonical_candidate_gate_required")
        if not isinstance(reviewer_registry, SyntheticReviewerCapabilityRegistry):
            raise ApprovalBoundaryError("reviewer_capability_registry_required")
        self._candidate_gate = candidate_gate
        self._reviewer_registry = reviewer_registry
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._initial_by_key: dict[str, ApprovalRequest] = {}
        self._current_by_id: dict[UUID, ApprovalRequest] = {}
        self._current_fingerprint_by_id: dict[UUID, str] = {}
        self._versions_by_id: dict[UUID, Tuple[ApprovalRequest, ...]] = {}
        self._version_fingerprint_by_id: dict[tuple[UUID, int], str] = {}
        self._request_fingerprint_by_key: dict[str, str] = {}
        self._decision_by_key: dict[str, ApprovalRequest] = {}
        self._decision_fingerprint_by_key: dict[str, str] = {}
        self._audit_events: Tuple[ApprovalAuditEvent, ...] = ()
        self._audit_fingerprint_by_id: dict[UUID, str] = {}

    def create_request(
        self,
        *,
        candidate: CanonicalMappedCandidate,
        subject_ref: str,
        requested_by: str,
        evidence_ref: str,
        policy_version: str,
        requested_at: datetime,
        expires_at: datetime,
        idempotency_key: str,
        scope: Optional[ScopeRef] = None,
    ) -> ApprovalRequest:
        candidate = self._candidate_gate.assert_canonical(candidate)
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
        fingerprint = _approval_request_fingerprint(
            scope=request_scope,
            candidate_fingerprint=candidate.fingerprint,
            subject_ref=subject_ref,
            requested_by=requested_by,
            evidence_ref=evidence_ref,
            policy_version=policy_version,
            requested_at=requested_at,
            expires_at=expires_at,
        )
        existing_fingerprint = self._request_fingerprint_by_key.get(idempotency_key)
        if existing_fingerprint is not None:
            if existing_fingerprint != fingerprint:
                raise ApprovalBoundaryError("approval_request_idempotency_conflict")
            return _snapshot(self._initial_by_key[idempotency_key])
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
        stored = self._append_request_version(request)
        self._initial_by_key[idempotency_key] = stored
        self._append_audit(
            request=stored,
            actor_ref=requested_by,
            action="create_request",
            state=stored.state,
            evidence_ref=evidence_ref,
            recorded_at=requested_at,
        )
        return _snapshot(stored)

    def record_decision(
        self,
        *,
        request_id: UUID,
        decision: ApprovalDecisionKind,
        reviewer_grant_id: UUID,
        evidence_ref: str,
        policy_version: str,
        decided_at: datetime,
        idempotency_key: str,
    ) -> ApprovalRequest:
        _require_uuid(request_id, "approval_request_id_required")
        if not isinstance(decision, ApprovalDecisionKind):
            raise ApprovalBoundaryError("approval_decision_required")
        for value, code in (
            (evidence_ref, "approval_decision_evidence_required"),
            (policy_version, "approval_policy_version_required"),
            (idempotency_key, "approval_idempotency_key_required"),
        ):
            _require_safe_identifier(value, code)
        decided_at = _require_safe_time(decided_at, "approval_decided_at_required")
        current = self._current_request(request_id)
        if policy_version != current.policy_version:
            raise ApprovalBoundaryError("approval_policy_mismatch")
        existing_fingerprint = self._decision_fingerprint_by_key.get(idempotency_key)
        if existing_fingerprint is not None:
            grant = self._reviewer_registry.assert_grant(
                reviewer_grant_id,
                scope=current.scope,
                policy_version=policy_version,
                role=ReviewerRole.DATA_REVIEWER,
                at=decided_at,
            )
            fingerprint = _digest(
                request_id,
                decision.value,
                grant.id,
                grant.actor_ref,
                evidence_ref,
                policy_version,
                decided_at.isoformat(),
            )
            if existing_fingerprint != fingerprint:
                raise ApprovalBoundaryError("approval_decision_idempotency_conflict")
            return _snapshot(self._decision_by_key[idempotency_key])
        if current.state is not ApprovalRequestState.PENDING:
            raise ApprovalBoundaryError("approval_decision_already_recorded")
        if decision is not ApprovalDecisionKind.EXPIRE and decided_at > current.expires_at:
            raise ApprovalBoundaryError("approval_request_expired")
        grant = self._reviewer_registry.assert_grant(
            reviewer_grant_id,
            scope=current.scope,
            policy_version=policy_version,
            role=ReviewerRole.DATA_REVIEWER,
            at=decided_at,
        )
        fingerprint = _digest(
            request_id,
            decision.value,
            grant.id,
            grant.actor_ref,
            evidence_ref,
            policy_version,
            decided_at.isoformat(),
        )
        if decision is ApprovalDecisionKind.APPROVE and grant.actor_ref == current.requested_by:
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
            decision_actor_ref=grant.actor_ref,
            decision_evidence_ref=evidence_ref,
            reviewer_grant_id=grant.id,
            decided_at=decided_at,
        )
        stored = self._append_request_version(decided)
        self._decision_fingerprint_by_key[idempotency_key] = fingerprint
        self._decision_by_key[idempotency_key] = stored
        self._append_audit(
            request=stored,
            actor_ref=grant.actor_ref,
            action=f"decision_{decision.value}",
            state=stored.state,
            evidence_ref=evidence_ref,
            recorded_at=decided_at,
            decision_id=stored.decision_id,
            reviewer_grant_id=grant.id,
        )
        return _snapshot(stored)

    def assert_publishable_request(
        self,
        request: ApprovalRequest,
        *,
        at: datetime,
    ) -> ApprovalRequest:
        if not isinstance(request, ApprovalRequest):
            raise ApprovalBoundaryError("approval_request_required")
        at = _require_safe_time(at, "publication_time_required")
        try:
            request.__post_init__()
        except ApprovalBoundaryError as exc:
            raise ApprovalBoundaryError("approval_request_not_canonical") from exc
        current = self._current_request(request.id)
        if current != request or current.fingerprint != request.fingerprint:
            raise ApprovalBoundaryError("approval_request_not_canonical")
        if current.state is not ApprovalRequestState.APPROVED:
            raise ApprovalBoundaryError("approval_request_not_publishable")
        if at > current.expires_at:
            raise ApprovalBoundaryError("approval_request_expired_at_publish")
        if current.decision_id is None or current.reviewer_grant_id is None:
            raise ApprovalBoundaryError("approval_decision_required")
        self._reviewer_registry.assert_grant(
            current.reviewer_grant_id,
            scope=current.scope,
            policy_version=current.policy_version,
            role=ReviewerRole.DATA_REVIEWER,
            at=current.decided_at,
        )
        if not self._has_decision_audit(current):
            raise ApprovalBoundaryError("approval_decision_audit_required")
        return _snapshot(current)

    def request_version_count(self, request_id: UUID) -> int:
        _require_uuid(request_id, "approval_request_id_required")
        return len(self._versions_by_id.get(request_id, ()))

    @property
    def audit_event_count(self) -> int:
        return len(self._audit_events)

    def safe_audit_summary(self) -> tuple[dict[str, object], ...]:
        return tuple(event.safe_summary() for event in self._audit_events)

    def _current_request(self, request_id: UUID) -> ApprovalRequest:
        current = self._current_by_id.get(request_id)
        if current is None:
            raise ApprovalBoundaryError("approval_request_not_found")
        current.__post_init__()
        if self._current_fingerprint_by_id.get(current.id) != current.fingerprint:
            raise ApprovalBoundaryError("approval_request_drift")
        return current

    def _append_request_version(self, request: ApprovalRequest) -> ApprovalRequest:
        request.__post_init__()
        versions = self._versions_by_id.get(request.id, ())
        if versions:
            previous = versions[-1]
            previous.__post_init__()
            if (
                self._version_fingerprint_by_id.get((previous.id, previous.version_no))
                != previous.fingerprint
            ):
                raise ApprovalBoundaryError("approval_request_drift")
        if versions and request.version_no != versions[-1].version_no + 1:
            raise ApprovalBoundaryError("approval_request_version_sequence_invalid")
        stored = _snapshot(request)
        stored.__post_init__()
        self._versions_by_id[request.id] = (*versions, stored)
        self._current_by_id[request.id] = stored
        self._current_fingerprint_by_id[request.id] = stored.fingerprint
        self._version_fingerprint_by_id[(request.id, request.version_no)] = stored.fingerprint
        return stored

    def _append_audit(
        self,
        *,
        request: ApprovalRequest,
        actor_ref: str,
        action: str,
        state: ApprovalRequestState,
        evidence_ref: str,
        recorded_at: datetime,
        decision_id: Optional[UUID] = None,
        reviewer_grant_id: Optional[UUID] = None,
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
            decision_id=decision_id,
            reviewer_grant_id=reviewer_grant_id,
        )
        stored = _snapshot(event)
        stored.__post_init__()
        self._audit_events = (*self._audit_events, stored)
        self._audit_fingerprint_by_id[stored.id] = stored.fingerprint

    def _has_decision_audit(self, request: ApprovalRequest) -> bool:
        for event in self._audit_events:
            event.__post_init__()
            if self._audit_fingerprint_by_id.get(event.id) != event.fingerprint:
                raise ApprovalBoundaryError("approval_audit_drift")
            if (
                event.request_id == request.id
                and event.decision_id == request.decision_id
                and event.reviewer_grant_id == request.reviewer_grant_id
                and event.actor_ref == request.decision_actor_ref
                and event.state is request.state
                and event.evidence_ref == request.decision_evidence_ref
                and event.policy_version == request.policy_version
            ):
                return True
        return False


class SyntheticInternalPublicationLedger:
    """Append-only ledger for P03 internal publication proofs."""

    def __init__(self) -> None:
        self._records_by_id: dict[UUID, InternalPublicationRecord] = {}
        self._fingerprints_by_id: dict[UUID, str] = {}
        self._series_versions: set[tuple[ScopeRef, str, str, int]] = set()
        self._child_by_parent: dict[UUID, UUID] = {}

    @property
    def appended_record_count(self) -> int:
        return len(self._records_by_id)

    def _snapshot(self) -> tuple[
        dict[UUID, InternalPublicationRecord],
        dict[UUID, str],
        set[tuple[ScopeRef, str, str, int]],
        dict[UUID, UUID],
    ]:
        return (
            _snapshot(self._records_by_id),
            dict(self._fingerprints_by_id),
            set(self._series_versions),
            dict(self._child_by_parent),
        )

    def _restore_from_snapshot(
        self,
        snapshot: tuple[
            dict[UUID, InternalPublicationRecord],
            dict[UUID, str],
            set[tuple[ScopeRef, str, str, int]],
            dict[UUID, UUID],
        ],
    ) -> None:
        self._records_by_id, self._fingerprints_by_id, self._series_versions, self._child_by_parent = (
            _snapshot(snapshot[0]),
            dict(snapshot[1]),
            set(snapshot[2]),
            dict(snapshot[3]),
        )

    def is_head(self, record: InternalPublicationRecord) -> bool:
        if not isinstance(record, InternalPublicationRecord):
            raise ApprovalBoundaryError("internal_publication_required")
        try:
            record.__post_init__()
        except ApprovalBoundaryError as exc:
            raise ApprovalBoundaryError("internal_publication_not_found") from exc
        stored = self._records_by_id.get(record.id)
        if stored is None:
            raise ApprovalBoundaryError("internal_publication_not_found")
        stored.__post_init__()
        if self._fingerprints_by_id.get(stored.id) != stored.fingerprint:
            raise ApprovalBoundaryError("internal_publication_drift")
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

    def append_batch(
        self,
        records: Tuple[InternalPublicationRecord, ...],
    ) -> Tuple[InternalPublicationRecord, ...]:
        if not isinstance(records, tuple) or not records:
            raise ApprovalBoundaryError("internal_publication_batch_required")
        if any(not isinstance(record, InternalPublicationRecord) for record in records):
            raise ApprovalBoundaryError("internal_publication_required")
        staged_input = tuple(_snapshot(record) for record in records)
        for record in staged_input:
            record.__post_init__()
        staged_records = dict(self._records_by_id)
        staged_fingerprints = dict(self._fingerprints_by_id)
        staged_series = set(self._series_versions)
        staged_children = dict(self._child_by_parent)
        for record in staged_input:
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
                parent.__post_init__()
                if staged_fingerprints.get(parent.id) != parent.fingerprint:
                    raise ApprovalBoundaryError("internal_publication_drift")
                if record.parent_record_id in staged_children:
                    raise ApprovalBoundaryError("publication_history_branch_forbidden")
                if record.series_key != parent.series_key:
                    raise ApprovalBoundaryError("publication_subject_mismatch")
                if record.version_no != parent.version_no + 1:
                    raise ApprovalBoundaryError("internal_publication_version_sequence_invalid")
                if record.state not in _PUBLICATION_TRANSITIONS[parent.state]:
                    raise ApprovalBoundaryError("internal_publication_transition_forbidden")
            staged_records[record.id] = record
            staged_fingerprints[record.id] = record.fingerprint
            staged_series.add(series_key)
            if record.parent_record_id is not None:
                staged_children[record.parent_record_id] = record.id
        self._records_by_id = staged_records
        self._fingerprints_by_id = staged_fingerprints
        self._series_versions = staged_series
        self._child_by_parent = staged_children
        return tuple(_snapshot(record) for record in staged_input)


class InMemoryInvalidationOutbox:
    """Internal-only fake outbox; it has no external adapter surface."""

    def __init__(self) -> None:
        self._events_by_id: Dict[UUID, InternalInvalidationEvent] = {}
        self._fingerprints_by_id: Dict[UUID, str] = {}

    @property
    def event_count(self) -> int:
        return len(self._events_by_id)

    def _snapshot(self) -> tuple[dict[UUID, InternalInvalidationEvent], dict[UUID, str]]:
        return _snapshot(self._events_by_id), dict(self._fingerprints_by_id)

    def _restore_from_snapshot(
        self,
        snapshot: tuple[dict[UUID, InternalInvalidationEvent], dict[UUID, str]],
    ) -> None:
        self._events_by_id, self._fingerprints_by_id = (
            _snapshot(snapshot[0]),
            dict(snapshot[1]),
        )

    def append(self, event: InternalInvalidationEvent) -> InternalInvalidationEvent:
        if not isinstance(event, InternalInvalidationEvent):
            raise ApprovalBoundaryError("invalidation_event_required")
        event = _snapshot(event)
        event.__post_init__()
        existing = self._events_by_id.get(event.id)
        if existing is not None:
            existing.__post_init__()
            if (
                self._fingerprints_by_id[event.id] != event.fingerprint
                or existing.fingerprint != event.fingerprint
                or existing != event
            ):
                raise ApprovalBoundaryError("invalidation_event_idempotency_conflict")
            return _snapshot(existing)
        self._events_by_id[event.id] = event
        self._fingerprints_by_id[event.id] = event.fingerprint
        return _snapshot(event)

    def safe_summary(self) -> tuple[dict[str, object], ...]:
        return tuple(event.safe_summary() for event in self._events_by_id.values())


class SyntheticPublicationTransactionLog:
    """Shared local transaction state for idempotent publication/revoke commits."""

    def __init__(self) -> None:
        self._results_by_key: Dict[str, object] = {}
        self._fingerprints_by_key: Dict[str, str] = {}

    def _snapshot(self) -> tuple[dict[str, object], dict[str, str]]:
        return _snapshot(self._results_by_key), dict(self._fingerprints_by_key)

    def _restore_from_snapshot(self, snapshot: tuple[dict[str, object], dict[str, str]]) -> None:
        self._results_by_key, self._fingerprints_by_key = (
            _snapshot(snapshot[0]),
            dict(snapshot[1]),
        )

    def get(self, key: str) -> object | None:
        _require_safe_hash(key, "publication_transaction_key_required")
        existing = self._results_by_key.get(key)
        return _snapshot(existing) if existing is not None else None

    def commit(self, key: str, result: object, fingerprint: str) -> object:
        _require_safe_hash(key, "publication_transaction_key_required")
        _require_safe_hash(fingerprint, "publication_transaction_fingerprint_required")
        existing = self._results_by_key.get(key)
        if existing is not None:
            if self._fingerprints_by_key[key] != fingerprint or existing != result:
                raise ApprovalBoundaryError("publication_transaction_conflict")
            return _snapshot(existing)
        self._results_by_key[key] = _snapshot(result)
        self._fingerprints_by_key[key] = fingerprint
        return _snapshot(result)


class SyntheticApprovalPublisher:
    """Publish approved canonical requests into an internal synthetic proof ledger."""

    def __init__(
        self,
        *,
        request_store: InMemoryApprovalRequestStore,
        reviewer_registry: SyntheticReviewerCapabilityRegistry,
        ledger: SyntheticInternalPublicationLedger,
        outbox: InMemoryInvalidationOutbox,
        transaction_log: SyntheticPublicationTransactionLog,
        now: Optional[Callable[[], datetime]] = None,
    ) -> None:
        if not isinstance(request_store, InMemoryApprovalRequestStore):
            raise ApprovalBoundaryError("approval_request_store_required")
        if not isinstance(reviewer_registry, SyntheticReviewerCapabilityRegistry):
            raise ApprovalBoundaryError("reviewer_capability_registry_required")
        if not isinstance(ledger, SyntheticInternalPublicationLedger):
            raise ApprovalBoundaryError("internal_publication_ledger_required")
        if not isinstance(outbox, InMemoryInvalidationOutbox):
            raise ApprovalBoundaryError("invalidation_outbox_required")
        if not isinstance(transaction_log, SyntheticPublicationTransactionLog):
            raise ApprovalBoundaryError("publication_transaction_log_required")
        self._request_store = request_store
        self._reviewer_registry = reviewer_registry
        self._ledger = ledger
        self._outbox = outbox
        self._transaction_log = transaction_log
        self._now = now or (lambda: datetime.now(timezone.utc))

    def publish(
        self,
        request: ApprovalRequest,
        *,
        supersedes: Optional[object] = None,
    ) -> InternalPublicationResult:
        published_at = _require_safe_time(self._now(), "publication_time_required")
        request = self._request_store.assert_publishable_request(request, at=published_at)
        candidate = request.candidate
        superseded_source: Optional[InternalPublicationRecord] = None
        if supersedes is not None:
            if isinstance(supersedes, InternalPublicationResult):
                superseded_source = supersedes.approved_record
            elif isinstance(supersedes, InternalRevocationResult):
                superseded_source = supersedes.revoked_record
            elif isinstance(supersedes, InternalPublicationRecord):
                superseded_source = supersedes
            else:
                raise ApprovalBoundaryError("superseded_publication_required")
            superseded_source = _snapshot(superseded_source)
            superseded_source.__post_init__()
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
        existing = self._transaction_log.get(publish_key)
        if existing is not None:
            if not isinstance(existing, InternalPublicationResult):
                raise ApprovalBoundaryError("publication_transaction_conflict")
            return existing

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
                revoked_record_id=None,
                published_at=published_at,
            )
            records = (approved_record,)
        elif superseded_source.state is InternalPublicationState.APPROVED_INTERNAL:
            superseded_record = self._record_for(
                request=request,
                state=InternalPublicationState.SUPERSEDED_INTERNAL,
                version_no=superseded_source.version_no + 1,
                parent_record_id=superseded_source.id,
                superseded_record_id=superseded_source.id,
                revoked_record_id=None,
                published_at=published_at,
                source_record=superseded_source,
            )
            approved_record = self._record_for(
                request=request,
                state=InternalPublicationState.APPROVED_INTERNAL,
                version_no=superseded_record.version_no + 1,
                parent_record_id=superseded_record.id,
                superseded_record_id=superseded_source.id,
                revoked_record_id=None,
                published_at=published_at,
            )
            records = (superseded_record, approved_record)
        else:
            approved_record = self._record_for(
                request=request,
                state=InternalPublicationState.APPROVED_INTERNAL,
                version_no=superseded_source.version_no + 1,
                parent_record_id=superseded_source.id,
                superseded_record_id=superseded_source.id,
                revoked_record_id=None,
                published_at=published_at,
            )
            records = (approved_record,)
        event = self._event_for(
            record=approved_record,
            occurred_at=published_at,
            superseded_publication_id=(
                superseded_source.id if superseded_source is not None else None
            ),
            revoked_publication_id=None,
        )
        result = InternalPublicationResult(
            approved_record=approved_record,
            superseded_record=superseded_record,
            event=event,
        )
        return self._commit_transaction(publish_key, records, event, result)

    def revoke(
        self,
        publication: InternalPublicationResult,
        *,
        reviewer_grant_id: UUID,
        evidence_ref: str,
        policy_version: str,
        idempotency_key: str,
    ) -> InternalRevocationResult:
        revoked_at = _require_safe_time(self._now(), "publication_time_required")
        if not isinstance(publication, InternalPublicationResult):
            raise ApprovalBoundaryError("internal_publication_required")
        current = publication.approved_record
        grant = self._reviewer_registry.assert_grant(
            reviewer_grant_id,
            scope=current.scope,
            policy_version=policy_version,
            role=ReviewerRole.DATA_REVIEWER,
            at=revoked_at,
        )
        _require_safe_identifier(evidence_ref, "approval_decision_evidence_required")
        _require_safe_identifier(idempotency_key, "approval_idempotency_key_required")
        revoke_key = _digest("revoke", current.id, grant.id, evidence_ref, policy_version, idempotency_key)
        existing = self._transaction_log.get(revoke_key)
        if existing is not None:
            if not isinstance(existing, InternalRevocationResult):
                raise ApprovalBoundaryError("publication_transaction_conflict")
            return existing
        if not self._ledger.is_head(current):
            raise ApprovalBoundaryError("revoked_publication_not_current")
        revoked_record = InternalPublicationRecord(
            id=_uuid_for("internal-revoke", current.id, grant.id, idempotency_key),
            scope=current.scope,
            request_id=current.request_id,
            decision_id=current.decision_id,
            candidate_id=current.candidate_id,
            subject_ref=current.subject_ref,
            target_field=current.target_field,
            version_no=current.version_no + 1,
            state=InternalPublicationState.REVOKED_INTERNAL,
            payload_hash=current.payload_hash,
            source_content_hash=current.source_content_hash,
            source_file_id=current.source_file_id,
            ingestion_job_id=current.ingestion_job_id,
            extraction_result_id=current.extraction_result_id,
            staging_candidate_id=current.staging_candidate_id,
            locator_fingerprint=current.locator_fingerprint,
            profile_id=current.profile_id,
            profile_version=current.profile_version,
            rule_id=current.rule_id,
            actor_ref=grant.actor_ref,
            evidence_ref=evidence_ref,
            policy_version=policy_version,
            published_at=revoked_at,
            parent_record_id=current.id,
            revoked_record_id=current.id,
        )
        event = self._event_for(
            record=revoked_record,
            occurred_at=revoked_at,
            superseded_publication_id=None,
            revoked_publication_id=current.id,
        )
        result = InternalRevocationResult(revoked_record=revoked_record, event=event)
        return self._commit_transaction(revoke_key, (revoked_record,), event, result)

    def _commit_transaction(
        self,
        key: str,
        records: Tuple[InternalPublicationRecord, ...],
        event: InternalInvalidationEvent,
        result,
    ):
        ledger_snapshot = self._ledger._snapshot()
        outbox_snapshot = self._outbox._snapshot()
        transaction_snapshot = self._transaction_log._snapshot()
        fingerprint = _digest(
            *(record.fingerprint for record in records),
            event.fingerprint,
            repr(result.safe_summary()),
        )
        try:
            appended_records = self._ledger.append_batch(records)
            if appended_records != records:
                raise ApprovalBoundaryError("internal_publication_commit_mismatch")
            appended_event = self._outbox.append(event)
            if appended_event != event:
                raise ApprovalBoundaryError("invalidation_event_idempotency_conflict")
            committed = self._transaction_log.commit(key, result, fingerprint)
            if committed != result:
                raise ApprovalBoundaryError("publication_transaction_conflict")
        except Exception:
            self._ledger._restore_from_snapshot(ledger_snapshot)
            self._outbox._restore_from_snapshot(outbox_snapshot)
            self._transaction_log._restore_from_snapshot(transaction_snapshot)
            raise
        return _snapshot(result)

    @staticmethod
    def _record_for(
        *,
        request: ApprovalRequest,
        state: InternalPublicationState,
        version_no: int,
        parent_record_id: Optional[UUID],
        superseded_record_id: Optional[UUID],
        revoked_record_id: Optional[UUID],
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
                revoked_record_id,
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
                else candidate.locator_fingerprint
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
            revoked_record_id=revoked_record_id,
        )

    @staticmethod
    def _event_for(
        *,
        record: InternalPublicationRecord,
        occurred_at: datetime,
        superseded_publication_id: Optional[UUID],
        revoked_publication_id: Optional[UUID],
    ) -> InternalInvalidationEvent:
        return InternalInvalidationEvent(
            id=_uuid_for(
                "internal-invalidation",
                record.id,
                superseded_publication_id or "no_supersede",
                revoked_publication_id or "no_revoke",
            ),
            scope=record.scope,
            publication_id=record.id,
            event_type="TruthFactsChanged",
            destination="internal_invalidation_outbox",
            subject_ref=record.subject_ref,
            target_field=record.target_field,
            version_no=record.version_no,
            correlation_id=record.scope.correlation_id,
            occurred_at=occurred_at,
            superseded_publication_id=superseded_publication_id,
            revoked_publication_id=revoked_publication_id,
        )


__all__ = [
    "ApprovalBoundaryError",
    "ApprovalDecisionKind",
    "ApprovalRequest",
    "ApprovalRequestState",
    "CanonicalMappedCandidate",
    "CanonicalMappingCandidateGate",
    "InMemoryApprovalRequestStore",
    "InMemoryInvalidationOutbox",
    "InternalInvalidationEvent",
    "InternalPublicationRecord",
    "InternalPublicationResult",
    "InternalPublicationState",
    "InternalRevocationResult",
    "ReviewerCapabilityGrant",
    "ReviewerRole",
    "SyntheticApprovalPublisher",
    "SyntheticInternalPublicationLedger",
    "SyntheticPublicationTransactionLog",
    "SyntheticReviewerCapabilityRegistry",
]
