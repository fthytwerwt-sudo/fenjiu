"""P06-03 human takeover state and zero-send case contracts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import re
from typing import Callable
from uuid import UUID

from core.contracts import ContractValidationError, ScopeRef
from modules.customer_service.contracts import ConversationReceipt, SupportDisposition
from modules.customer_service.drafts import DraftDisposition, DraftOutcome


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)


class SupportTakeoverBoundaryError(ContractValidationError):
    """Stable, value-free P06-03 takeover boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class SupportCaseState(str, Enum):
    DRAFT_ONLY = "draft_only"
    MANUAL_HANDOFF = "manual_handoff"
    HUMAN_APPROVED_INTERNAL = "human_approved_internal"
    HUMAN_REJECTED = "human_rejected"
    HUMAN_REVISED = "human_revised"
    RESUMED_INTERNAL = "resumed_internal"
    INVALIDATED = "invalidated"


class HumanDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"
    RESUME = "resume"


def _boundary(code: str) -> SupportTakeoverBoundaryError:
    return SupportTakeoverBoundaryError(code)


def _digest(*parts: object) -> str:
    return sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _stable_ref(kind: str, *parts: object) -> str:
    digest = _digest(kind, *parts)[:32]
    return f"{kind}:{digest}"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _reject_sensitive_text(value: object) -> None:
    if not isinstance(value, str):
        return
    local_user_root = "/" + "Users" + "/"
    local_volume_root = "/" + "Volumes" + "/"
    if value.startswith("/") or "\\" in value or local_user_root in value or local_volume_root in value:
        raise _boundary("support_payload_forbidden")
    if _SENSITIVE.search(value) is not None:
        raise _boundary("support_payload_forbidden")


def _require_identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _boundary(code)
    _reject_sensitive_text(value)
    return value


def _require_hash(value: object, code: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise _boundary(code)
    return value


def _require_uuid(value: object, code: str) -> UUID:
    if not isinstance(value, UUID) or value.int == 0:
        raise _boundary(code)
    return value


def _require_scope(value: object) -> ScopeRef:
    if not isinstance(value, ScopeRef):
        raise _boundary("scope_required")
    _require_identifier(value.correlation_id, "correlation_id_required")
    return value


def _require_time(value: object, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _boundary(code)
    return value


@dataclass(frozen=True)
class SupportZeroSendProof:
    external_send_attempts: int
    external_execution_allowed: bool
    send_approved_present: bool
    provider_endpoint_present: bool

    def __post_init__(self) -> None:
        if self.external_send_attempts != 0:
            raise _boundary("external_send_forbidden")
        if self.external_execution_allowed is not False:
            raise _boundary("external_execution_forbidden")
        if self.send_approved_present is not False or self.provider_endpoint_present is not False:
            raise _boundary("external_send_surface_forbidden")

    def safe_summary(self) -> dict[str, object]:
        return {
            "external_send_attempts": 0,
            "external_execution_allowed": False,
            "send_approved_present": False,
            "provider_endpoint_present": False,
        }


@dataclass(frozen=True)
class SupportReviewCase:
    case_ref: str
    scope: ScopeRef
    conversation_id: UUID
    message_id: UUID
    intake_disposition: str
    state: SupportCaseState
    policy_version: str
    policy_snapshot_hash: str
    fact_version_set_hash: str | None
    fact_version_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    subject_version: int
    created_at: datetime
    created_by: str
    automation_paused: bool
    draft_ref: str | None = None
    handoff_reason_code: str | None = None
    approval_request_ref: str | None = None
    approval_decision_ref: str | None = None
    revision_ref: str | None = None
    invalidation_reason: str | None = None
    external_send_attempts: int = 0
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.case_ref, "support_case_ref_required")
        _require_scope(self.scope)
        _require_uuid(self.conversation_id, "conversation_id_required")
        _require_uuid(self.message_id, "message_id_required")
        _require_identifier(self.intake_disposition, "intake_disposition_required")
        if not isinstance(self.state, SupportCaseState):
            raise _boundary("support_case_state_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_hash(self.policy_snapshot_hash, "policy_snapshot_hash_required")
        if self.fact_version_set_hash is not None:
            _require_hash(self.fact_version_set_hash, "fact_version_set_hash_required")
        if not isinstance(self.fact_version_ids, tuple):
            raise _boundary("fact_version_required")
        for version_id in self.fact_version_ids:
            _require_identifier(version_id, "fact_version_required")
        if not isinstance(self.evidence_refs, tuple):
            raise _boundary("evidence_ref_required")
        for evidence_ref in self.evidence_refs:
            _require_identifier(evidence_ref, "evidence_ref_required")
        if not isinstance(self.subject_version, int) or isinstance(self.subject_version, bool) or self.subject_version < 1:
            raise _boundary("subject_version_required")
        _require_time(self.created_at, "created_at_required")
        _require_identifier(self.created_by, "actor_ref_required")
        if not isinstance(self.automation_paused, bool):
            raise _boundary("automation_state_required")
        if self.draft_ref is not None:
            _require_identifier(self.draft_ref, "draft_ref_required")
        if self.handoff_reason_code is not None:
            _require_identifier(self.handoff_reason_code, "handoff_reason_required")
        if self.approval_request_ref is not None:
            _require_identifier(self.approval_request_ref, "approval_request_id_required")
        if self.approval_decision_ref is not None:
            _require_identifier(self.approval_decision_ref, "approval_decision_id_required")
        if self.revision_ref is not None:
            _require_identifier(self.revision_ref, "revision_ref_required")
        if self.invalidation_reason is not None:
            _require_identifier(self.invalidation_reason, "invalidation_reason_required")
        if self.external_send_attempts != 0 or self.external_execution_allowed is not False:
            raise _boundary("external_send_forbidden")
        if self.state is SupportCaseState.DRAFT_ONLY and self.draft_ref is None:
            raise _boundary("draft_ref_required")
        if self.state is SupportCaseState.MANUAL_HANDOFF and self.handoff_reason_code is None:
            raise _boundary("handoff_reason_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "case_ref": self.case_ref,
            "conversation_id": str(self.conversation_id),
            "message_id": str(self.message_id),
            "intake_disposition": self.intake_disposition,
            "state": self.state.value,
            "policy_version": self.policy_version,
            "policy_snapshot_hash": self.policy_snapshot_hash,
            "fact_version_set_hash": self.fact_version_set_hash,
            "fact_version_ids": self.fact_version_ids,
            "evidence_refs": self.evidence_refs,
            "subject_version": self.subject_version,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "automation_paused": self.automation_paused,
            "draft_ref": self.draft_ref,
            "handoff_reason_code": self.handoff_reason_code,
            "approval_request_ref": self.approval_request_ref,
            "approval_decision_ref": self.approval_decision_ref,
            "revision_ref": self.revision_ref,
            "invalidation_reason": self.invalidation_reason,
            "external_send_attempts": 0,
            "external_execution_allowed": False,
        }


@dataclass(frozen=True)
class SupportHumanDecisionRecord:
    decision_ref: str
    case_ref: str
    action: HumanDecision
    actor_ref: str
    evidence_ref: str
    result_state: SupportCaseState
    created_at: datetime
    revision_ref: str | None = None
    external_send_attempts: int = 0
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.decision_ref, "support_decision_ref_required")
        _require_identifier(self.case_ref, "support_case_ref_required")
        if not isinstance(self.action, HumanDecision):
            raise _boundary("human_decision_required")
        _require_identifier(self.actor_ref, "actor_ref_required")
        _require_identifier(self.evidence_ref, "evidence_ref_required")
        if not isinstance(self.result_state, SupportCaseState):
            raise _boundary("support_case_state_required")
        _require_time(self.created_at, "created_at_required")
        if self.revision_ref is not None:
            _require_identifier(self.revision_ref, "revision_ref_required")
        if self.external_send_attempts != 0 or self.external_execution_allowed is not False:
            raise _boundary("external_send_forbidden")


@dataclass(frozen=True)
class SupportCaseReceipt:
    case: SupportReviewCase
    zero_send_proof: SupportZeroSendProof
    replayed: bool = False

    def safe_summary(self) -> dict[str, object]:
        return {
            "case": self.case.safe_summary(),
            "zero_send_proof": self.zero_send_proof.safe_summary(),
            "replayed": self.replayed,
        }


class SupportCaseQueue:
    """Append-only synthetic case queue for draft-only review and handoff."""

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or _now_utc
        self._cases_by_ref: dict[str, SupportReviewCase] = {}
        self._case_ref_by_fingerprint: dict[str, str] = {}
        self._decisions_by_key: dict[str, SupportHumanDecisionRecord] = {}

    @property
    def cases(self) -> tuple[SupportReviewCase, ...]:
        return tuple(self._cases_by_ref.values())

    @property
    def decisions(self) -> tuple[SupportHumanDecisionRecord, ...]:
        return tuple(self._decisions_by_key.values())

    def zero_send_proof(self) -> SupportZeroSendProof:
        return SupportZeroSendProof(
            external_send_attempts=0,
            external_execution_allowed=False,
            send_approved_present=False,
            provider_endpoint_present=False,
        )

    def open_case(
        self,
        receipt: ConversationReceipt,
        outcome: DraftOutcome,
        *,
        actor_ref: str,
    ) -> SupportCaseReceipt:
        if not isinstance(receipt, ConversationReceipt):
            raise _boundary("conversation_receipt_required")
        if not isinstance(outcome, DraftOutcome):
            raise _boundary("draft_outcome_required")
        actor = _require_identifier(actor_ref, "actor_ref_required")
        if receipt.conversation is None or receipt.message is None:
            raise _boundary("scoped_conversation_required")
        fingerprint = self._case_fingerprint(receipt, outcome)
        existing_ref = self._case_ref_by_fingerprint.get(fingerprint)
        if existing_ref is not None:
            return SupportCaseReceipt(
                case=self._cases_by_ref[existing_ref],
                zero_send_proof=self.zero_send_proof(),
                replayed=True,
            )
        case = self._build_case(receipt, outcome, actor_ref=actor, fingerprint=fingerprint)
        if case.case_ref in self._cases_by_ref:
            raise _boundary("idempotency_conflict")
        self._cases_by_ref[case.case_ref] = case
        self._case_ref_by_fingerprint[fingerprint] = case.case_ref
        return SupportCaseReceipt(case=case, zero_send_proof=self.zero_send_proof())

    def apply_decision(
        self,
        case_ref: str,
        *,
        action: HumanDecision,
        actor_ref: str,
        evidence_ref: str,
        idempotency_key: str,
        revision_ref: str | None = None,
        approval_request_ref: str | None = None,
        approval_decision_ref: str | None = None,
    ) -> SupportReviewCase:
        case = self._case(case_ref)
        key = _require_identifier(idempotency_key, "idempotency_key_required")
        if not isinstance(action, HumanDecision):
            raise _boundary("human_decision_required")
        actor = _require_identifier(actor_ref, "actor_ref_required")
        evidence = _require_identifier(evidence_ref, "evidence_ref_required")
        if action is HumanDecision.REVISE and revision_ref is None:
            raise _boundary("revision_ref_required")
        if revision_ref is not None:
            _require_identifier(revision_ref, "revision_ref_required")
        existing = self._decisions_by_key.get(key)
        if existing is not None:
            if (
                existing.case_ref != case.case_ref
                or existing.action is not action
                or existing.actor_ref != actor
                or existing.evidence_ref != evidence
                or existing.revision_ref != revision_ref
            ):
                raise _boundary("idempotency_conflict")
            return self._cases_by_ref[case.case_ref]
        allowed_states = {
            HumanDecision.APPROVE: frozenset({SupportCaseState.DRAFT_ONLY, SupportCaseState.HUMAN_REVISED}),
            HumanDecision.REJECT: frozenset(
                {
                    SupportCaseState.DRAFT_ONLY,
                    SupportCaseState.HUMAN_REVISED,
                    SupportCaseState.MANUAL_HANDOFF,
                    SupportCaseState.HUMAN_APPROVED_INTERNAL,
                }
            ),
            HumanDecision.REVISE: frozenset(
                {SupportCaseState.DRAFT_ONLY, SupportCaseState.HUMAN_REVISED, SupportCaseState.MANUAL_HANDOFF}
            ),
            HumanDecision.RESUME: frozenset(),
        }
        if case.state not in allowed_states[action]:
            raise _boundary("support_case_state_required")
        if action is HumanDecision.APPROVE and case.draft_ref is None:
            raise _boundary("draft_ref_required")
        next_state = {
            HumanDecision.APPROVE: SupportCaseState.HUMAN_APPROVED_INTERNAL,
            HumanDecision.REJECT: SupportCaseState.HUMAN_REJECTED,
            HumanDecision.REVISE: SupportCaseState.HUMAN_REVISED,
        }[action]
        updated = replace(
            case,
            state=next_state,
            approval_request_ref=approval_request_ref or case.approval_request_ref,
            approval_decision_ref=approval_decision_ref or case.approval_decision_ref,
            revision_ref=revision_ref or case.revision_ref,
            automation_paused=True,
        )
        decision = SupportHumanDecisionRecord(
            decision_ref=_stable_ref("support_decision", case.case_ref, key),
            case_ref=case.case_ref,
            action=action,
            actor_ref=actor,
            evidence_ref=evidence,
            revision_ref=revision_ref,
            result_state=next_state,
            created_at=self._now(),
        )
        self._decisions_by_key[key] = decision
        self._cases_by_ref[case.case_ref] = updated
        return updated

    def resume_case(
        self,
        case_ref: str,
        *,
        actor_ref: str,
        evidence_ref: str,
        idempotency_key: str,
    ) -> SupportReviewCase:
        case = self._case(case_ref)
        key = _require_identifier(idempotency_key, "idempotency_key_required")
        actor = _require_identifier(actor_ref, "actor_ref_required")
        evidence = _require_identifier(evidence_ref, "evidence_ref_required")
        existing = self._decisions_by_key.get(key)
        if existing is not None:
            if existing.case_ref != case.case_ref or existing.actor_ref != actor or existing.evidence_ref != evidence:
                raise _boundary("idempotency_conflict")
            return self._cases_by_ref[case.case_ref]
        if case.state not in {
            SupportCaseState.HUMAN_APPROVED_INTERNAL,
            SupportCaseState.HUMAN_REVISED,
            SupportCaseState.MANUAL_HANDOFF,
        }:
            raise _boundary("resume_state_required")
        updated = replace(
            case,
            state=SupportCaseState.RESUMED_INTERNAL,
            automation_paused=True,
        )
        self._decisions_by_key[key] = SupportHumanDecisionRecord(
            decision_ref=_stable_ref("support_decision", case.case_ref, key),
            case_ref=case.case_ref,
            action=HumanDecision.RESUME,
            actor_ref=actor,
            evidence_ref=evidence,
            result_state=SupportCaseState.RESUMED_INTERNAL,
            created_at=self._now(),
        )
        self._cases_by_ref[case.case_ref] = updated
        return updated

    def invalidate_on_fact_change(
        self,
        case_ref: str,
        *,
        invalidated_version_ids: tuple[str, ...],
        current_policy_version: str,
    ) -> SupportReviewCase:
        case = self._case(case_ref)
        _require_identifier(current_policy_version, "policy_version_required")
        for version_id in invalidated_version_ids:
            _require_identifier(version_id, "fact_version_required")
        reason: str | None = None
        if current_policy_version != case.policy_version:
            reason = "policy_version_changed"
        elif set(case.fact_version_ids).intersection(invalidated_version_ids):
            reason = "fact_version_invalidated"
        if reason is None:
            return case
        updated = replace(
            case,
            state=SupportCaseState.INVALIDATED,
            invalidation_reason=reason,
            automation_paused=True,
        )
        self._cases_by_ref[case.case_ref] = updated
        return updated

    def _case_fingerprint(self, receipt: ConversationReceipt, outcome: DraftOutcome) -> str:
        assert receipt.conversation is not None
        assert receipt.message is not None
        parts: list[object] = [
            "support_case_fingerprint",
            receipt.conversation.id,
            receipt.message.id,
            receipt.disposition.value,
            outcome.disposition.value,
        ]
        if outcome.disposition is DraftDisposition.DRAFT_READY and outcome.draft is not None:
            parts.extend(
                (
                    outcome.draft.draft_ref,
                    outcome.draft.policy_version,
                    outcome.draft.policy_snapshot_hash,
                    outcome.draft.fact_version_set_hash,
                    tuple(str(lock.version_id) for lock in outcome.draft.fact_locks),
                )
            )
        elif outcome.disposition is DraftDisposition.HANDOFF_REQUIRED and outcome.handoff is not None:
            parts.extend(
                (
                    self._handoff_reason(receipt, outcome),
                    outcome.handoff.policy_version,
                    outcome.handoff.policy_snapshot_hash,
                )
            )
        return _digest(*parts)

    @staticmethod
    def _handoff_reason(receipt: ConversationReceipt, outcome: DraftOutcome) -> str:
        if outcome.handoff is None:
            raise _boundary("handoff_reason_required")
        handoff_reason = outcome.handoff.reason_code
        if (
            handoff_reason == "conversation_handoff_required"
            and receipt.disposition is SupportDisposition.HANDOFF_REQUIRED
            and receipt.handoff is not None
        ):
            handoff_reason = receipt.handoff.reason.value
        return handoff_reason

    def _build_case(
        self,
        receipt: ConversationReceipt,
        outcome: DraftOutcome,
        *,
        actor_ref: str,
        fingerprint: str,
    ) -> SupportReviewCase:
        assert receipt.conversation is not None
        assert receipt.message is not None
        created_at = self._now()
        if outcome.disposition is DraftDisposition.DRAFT_READY:
            if outcome.draft is None:
                raise _boundary("draft_ref_required")
            fact_version_ids = tuple(str(lock.version_id) for lock in outcome.draft.fact_locks)
            evidence_refs = tuple(dict.fromkeys(lock.evidence_ref for lock in outcome.draft.fact_locks))
            subject_version = max(lock.version_no for lock in outcome.draft.fact_locks)
            return SupportReviewCase(
                case_ref=_stable_ref("support_case", receipt.message.id, fingerprint),
                scope=receipt.message.scope,
                conversation_id=receipt.conversation.id,
                message_id=receipt.message.id,
                intake_disposition=receipt.disposition.value,
                state=SupportCaseState.DRAFT_ONLY,
                policy_version=outcome.draft.policy_version,
                policy_snapshot_hash=outcome.draft.policy_snapshot_hash,
                fact_version_set_hash=outcome.draft.fact_version_set_hash,
                fact_version_ids=fact_version_ids,
                evidence_refs=evidence_refs or ("support_evidence_ref",),
                subject_version=subject_version,
                created_at=created_at,
                created_by=actor_ref,
                automation_paused=True,
                draft_ref=outcome.draft.draft_ref,
            )
        if outcome.disposition is DraftDisposition.HANDOFF_REQUIRED:
            if outcome.handoff is None:
                raise _boundary("handoff_reason_required")
            handoff_reason = self._handoff_reason(receipt, outcome)
            return SupportReviewCase(
                case_ref=_stable_ref("support_case", receipt.message.id, fingerprint),
                scope=receipt.message.scope,
                conversation_id=receipt.conversation.id,
                message_id=receipt.message.id,
                intake_disposition=receipt.disposition.value,
                state=SupportCaseState.MANUAL_HANDOFF,
                policy_version=outcome.handoff.policy_version,
                policy_snapshot_hash=outcome.handoff.policy_snapshot_hash,
                fact_version_set_hash=None,
                fact_version_ids=(),
                evidence_refs=("support_handoff_evidence_ref",),
                subject_version=1,
                created_at=created_at,
                created_by=actor_ref,
                automation_paused=True,
                handoff_reason_code=handoff_reason,
            )
        if receipt.disposition is SupportDisposition.HANDOFF_REQUIRED and receipt.handoff is not None:
            return SupportReviewCase(
                case_ref=_stable_ref("support_case", receipt.message.id, fingerprint),
                scope=receipt.message.scope,
                conversation_id=receipt.conversation.id,
                message_id=receipt.message.id,
                intake_disposition=receipt.disposition.value,
                state=SupportCaseState.MANUAL_HANDOFF,
                policy_version=receipt.handoff.policy_version,
                policy_snapshot_hash=_digest("conversation_handoff", receipt.handoff.id),
                fact_version_set_hash=None,
                fact_version_ids=(),
                evidence_refs=("support_handoff_evidence_ref",),
                subject_version=1,
                created_at=created_at,
                created_by=actor_ref,
                automation_paused=True,
                handoff_reason_code=receipt.handoff.reason.value,
            )
        raise _boundary("draft_or_handoff_required")

    def _case(self, case_ref: str) -> SupportReviewCase:
        ref = _require_identifier(case_ref, "support_case_ref_required")
        case = self._cases_by_ref.get(ref)
        if case is None:
            raise _boundary("support_case_not_found")
        return case


__all__ = [
    "HumanDecision",
    "SupportCaseQueue",
    "SupportCaseReceipt",
    "SupportCaseState",
    "SupportHumanDecisionRecord",
    "SupportReviewCase",
    "SupportTakeoverBoundaryError",
    "SupportZeroSendProof",
]
