"""P05-02 synthetic CRM, DNC, retention, and export contracts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import csv
import io
import re
from typing import Any

from core.contracts import ContractValidationError, DataState, ScopeRef
from core.contracts.leads_crm import (
    LeadDedupeResult,
    LeadReview,
    LeadReviewDecision,
    SyntheticLeadCandidate,
    require_hash,
    require_identifier,
    require_scope,
    require_synthetic_fixture_boundary,
    require_time,
    stable_ref,
)


_PROMPT_BYPASS = re.compile(r"(?i)(ignore[-_ ]?dnc|admin[-_ ]?override|send[-_ ]?anyway|bypass)")


class CrmBoundaryError(ContractValidationError):
    """Stable, value-free P05-02 CRM boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class CrmStage(str, Enum):
    REVIEWED = "reviewed"
    MANUAL_REVIEW = "manual_review"
    CLOSED_BLOCKED = "closed_blocked"


class InteractionKind(str, Enum):
    INTERNAL_NOTE = "internal_note"
    DRAFT = "draft"
    SEND_ATTEMPT = "send_attempt"


def _boundary(code: str) -> CrmBoundaryError:
    return CrmBoundaryError(code)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _scope_key(scope: ScopeRef) -> tuple[object, object, object]:
    return (scope.tenant_id, scope.project_id, scope.business_line_id)


def _assert_same_scope(left: ScopeRef, right: ScopeRef) -> None:
    if left != right:
        raise _boundary("cross_scope_forbidden")


def _record_audit(
    audit_log: object,
    *,
    event_kind: str,
    scope: ScopeRef,
    command_ref: str,
    target_ref: str,
    policy_version: str,
    result_code: str,
    actor_ref: str = "crm_contract_guard",
    subject_version: int = 1,
    metadata: Mapping[str, object] | None = None,
) -> None:
    record = getattr(audit_log, "record", None)
    if not callable(record):
        raise _boundary("audit_persistence_required")
    record(
        event_kind=event_kind,
        actor_ref=actor_ref,
        scope=scope,
        command_ref=command_ref,
        target_ref=target_ref,
        policy_version=policy_version,
        subject_version=subject_version,
        result_code=result_code,
        metadata=metadata,
    )


@dataclass(frozen=True)
class DncRecord:
    scope: ScopeRef
    dnc_ref: str
    subject_hash: str
    evidence_ref: str
    actor_ref: str
    reason_code: str
    created_at: datetime

    def __post_init__(self) -> None:
        require_scope(self.scope)
        require_identifier(self.dnc_ref, "dnc_ref_required")
        require_hash(self.subject_hash, "dnc_subject_required")
        require_identifier(self.evidence_ref, "dnc_evidence_required")
        require_identifier(self.actor_ref, "actor_ref_required")
        require_identifier(self.reason_code, "dnc_reason_required")
        require_time(self.created_at, "created_at_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "dnc_ref": self.dnc_ref,
            "subject_hash": self.subject_hash,
            "evidence_ref": self.evidence_ref,
            "actor_ref": self.actor_ref,
            "reason_code": self.reason_code,
            "created_at": self.created_at.isoformat(),
        }


class DncRegistry:
    """Append-only DNC/withdrawal registry with no update/delete surface."""

    __slots__ = ("_audit_log", "_by_idempotency", "_by_subject", "_fingerprints", "_now", "_records")

    def __init__(
        self,
        *,
        audit_log: object,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._audit_log = audit_log
        self._now = now or _now_utc
        self._records: tuple[DncRecord, ...] = ()
        self._by_subject: dict[tuple[tuple[object, object, object], str], DncRecord] = {}
        self._by_idempotency: dict[str, DncRecord] = {}
        self._fingerprints: dict[str, str] = {}

    @property
    def records(self) -> tuple[DncRecord, ...]:
        return self._records

    def record_withdrawal(
        self,
        *,
        scope: ScopeRef,
        subject_hash: str,
        evidence_ref: str,
        actor_ref: str,
        reason_code: str,
        idempotency_key: str,
    ) -> DncRecord:
        scope = require_scope(scope)
        subject = require_hash(subject_hash, "dnc_subject_required")
        key = require_identifier(idempotency_key, "idempotency_key_required")
        evidence = require_identifier(evidence_ref, "dnc_evidence_required")
        actor = require_identifier(actor_ref, "actor_ref_required")
        reason = require_identifier(reason_code, "dnc_reason_required")
        fingerprint = _digest(scope, subject, evidence, actor, reason)
        existing = self._by_idempotency.get(key)
        if existing is not None:
            if self._fingerprints[key] != fingerprint:
                raise _boundary("idempotency_conflict")
            return existing
        subject_key = (_scope_key(scope), subject)
        already_blocked = self._by_subject.get(subject_key)
        if already_blocked is not None:
            return already_blocked
        record = DncRecord(
            scope=scope,
            dnc_ref=stable_ref("dnc", scope.tenant_id, scope.project_id, scope.business_line_id, subject),
            subject_hash=subject,
            evidence_ref=evidence,
            actor_ref=actor,
            reason_code=reason,
            created_at=self._now(),
        )
        self._records = (*self._records, record)
        self._by_subject[subject_key] = record
        self._by_idempotency[key] = record
        self._fingerprints[key] = fingerprint
        _record_audit(
            self._audit_log,
            event_kind="crm_dnc_recorded",
            scope=scope,
            command_ref="crm.dnc.record_withdrawal",
            target_ref=record.dnc_ref,
            policy_version="p05_02_crm_domain",
            result_code="dnc_recorded",
            actor_ref=actor,
            metadata={"reason_code": reason},
        )
        return record

    def is_blocked(self, scope: ScopeRef, subject_hash: str) -> bool:
        return (_scope_key(require_scope(scope)), require_hash(subject_hash, "dnc_subject_required")) in self._by_subject


@dataclass(frozen=True)
class Organization:
    scope: ScopeRef
    organization_ref: str
    review_ref: str
    source_policy_id: str
    source_url_hash: str
    organization_fingerprint: str
    dnc_subject_hash: str
    data_state: DataState
    is_synthetic: bool
    external_execution_allowed: bool
    business_external_ready: bool
    created_at: datetime
    created_by: str

    def __post_init__(self) -> None:
        require_scope(self.scope)
        require_identifier(self.organization_ref, "organization_ref_required")
        require_identifier(self.review_ref, "review_ref_required")
        require_identifier(self.source_policy_id, "source_policy_required")
        require_hash(self.source_url_hash, "source_url_hash_required")
        require_hash(self.organization_fingerprint, "organization_fingerprint_required")
        require_hash(self.dnc_subject_hash, "dnc_subject_required")
        require_time(self.created_at, "created_at_required")
        require_identifier(self.created_by, "created_by_required")
        require_synthetic_fixture_boundary(
            data_state=self.data_state,
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            business_external_ready=self.business_external_ready,
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "organization_ref": self.organization_ref,
            "review_ref": self.review_ref,
            "source_policy_id": self.source_policy_id,
            "source_url_hash": self.source_url_hash,
            "organization_fingerprint": self.organization_fingerprint,
            "dnc_subject_hash": self.dnc_subject_hash,
            "data_state": self.data_state.value,
            "is_synthetic": self.is_synthetic,
            "external_execution_allowed": self.external_execution_allowed,
            "business_external_ready": self.business_external_ready,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }


@dataclass(frozen=True)
class Contact:
    scope: ScopeRef
    contact_ref: str
    organization_ref: str
    subject_hash: str
    source_evidence_ref: str
    consent_granted: bool
    dnc_blocked: bool
    data_state: DataState
    is_synthetic: bool
    external_execution_allowed: bool
    business_external_ready: bool
    created_at: datetime

    def __post_init__(self) -> None:
        require_scope(self.scope)
        require_identifier(self.contact_ref, "contact_ref_required")
        require_identifier(self.organization_ref, "organization_ref_required")
        require_hash(self.subject_hash, "contact_subject_required")
        require_identifier(self.source_evidence_ref, "contact_source_consent_required")
        if self.consent_granted is not True or self.dnc_blocked is not False:
            raise _boundary("contact_source_consent_required")
        require_time(self.created_at, "created_at_required")
        require_synthetic_fixture_boundary(
            data_state=self.data_state,
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            business_external_ready=self.business_external_ready,
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "contact_ref": self.contact_ref,
            "organization_ref": self.organization_ref,
            "subject_hash": self.subject_hash,
            "source_evidence_ref": self.source_evidence_ref,
            "consent_granted": self.consent_granted,
            "dnc_blocked": self.dnc_blocked,
            "data_state": self.data_state.value,
            "is_synthetic": self.is_synthetic,
            "external_execution_allowed": self.external_execution_allowed,
            "business_external_ready": self.business_external_ready,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class Opportunity:
    scope: ScopeRef
    opportunity_ref: str
    organization_ref: str
    stage: CrmStage
    amount_state: str
    external_execution_allowed: bool
    business_external_ready: bool
    created_at: datetime

    def __post_init__(self) -> None:
        require_scope(self.scope)
        require_identifier(self.opportunity_ref, "opportunity_ref_required")
        require_identifier(self.organization_ref, "organization_ref_required")
        if not isinstance(self.stage, CrmStage):
            raise _boundary("crm_stage_required")
        require_identifier(self.amount_state, "amount_state_required")
        if self.external_execution_allowed is not False:
            raise _boundary("external_execution_forbidden")
        if self.business_external_ready is not False:
            raise _boundary("business_external_ready_forbidden")
        require_time(self.created_at, "created_at_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "opportunity_ref": self.opportunity_ref,
            "organization_ref": self.organization_ref,
            "stage": self.stage.value,
            "amount_state": self.amount_state,
            "external_execution_allowed": self.external_execution_allowed,
            "business_external_ready": self.business_external_ready,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class Interaction:
    scope: ScopeRef
    interaction_ref: str
    organization_ref: str
    kind: InteractionKind
    subject_hash: str
    sent_count: int
    external_sent: bool
    created_at: datetime

    def __post_init__(self) -> None:
        require_scope(self.scope)
        require_identifier(self.interaction_ref, "interaction_ref_required")
        require_identifier(self.organization_ref, "organization_ref_required")
        if not isinstance(self.kind, InteractionKind):
            raise _boundary("interaction_kind_required")
        require_hash(self.subject_hash, "interaction_subject_required")
        if self.sent_count != 0 or self.external_sent is not False:
            raise _boundary("external_send_forbidden")
        require_time(self.created_at, "created_at_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "interaction_ref": self.interaction_ref,
            "organization_ref": self.organization_ref,
            "kind": self.kind.value,
            "subject_hash": self.subject_hash,
            "sent_count": self.sent_count,
            "external_sent": self.external_sent,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class RetentionIntent:
    scope: ScopeRef
    retention_ref: str
    subject_ref: str
    intent: str
    evidence_ref: str
    actor_ref: str
    created_at: datetime

    def __post_init__(self) -> None:
        require_scope(self.scope)
        require_identifier(self.retention_ref, "retention_ref_required")
        require_identifier(self.subject_ref, "retention_subject_required")
        if self.intent not in {"delete_requested", "anonymize_requested", "retain_minimized"}:
            raise _boundary("retention_intent_required")
        require_identifier(self.evidence_ref, "retention_evidence_required")
        require_identifier(self.actor_ref, "actor_ref_required")
        require_time(self.created_at, "created_at_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "retention_ref": self.retention_ref,
            "subject_ref": self.subject_ref,
            "intent": self.intent,
            "evidence_ref": self.evidence_ref,
            "actor_ref": self.actor_ref,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class CrmRecordSet:
    organization: Organization
    opportunity: Opportunity
    interaction: Interaction


@dataclass(frozen=True)
class CrmExport:
    export_ref: str
    json_payload: Mapping[str, object]
    csv_payloads: Mapping[str, str]


class CrmRepository:
    """In-memory CRM truth contract used before any real CRM adapter exists."""

    __slots__ = (
        "_audit_log",
        "_contacts",
        "_crm_by_idempotency",
        "_dnc",
        "_identity_index",
        "_interactions",
        "_lead_reviews",
        "_now",
        "_opportunities",
        "_organizations",
        "_retention_by_idempotency",
        "_retention_intents",
        "_review_by_idempotency",
        "_review_fingerprints",
        "_source_index",
    )

    def __init__(
        self,
        *,
        dnc_registry: DncRegistry,
        audit_log: object,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._dnc = dnc_registry
        self._audit_log = audit_log
        self._now = now or _now_utc
        self._lead_reviews: dict[str, LeadReview] = {}
        self._review_by_idempotency: dict[str, LeadReview] = {}
        self._review_fingerprints: dict[str, str] = {}
        self._organizations: dict[str, Organization] = {}
        self._opportunities: dict[str, Opportunity] = {}
        self._interactions: dict[str, Interaction] = {}
        self._contacts: dict[str, Contact] = {}
        self._retention_intents: tuple[RetentionIntent, ...] = ()
        self._retention_by_idempotency: dict[str, RetentionIntent] = {}
        self._crm_by_idempotency: dict[str, CrmRecordSet] = {}
        self._source_index: dict[tuple[tuple[object, object, object], str, str], str] = {}
        self._identity_index: dict[tuple[tuple[object, object, object], str], set[str]] = {}

    @property
    def organizations(self) -> tuple[Organization, ...]:
        return tuple(self._organizations.values())

    @property
    def contacts(self) -> tuple[Contact, ...]:
        return tuple(self._contacts.values())

    @property
    def opportunities(self) -> tuple[Opportunity, ...]:
        return tuple(self._opportunities.values())

    @property
    def interactions(self) -> tuple[Interaction, ...]:
        return tuple(self._interactions.values())

    @property
    def retention_intents(self) -> tuple[RetentionIntent, ...]:
        return self._retention_intents

    def review_lead(
        self,
        candidate: SyntheticLeadCandidate,
        *,
        decision: LeadReviewDecision,
        reviewer_ref: str,
        review_evidence_ref: str,
        idempotency_key: str,
        expected_scope: ScopeRef | None = None,
    ) -> LeadReview:
        if not isinstance(candidate, SyntheticLeadCandidate):
            raise _boundary("lead_candidate_required")
        if expected_scope is not None:
            _assert_same_scope(candidate.scope, expected_scope)
        if not isinstance(decision, LeadReviewDecision):
            raise _boundary("review_decision_required")
        reviewer = require_identifier(reviewer_ref, "reviewer_ref_required")
        evidence = require_identifier(review_evidence_ref, "review_evidence_required")
        key = require_identifier(idempotency_key, "idempotency_key_required")
        fingerprint = _digest(candidate.safe_summary(), decision.value, reviewer, evidence)
        existing = self._review_by_idempotency.get(key)
        if existing is not None:
            if self._review_fingerprints[key] != fingerprint:
                raise _boundary("idempotency_conflict")
            return existing
        if decision is LeadReviewDecision.APPROVE and candidate.identity_confidence == "unresolved":
            raise _boundary("merge_candidate_manual_review_required")
        dedupe_result = self._dedupe(candidate)
        review = LeadReview(
            review_ref=stable_ref("lead_review", candidate.scope, candidate.lead_ref, key),
            candidate=candidate,
            decision=decision,
            reviewer_ref=reviewer,
            review_evidence_ref=evidence,
            dedupe_result=dedupe_result,
            reviewed_at=self._now(),
        )
        self._lead_reviews[review.review_ref] = review
        self._review_by_idempotency[key] = review
        self._review_fingerprints[key] = fingerprint
        _record_audit(
            self._audit_log,
            event_kind="lead_reviewed",
            scope=candidate.scope,
            command_ref="crm.review_lead",
            target_ref=review.review_ref,
            policy_version="p05_02_crm_domain",
            result_code=decision.value,
            actor_ref=reviewer,
            metadata={"reason_code": dedupe_result.result},
        )
        return review

    def create_crm_record(
        self,
        review_ref: str,
        *,
        organization_ref: str,
        opportunity_ref: str,
        interaction_ref: str,
        stage: CrmStage,
        owner_ref: str,
        idempotency_key: str,
        expected_scope: ScopeRef | None = None,
    ) -> CrmRecordSet:
        key = require_identifier(idempotency_key, "idempotency_key_required")
        existing = self._crm_by_idempotency.get(key)
        if existing is not None:
            return existing
        review = self._approved_new_review(review_ref)
        if expected_scope is not None:
            _assert_same_scope(review.scope, expected_scope)
        created_by = require_identifier(owner_ref, "owner_ref_required")
        if not isinstance(stage, CrmStage):
            raise _boundary("crm_stage_required")
        candidate = review.candidate
        organization = Organization(
            scope=candidate.scope,
            organization_ref=require_identifier(organization_ref, "organization_ref_required"),
            review_ref=review.review_ref,
            source_policy_id=candidate.source_policy_id,
            source_url_hash=candidate.source_url_hash,
            organization_fingerprint=candidate.organization_fingerprint,
            dnc_subject_hash=candidate.dnc_subject_hash,
            data_state=DataState.FIXTURE,
            is_synthetic=True,
            external_execution_allowed=False,
            business_external_ready=False,
            created_at=self._now(),
            created_by=created_by,
        )
        opportunity = Opportunity(
            scope=candidate.scope,
            opportunity_ref=require_identifier(opportunity_ref, "opportunity_ref_required"),
            organization_ref=organization.organization_ref,
            stage=stage,
            amount_state="unknown_not_priced",
            external_execution_allowed=False,
            business_external_ready=False,
            created_at=self._now(),
        )
        interaction = Interaction(
            scope=candidate.scope,
            interaction_ref=require_identifier(interaction_ref, "interaction_ref_required"),
            organization_ref=organization.organization_ref,
            kind=InteractionKind.INTERNAL_NOTE,
            subject_hash=organization.dnc_subject_hash,
            sent_count=0,
            external_sent=False,
            created_at=self._now(),
        )
        record_set = CrmRecordSet(
            organization=organization,
            opportunity=opportunity,
            interaction=interaction,
        )
        self._organizations[organization.organization_ref] = organization
        self._opportunities[opportunity.opportunity_ref] = opportunity
        self._interactions[interaction.interaction_ref] = interaction
        self._crm_by_idempotency[key] = record_set
        self._source_index[
            (_scope_key(candidate.scope), candidate.organization_fingerprint, candidate.source_url_hash)
        ] = organization.organization_ref
        self._identity_index.setdefault(
            (_scope_key(candidate.scope), candidate.organization_fingerprint),
            set(),
        ).add(candidate.source_url_hash)
        _record_audit(
            self._audit_log,
            event_kind="crm_record_created",
            scope=candidate.scope,
            command_ref="crm.create_record",
            target_ref=organization.organization_ref,
            policy_version="p05_02_crm_domain",
            result_code="crm_record_created",
            actor_ref=created_by,
            metadata={"reason_code": stage.value, "item_count": 3},
        )
        return record_set

    def create_contact(
        self,
        organization_ref: str,
        *,
        contact_ref: str,
        subject_hash: str,
        source_evidence_ref: str | None,
        consent_granted: bool,
        idempotency_key: str,
    ) -> Contact:
        require_identifier(idempotency_key, "idempotency_key_required")
        organization = self._organization(organization_ref)
        if source_evidence_ref is None or consent_granted is not True:
            raise _boundary("contact_source_consent_required")
        subject = require_hash(subject_hash, "contact_subject_required")
        if self._dnc.is_blocked(organization.scope, subject):
            raise _boundary("dnc_blocked")
        contact = Contact(
            scope=organization.scope,
            contact_ref=require_identifier(contact_ref, "contact_ref_required"),
            organization_ref=organization.organization_ref,
            subject_hash=subject,
            source_evidence_ref=source_evidence_ref,
            consent_granted=True,
            dnc_blocked=False,
            data_state=DataState.FIXTURE,
            is_synthetic=True,
            external_execution_allowed=False,
            business_external_ready=False,
            created_at=self._now(),
        )
        self._contacts[contact.contact_ref] = contact
        _record_audit(
            self._audit_log,
            event_kind="crm_party_created",
            scope=organization.scope,
            command_ref="crm.create_party",
            target_ref=contact.contact_ref,
            policy_version="p05_02_crm_domain",
            result_code="party_created",
            metadata={"party_count": 1},
        )
        return contact

    def create_interaction(
        self,
        organization_ref: str,
        *,
        interaction_ref: str,
        kind: InteractionKind,
        subject_hash: str,
        prompt_instruction: str | None,
        idempotency_key: str,
    ) -> Interaction:
        require_identifier(idempotency_key, "idempotency_key_required")
        organization = self._organization(organization_ref)
        subject = require_hash(subject_hash, "interaction_subject_required")
        if self._dnc.is_blocked(organization.scope, subject):
            raise _boundary("dnc_blocked")
        if prompt_instruction is not None and _PROMPT_BYPASS.search(prompt_instruction) is not None:
            raise _boundary("prompt_override_forbidden")
        if kind is InteractionKind.SEND_ATTEMPT:
            raise _boundary("external_send_forbidden")
        interaction = Interaction(
            scope=organization.scope,
            interaction_ref=interaction_ref,
            organization_ref=organization.organization_ref,
            kind=kind,
            subject_hash=subject,
            sent_count=0,
            external_sent=False,
            created_at=self._now(),
        )
        self._interactions[interaction.interaction_ref] = interaction
        _record_audit(
            self._audit_log,
            event_kind="crm_interaction_created",
            scope=organization.scope,
            command_ref="crm.create_interaction",
            target_ref=interaction.interaction_ref,
            policy_version="p05_02_crm_domain",
            result_code="interaction_created",
            metadata={"reason_code": kind.value},
        )
        return interaction

    def record_retention_intent(
        self,
        *,
        scope: ScopeRef,
        subject_ref: str,
        intent: str,
        evidence_ref: str,
        actor_ref: str,
        idempotency_key: str,
    ) -> RetentionIntent:
        scope = require_scope(scope)
        key = require_identifier(idempotency_key, "idempotency_key_required")
        existing = self._retention_by_idempotency.get(key)
        if existing is not None:
            return existing
        retention = RetentionIntent(
            scope=scope,
            retention_ref=stable_ref("retention", scope, subject_ref, intent, key),
            subject_ref=subject_ref,
            intent=intent,
            evidence_ref=evidence_ref,
            actor_ref=actor_ref,
            created_at=self._now(),
        )
        self._retention_intents = (*self._retention_intents, retention)
        self._retention_by_idempotency[key] = retention
        _record_audit(
            self._audit_log,
            event_kind="crm_retention_recorded",
            scope=scope,
            command_ref="crm.record_retention_intent",
            target_ref=retention.retention_ref,
            policy_version="p05_02_crm_domain",
            result_code="retention_recorded",
            actor_ref=retention.actor_ref,
            metadata={"reason_code": intent},
        )
        return retention

    def has_data(self) -> bool:
        return bool(
            self._lead_reviews
            or self._organizations
            or self._contacts
            or self._opportunities
            or self._interactions
        )

    def data_scopes(self) -> set[tuple[object, object, object]]:
        return {
            _scope_key(item.scope)
            for collection in (
                self._lead_reviews.values(),
                self._organizations.values(),
                self._contacts.values(),
                self._opportunities.values(),
                self._interactions.values(),
                self._retention_intents,
            )
            for item in collection
        }

    def _dedupe(self, candidate: SyntheticLeadCandidate) -> LeadDedupeResult:
        same_source = self._source_index.get(
            (_scope_key(candidate.scope), candidate.organization_fingerprint, candidate.source_url_hash)
        )
        if same_source is not None:
            return LeadDedupeResult(
                result="duplicate",
                reason_codes=("same_source_fingerprint",),
                matched_ref=same_source,
            )
        source_hashes = self._identity_index.get((_scope_key(candidate.scope), candidate.organization_fingerprint))
        if source_hashes and candidate.source_url_hash not in source_hashes:
            return LeadDedupeResult(
                result="merge_candidate",
                reason_codes=("manual_identity_review_required",),
            )
        return LeadDedupeResult(result="new", reason_codes=("no_existing_source_match",))

    def _approved_new_review(self, review_ref: str) -> LeadReview:
        review = self._lead_reviews.get(require_identifier(review_ref, "review_ref_required"))
        if review is None or review.decision is not LeadReviewDecision.APPROVE:
            raise _boundary("lead_review_required")
        if review.dedupe_result.result == "merge_candidate":
            raise _boundary("merge_candidate_manual_review_required")
        if review.dedupe_result.result == "duplicate":
            raise _boundary("duplicate_lead_requires_manual_review")
        return review

    def _organization(self, organization_ref: str) -> Organization:
        organization = self._organizations.get(require_identifier(organization_ref, "organization_ref_required"))
        if organization is None:
            raise _boundary("organization_required")
        return organization


class CrmExportService:
    """Scoped internal export that keeps this system as CRM truth."""

    def __init__(
        self,
        repository: CrmRepository,
        *,
        audit_log: object,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._audit_log = audit_log
        self._now = now or _now_utc

    def export_scope(self, scope: ScopeRef, *, requester_ref: str) -> CrmExport:
        scope = require_scope(scope)
        requester = require_identifier(requester_ref, "requester_ref_required")
        if self._repository.has_data() and _scope_key(scope) not in self._repository.data_scopes():
            raise _boundary("cross_scope_forbidden")
        retention_subjects = {
            item.subject_ref
            for item in self._repository.retention_intents
            if item.scope == scope and item.intent in {"delete_requested", "anonymize_requested"}
        }
        organizations = [item for item in self._repository.organizations if item.scope == scope]
        contacts = [
            item for item in self._repository.contacts
            if item.scope == scope and item.contact_ref not in retention_subjects
        ]
        opportunities = [item for item in self._repository.opportunities if item.scope == scope]
        interactions = [item for item in self._repository.interactions if item.scope == scope]
        retention = [item for item in self._repository.retention_intents if item.scope == scope]
        export_ref = stable_ref("crm_export", scope, self._now().isoformat(), len(organizations))
        json_payload: dict[str, object] = {
            "export_ref": export_ref,
            "scope": {
                "tenant_id": str(scope.tenant_id),
                "project_id": str(scope.project_id),
                "business_line_id": str(scope.business_line_id),
            },
            "crm_truth": "internal_contract",
            "future_adapter_status": "deferred",
            "organizations": [item.safe_summary() for item in organizations],
            "contacts": [item.safe_summary() for item in contacts],
            "opportunities": [item.safe_summary() for item in opportunities],
            "interactions": [item.safe_summary() for item in interactions],
            "dnc_records": [
                item.safe_summary() for item in self._repository._dnc.records if item.scope == scope
            ],
            "retention_intents": [item.safe_summary() for item in retention],
        }
        csv_payloads = {
            "organizations": _csv(
                ("organization_ref", "stage", "source_policy_id"),
                (
                    (
                        item.organization_ref,
                        _stage_for_organization(item.organization_ref, opportunities),
                        item.source_policy_id,
                    )
                    for item in organizations
                ),
            ),
            "contacts": _csv(
                ("contact_ref", "organization_ref", "source_evidence_ref", "consent_granted"),
                (
                    (
                        item.contact_ref,
                        item.organization_ref,
                        item.source_evidence_ref,
                        str(item.consent_granted).lower(),
                    )
                    for item in contacts
                ),
            ),
            "opportunities": _csv(
                ("opportunity_ref", "organization_ref", "stage", "amount_state"),
                (
                    (
                        item.opportunity_ref,
                        item.organization_ref,
                        item.stage.value,
                        item.amount_state,
                    )
                    for item in opportunities
                ),
            ),
            "interactions": _csv(
                ("interaction_ref", "organization_ref", "kind", "sent_count"),
                (
                    (
                        item.interaction_ref,
                        item.organization_ref,
                        item.kind.value,
                        str(item.sent_count),
                    )
                    for item in interactions
                ),
            ),
            "dnc_records": _csv(
                ("dnc_ref", "subject_hash", "reason_code"),
                ((item.dnc_ref, item.subject_hash, item.reason_code) for item in self._repository._dnc.records if item.scope == scope),
            ),
            "retention_intents": _csv(
                ("retention_ref", "subject_ref", "intent"),
                ((item.retention_ref, item.subject_ref, item.intent) for item in retention),
            ),
        }
        _assert_no_provider_keys(json_payload, csv_payloads)
        _record_audit(
            self._audit_log,
            event_kind="crm_export_created",
            scope=scope,
            command_ref="crm.export_scope",
            target_ref=export_ref,
            policy_version="p05_02_crm_domain",
            result_code="export_created",
            actor_ref=requester,
            metadata={
                "organization_count": len(organizations),
                "party_count": len(contacts),
                "opportunity_count": len(opportunities),
                "interaction_count": len(interactions),
                "retention_count": len(retention),
            },
        )
        return CrmExport(
            export_ref=export_ref,
            json_payload=json_payload,
            csv_payloads=csv_payloads,
        )


def _digest(*parts: object) -> str:
    return sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _csv(headers: tuple[str, ...], rows: object) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def _stage_for_organization(organization_ref: str, opportunities: list[Opportunity]) -> str:
    for opportunity in opportunities:
        if opportunity.organization_ref == organization_ref:
            return opportunity.stage.value
    return CrmStage.MANUAL_REVIEW.value


def _assert_no_provider_keys(json_payload: Mapping[str, object], csv_payloads: Mapping[str, str]) -> None:
    rendered_json = str(_walk_keys(json_payload)).lower()
    rendered_csv = "\n".join(csv_payloads.values()).lower()
    if "provider:" in rendered_json or "external_provider_id" in rendered_json:
        raise _boundary("provider_id_key_forbidden")
    if "provider:" in rendered_csv or "external_provider_id" in rendered_csv:
        raise _boundary("provider_id_key_forbidden")


def _walk_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_keys(item))
    return tuple(keys)


__all__ = [
    "Contact",
    "CrmBoundaryError",
    "CrmExport",
    "CrmExportService",
    "CrmRecordSet",
    "CrmRepository",
    "CrmStage",
    "DncRecord",
    "DncRegistry",
    "Interaction",
    "InteractionKind",
    "LeadReviewDecision",
    "Opportunity",
    "Organization",
    "RetentionIntent",
    "SyntheticLeadCandidate",
]
