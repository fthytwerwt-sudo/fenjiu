"""P05-03 internal outreach draft and zero-send contracts.

This module creates editable internal drafts from reviewed synthetic CRM
entities and fresh approved synthetic fact references. It intentionally has no
sender port, provider endpoint, or external recipient surface.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256

from core.contracts import DataState, ScopeRef
from core.contracts.leads_crm import (
    require_hash,
    require_identifier,
    require_scope,
    require_time,
    stable_ref,
)
from modules.crm.domain import CrmBoundaryError, CrmRepository, DncRegistry, InteractionKind


class OutreachFactStatus(str, Enum):
    APPROVED = "approved"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    CONFLICT = "conflict"


class OutreachRisk(str, Enum):
    LOW = "low"
    HIGH = "high"


class OutreachDraftState(str, Enum):
    DRAFT_ONLY = "draft_only"
    APPROVED_INTERNAL = "approved_internal"
    INVALIDATED = "invalidated"


class OutreachBoundaryError(CrmBoundaryError):
    """Stable, value-free P05-03 outreach boundary error."""


def _boundary(code: str) -> OutreachBoundaryError:
    return OutreachBoundaryError(code)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _scope_key(scope: ScopeRef) -> tuple[object, object, object]:
    return (scope.tenant_id, scope.project_id, scope.business_line_id)


def _digest(*parts: object) -> str:
    return sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()


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
    actor_ref: str,
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
class OutreachFactRef:
    scope: ScopeRef
    fact_ref: str
    version_ref: str
    fact_type: str
    subject_ref: str
    target_field: str
    version_no: int
    observed_at: datetime
    expires_at: datetime
    evidence_refs: tuple[str, ...]
    policy_version: str
    status: OutreachFactStatus
    data_state: DataState
    is_synthetic: bool
    external_execution_allowed: bool
    business_external_ready: bool

    def __post_init__(self) -> None:
        require_scope(self.scope)
        for value, code in (
            (self.fact_ref, "fact_ref_required"),
            (self.version_ref, "fact_version_required"),
            (self.fact_type, "fact_type_required"),
            (self.subject_ref, "fact_subject_required"),
            (self.target_field, "target_field_required"),
            (self.policy_version, "fact_policy_version_required"),
        ):
            require_identifier(value, code)
        if not isinstance(self.version_no, int) or isinstance(self.version_no, bool) or self.version_no < 1:
            raise _boundary("fact_version_required")
        observed = require_time(self.observed_at, "fact_observed_at_required")
        expires = require_time(self.expires_at, "fact_expires_at_required")
        if expires <= observed:
            raise _boundary("fact_stale")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise _boundary("approved_fact_required")
        for evidence_ref in self.evidence_refs:
            require_identifier(evidence_ref, "approved_fact_required")
        if not isinstance(self.status, OutreachFactStatus):
            raise _boundary("fact_status_required")
        if (
            self.data_state is not DataState.FIXTURE
            or self.is_synthetic is not True
            or self.external_execution_allowed is not False
            or self.business_external_ready is not False
        ):
            raise _boundary("approved_synthetic_fact_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "fact_ref": self.fact_ref,
            "version_ref": self.version_ref,
            "fact_type": self.fact_type,
            "subject_ref": self.subject_ref,
            "target_field": self.target_field,
            "version_no": self.version_no,
            "evidence_refs": self.evidence_refs,
            "policy_version": self.policy_version,
            "status": self.status.value,
            "data_state": self.data_state.value,
            "is_synthetic": True,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


@dataclass(frozen=True)
class OutreachFactLock:
    fact_ref: str
    version_ref: str
    fact_type: str
    target_field: str
    version_no: int
    evidence_refs: tuple[str, ...]
    policy_version: str

    @classmethod
    def from_fact(cls, fact: OutreachFactRef) -> "OutreachFactLock":
        return cls(
            fact_ref=fact.fact_ref,
            version_ref=fact.version_ref,
            fact_type=fact.fact_type,
            target_field=fact.target_field,
            version_no=fact.version_no,
            evidence_refs=fact.evidence_refs,
            policy_version=fact.policy_version,
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "fact_ref": self.fact_ref,
            "version_ref": self.version_ref,
            "fact_type": self.fact_type,
            "target_field": self.target_field,
            "version_no": self.version_no,
            "evidence_refs": self.evidence_refs,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True)
class OutreachZeroSendProof:
    external_send_attempts: int
    external_execution_allowed: bool
    send_port_present: bool
    provider_endpoint_present: bool
    external_recipient_present: bool

    def __post_init__(self) -> None:
        if self.external_send_attempts != 0:
            raise _boundary("external_send_forbidden")
        if self.external_execution_allowed is not False:
            raise _boundary("external_execution_forbidden")
        if (
            self.send_port_present is not False
            or self.provider_endpoint_present is not False
            or self.external_recipient_present is not False
        ):
            raise _boundary("external_send_surface_forbidden")

    def safe_summary(self) -> dict[str, object]:
        return {
            "external_send_attempts": 0,
            "external_execution_allowed": False,
            "send_port_present": False,
            "provider_endpoint_present": False,
            "external_recipient_present": False,
        }


@dataclass(frozen=True)
class OutreachDraftCommand:
    scope: ScopeRef
    organization_ref: str
    subject_hash: str
    template_ref: str
    template_version: str
    fact_refs: tuple[OutreachFactRef, ...]
    policy_version: str
    consent_evidence_ref: str | None
    requested_by: str
    risk_level: OutreachRisk
    idempotency_key: str

    def __post_init__(self) -> None:
        require_scope(self.scope)
        require_identifier(self.organization_ref, "organization_ref_required")
        require_hash(self.subject_hash, "outreach_subject_required")
        require_identifier(self.template_ref, "template_ref_required")
        require_identifier(self.template_version, "template_version_required")
        if not isinstance(self.fact_refs, tuple):
            raise _boundary("approved_fact_required")
        for fact in self.fact_refs:
            if not isinstance(fact, OutreachFactRef):
                raise _boundary("approved_fact_required")
        require_identifier(self.policy_version, "policy_version_required")
        if self.consent_evidence_ref is not None:
            require_identifier(self.consent_evidence_ref, "consent_evidence_required")
        require_identifier(self.requested_by, "actor_ref_required")
        if not isinstance(self.risk_level, OutreachRisk):
            raise _boundary("risk_level_required")
        require_identifier(self.idempotency_key, "idempotency_key_required")


@dataclass(frozen=True)
class OutreachManualHandoff:
    handoff_ref: str
    scope: ScopeRef
    organization_ref: str
    reason_code: str
    policy_version: str
    requested_by: str
    created_at: datetime
    external_send_attempts: int = 0
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        require_identifier(self.handoff_ref, "handoff_ref_required")
        require_scope(self.scope)
        require_identifier(self.organization_ref, "organization_ref_required")
        require_identifier(self.reason_code, "handoff_reason_required")
        require_identifier(self.policy_version, "policy_version_required")
        require_identifier(self.requested_by, "actor_ref_required")
        require_time(self.created_at, "created_at_required")
        if self.external_send_attempts != 0 or self.external_execution_allowed is not False:
            raise _boundary("external_send_forbidden")

    def safe_summary(self) -> dict[str, object]:
        return {
            "handoff_ref": self.handoff_ref,
            "organization_ref": self.organization_ref,
            "reason_code": self.reason_code,
            "policy_version": self.policy_version,
            "requested_by": self.requested_by,
            "created_at": self.created_at.isoformat(),
            "external_send_attempts": 0,
            "external_execution_allowed": False,
        }


@dataclass(frozen=True)
class OutreachDraft:
    scope: ScopeRef
    draft_ref: str
    organization_ref: str
    interaction_ref: str
    subject_hash: str
    template_ref: str
    template_version: str
    fact_locks: tuple[OutreachFactLock, ...]
    body_blocks: tuple[str, ...]
    policy_version: str
    policy_fingerprint: str
    state: OutreachDraftState
    editable_by_human: bool
    evidence_refs: tuple[str, ...]
    fact_observed_at: datetime
    fact_expires_at: datetime
    subject_version: int
    created_at: datetime
    requested_by: str
    approval_request_ref: str | None = None
    approval_decision_ref: str | None = None
    invalidation_reason: str | None = None
    external_send_attempts: int = 0
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        require_scope(self.scope)
        for value, code in (
            (self.draft_ref, "draft_ref_required"),
            (self.organization_ref, "organization_ref_required"),
            (self.interaction_ref, "interaction_ref_required"),
            (self.template_ref, "template_ref_required"),
            (self.template_version, "template_version_required"),
            (self.policy_version, "policy_version_required"),
            (self.policy_fingerprint, "policy_fingerprint_required"),
            (self.requested_by, "actor_ref_required"),
        ):
            require_identifier(value, code)
        require_hash(self.subject_hash, "outreach_subject_required")
        if not self.fact_locks:
            raise _boundary("approved_fact_required")
        if not self.body_blocks:
            raise _boundary("draft_body_required")
        for block in self.body_blocks:
            require_identifier(block, "draft_body_required")
        if not isinstance(self.state, OutreachDraftState):
            raise _boundary("draft_state_required")
        if self.editable_by_human is not True:
            raise _boundary("human_edit_required")
        if not self.evidence_refs:
            raise _boundary("approved_fact_required")
        for evidence_ref in self.evidence_refs:
            require_identifier(evidence_ref, "approved_fact_required")
        require_time(self.fact_observed_at, "fact_observed_at_required")
        require_time(self.fact_expires_at, "fact_expires_at_required")
        if self.fact_expires_at <= self.fact_observed_at:
            raise _boundary("fact_stale")
        if not isinstance(self.subject_version, int) or isinstance(self.subject_version, bool) or self.subject_version < 1:
            raise _boundary("subject_version_required")
        require_time(self.created_at, "created_at_required")
        if self.approval_request_ref is not None:
            require_identifier(self.approval_request_ref, "approval_request_id_required")
        if self.approval_decision_ref is not None:
            require_identifier(self.approval_decision_ref, "approval_decision_id_required")
        if self.invalidation_reason is not None:
            require_identifier(self.invalidation_reason, "invalidation_reason_required")
        if self.external_send_attempts != 0 or self.external_execution_allowed is not False:
            raise _boundary("external_send_forbidden")

    def safe_summary(self) -> dict[str, object]:
        return {
            "draft_ref": self.draft_ref,
            "organization_ref": self.organization_ref,
            "interaction_ref": self.interaction_ref,
            "template_ref": self.template_ref,
            "template_version": self.template_version,
            "fact_locks": [item.safe_summary() for item in self.fact_locks],
            "body_blocks": self.body_blocks,
            "policy_version": self.policy_version,
            "state": self.state.value,
            "editable_by_human": True,
            "subject_version": self.subject_version,
            "created_at": self.created_at.isoformat(),
            "approval_request_ref": self.approval_request_ref,
            "approval_decision_ref": self.approval_decision_ref,
            "invalidation_reason": self.invalidation_reason,
            "external_send_attempts": 0,
            "external_execution_allowed": False,
        }


@dataclass(frozen=True)
class OutreachDraftReceipt:
    draft: OutreachDraft | None
    manual_handoff: OutreachManualHandoff | None
    zero_send_proof: OutreachZeroSendProof

    def __post_init__(self) -> None:
        if (self.draft is None) == (self.manual_handoff is None):
            raise _boundary("draft_or_handoff_required")
        if not isinstance(self.zero_send_proof, OutreachZeroSendProof):
            raise _boundary("zero_send_proof_required")


class OutreachDraftService:
    """Draft-only CRM outreach workflow with fail-closed manual handoff."""

    __slots__ = (
        "_audit_log",
        "_crm",
        "_dnc",
        "_draft_by_idempotency",
        "_fingerprint_by_idempotency",
        "_handoff_by_idempotency",
        "_now",
    )

    def __init__(
        self,
        *,
        crm_repository: CrmRepository,
        dnc_registry: DncRegistry,
        audit_log: object,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._crm = crm_repository
        self._dnc = dnc_registry
        self._audit_log = audit_log
        self._now = now or _now_utc
        self._draft_by_idempotency: dict[str, OutreachDraft] = {}
        self._handoff_by_idempotency: dict[str, OutreachManualHandoff] = {}
        self._fingerprint_by_idempotency: dict[str, str] = {}

    def prepare_draft(self, command: OutreachDraftCommand) -> OutreachDraftReceipt:
        if not isinstance(command, OutreachDraftCommand):
            raise _boundary("outreach_command_required")
        proof = self.zero_send_proof()
        fingerprint = self._command_fingerprint(command)
        existing_draft = self._draft_by_idempotency.get(command.idempotency_key)
        if existing_draft is not None:
            self._assert_idempotent(command.idempotency_key, fingerprint)
            return OutreachDraftReceipt(draft=existing_draft, manual_handoff=None, zero_send_proof=proof)
        existing_handoff = self._handoff_by_idempotency.get(command.idempotency_key)
        if existing_handoff is not None:
            self._assert_idempotent(command.idempotency_key, fingerprint)
            return OutreachDraftReceipt(draft=None, manual_handoff=existing_handoff, zero_send_proof=proof)

        prepared_at = self._now()
        organization = self._organization(command.organization_ref)
        reason = self._manual_handoff_reason(command, prepared_at)
        if reason is not None:
            handoff = self._manual_handoff(command, reason, prepared_at)
            self._handoff_by_idempotency[command.idempotency_key] = handoff
            self._fingerprint_by_idempotency[command.idempotency_key] = fingerprint
            return OutreachDraftReceipt(draft=None, manual_handoff=handoff, zero_send_proof=proof)

        interaction = self._crm.create_interaction(
            organization.organization_ref,
            interaction_ref=stable_ref("outreach_interaction", command.scope, command.idempotency_key),
            kind=InteractionKind.DRAFT,
            subject_hash=command.subject_hash,
            prompt_instruction=None,
            idempotency_key="outreach_interaction:" + command.idempotency_key,
        )
        fact_locks = tuple(OutreachFactLock.from_fact(fact) for fact in command.fact_refs)
        evidence_refs = tuple(dict.fromkeys(ref for fact in command.fact_refs for ref in fact.evidence_refs))
        fact_observed_at = min(fact.observed_at for fact in command.fact_refs)
        fact_expires_at = min(fact.expires_at for fact in command.fact_refs)
        subject_version = max(fact.version_no for fact in command.fact_refs)
        draft = OutreachDraft(
            scope=command.scope,
            draft_ref=stable_ref("outreach_draft", command.scope, command.idempotency_key),
            organization_ref=organization.organization_ref,
            interaction_ref=interaction.interaction_ref,
            subject_hash=command.subject_hash,
            template_ref=command.template_ref,
            template_version=command.template_version,
            fact_locks=fact_locks,
            body_blocks=(
                "human_edit_required",
                "approved_fact_lock_bound",
                "commercial_terms_confirmation_required",
                "inventory_confirmation_required",
            ),
            policy_version=command.policy_version,
            policy_fingerprint=_digest(command.policy_version, command.template_ref, command.template_version),
            state=OutreachDraftState.DRAFT_ONLY,
            editable_by_human=True,
            evidence_refs=evidence_refs,
            fact_observed_at=fact_observed_at,
            fact_expires_at=fact_expires_at,
            subject_version=subject_version,
            created_at=prepared_at,
            requested_by=command.requested_by,
        )
        self._draft_by_idempotency[command.idempotency_key] = draft
        self._fingerprint_by_idempotency[command.idempotency_key] = fingerprint
        _record_audit(
            self._audit_log,
            event_kind="outreach_draft_created",
            scope=command.scope,
            command_ref="crm.outreach.prepare_draft",
            target_ref=draft.draft_ref,
            policy_version=command.policy_version,
            result_code="draft_created",
            actor_ref=command.requested_by,
            subject_version=subject_version,
            metadata={"item_count": len(fact_locks), "reason_code": "draft_only"},
        )
        return OutreachDraftReceipt(draft=draft, manual_handoff=None, zero_send_proof=proof)

    def invalidate_on_fact_change(
        self,
        draft: OutreachDraft,
        *,
        invalidated_version_refs: tuple[str, ...],
        current_policy_version: str,
    ) -> OutreachDraft:
        if not isinstance(draft, OutreachDraft):
            raise _boundary("draft_required")
        require_identifier(current_policy_version, "policy_version_required")
        if current_policy_version != draft.policy_version:
            return replace(
                draft,
                state=OutreachDraftState.INVALIDATED,
                invalidation_reason="policy_version_changed",
            )
        locked_versions = {lock.version_ref for lock in draft.fact_locks}
        for version_ref in invalidated_version_refs:
            require_identifier(version_ref, "fact_version_required")
        if locked_versions.intersection(invalidated_version_refs):
            return replace(
                draft,
                state=OutreachDraftState.INVALIDATED,
                invalidation_reason="fact_version_invalidated",
            )
        return draft

    def zero_send_proof(self) -> OutreachZeroSendProof:
        return OutreachZeroSendProof(
            external_send_attempts=0,
            external_execution_allowed=False,
            send_port_present=False,
            provider_endpoint_present=False,
            external_recipient_present=False,
        )

    def _manual_handoff_reason(self, command: OutreachDraftCommand, now: datetime) -> str | None:
        organization = self._organization(command.organization_ref)
        if organization.scope != command.scope:
            return "cross_scope_forbidden"
        if command.risk_level is OutreachRisk.HIGH:
            return "manual_review_required"
        if command.consent_evidence_ref is None:
            return "consent_required"
        if self._dnc.is_blocked(command.scope, command.subject_hash):
            return "dnc_blocked"
        if not command.fact_refs:
            return "approved_fact_required"
        for fact in command.fact_refs:
            if fact.scope != command.scope:
                return "cross_scope_forbidden"
            if fact.status is not OutreachFactStatus.APPROVED:
                return "fact_not_approved"
            if (
                fact.data_state is not DataState.FIXTURE
                or fact.is_synthetic is not True
                or fact.external_execution_allowed is not False
                or fact.business_external_ready is not False
            ):
                return "approved_synthetic_fact_required"
            if fact.expires_at <= now:
                return "fact_stale"
        return None

    def _manual_handoff(
        self,
        command: OutreachDraftCommand,
        reason_code: str,
        created_at: datetime,
    ) -> OutreachManualHandoff:
        handoff = OutreachManualHandoff(
            handoff_ref=stable_ref("outreach_handoff", command.scope, command.idempotency_key, reason_code),
            scope=command.scope,
            organization_ref=command.organization_ref,
            reason_code=reason_code,
            policy_version=command.policy_version,
            requested_by=command.requested_by,
            created_at=created_at,
        )
        _record_audit(
            self._audit_log,
            event_kind="outreach_manual_handoff_created",
            scope=command.scope,
            command_ref="crm.outreach.manual_handoff",
            target_ref=handoff.handoff_ref,
            policy_version=command.policy_version,
            result_code=reason_code,
            actor_ref=command.requested_by,
            metadata={"reason_code": reason_code},
        )
        return handoff

    def _organization(self, organization_ref: str):
        ref = require_identifier(organization_ref, "organization_ref_required")
        for organization in self._crm.organizations:
            if organization.organization_ref == ref:
                return organization
        raise _boundary("organization_required")

    def _command_fingerprint(self, command: OutreachDraftCommand) -> str:
        return _digest(
            _scope_key(command.scope),
            command.organization_ref,
            command.subject_hash,
            command.template_ref,
            command.template_version,
            tuple(fact.safe_summary() for fact in command.fact_refs),
            command.policy_version,
            command.consent_evidence_ref,
            command.requested_by,
            command.risk_level.value,
        )

    def _assert_idempotent(self, idempotency_key: str, fingerprint: str) -> None:
        if self._fingerprint_by_idempotency.get(idempotency_key) != fingerprint:
            raise _boundary("idempotency_conflict")


__all__ = [
    "OutreachBoundaryError",
    "OutreachDraft",
    "OutreachDraftCommand",
    "OutreachDraftReceipt",
    "OutreachDraftService",
    "OutreachDraftState",
    "OutreachFactLock",
    "OutreachFactRef",
    "OutreachFactStatus",
    "OutreachManualHandoff",
    "OutreachRisk",
    "OutreachZeroSendProof",
]
