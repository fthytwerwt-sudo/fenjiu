"""P06-02 approved-fact retrieval, risk policy, and draft contracts.

The module is stdlib-only, local-only, and synthetic. It creates reviewable
draft references or manual handoff evidence; it does not write truth, approval,
or outbound delivery state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import re
from typing import Callable
from uuid import NAMESPACE_URL, UUID, uuid5

from core.contracts import ContractValidationError, DataState, ScopeRef
from modules.customer_service.contracts import (
    ConversationReceipt,
    RiskLevel,
    SupportDisposition,
)


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)

_BUSINESS_GATE_INTENTS = frozenset(
    {
        "price",
        "inventory",
        "delivery",
        "alcohol_purchase",
        "quote",
        "refund",
        "complaint",
        "quality",
        "credit_terms",
        "exclusive",
        "order",
        "payment",
        "unknown",
    }
)
_LOW_RISK_DRAFT_INTENTS = frozenset(
    {
        "faq_general",
        "faq_product_info",
        "faq_brand",
        "faq_usage",
        "greeting",
    }
)


class DraftBoundaryError(ContractValidationError):
    """Stable, value-free P06-02 boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class DraftDisposition(str, Enum):
    DRAFT_READY = "draft_ready"
    HANDOFF_REQUIRED = "handoff_required"


class FactApprovalState(str, Enum):
    APPROVED = "approved"
    EXPIRED = "expired"
    REVOKED = "revoked"
    CONFLICT = "conflict"
    BLOCKED = "blocked"
    SUPERSEDED = "superseded"


def _boundary(code: str) -> DraftBoundaryError:
    return DraftBoundaryError(code)


def _digest(*parts: object) -> str:
    return sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _stable_id(kind: str, *parts: object) -> UUID:
    return uuid5(NAMESPACE_URL, "|".join((kind, *(str(part) for part in parts))))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _reject_sensitive_text(value: object) -> None:
    if not isinstance(value, str):
        return
    local_user_root = "/" + "Users" + "/"
    local_volume_root = "/" + "Volumes" + "/"
    if value.startswith("/") or "\\" in value or local_user_root in value or local_volume_root in value:
        raise _boundary("privacy_payload_forbidden")
    if _SENSITIVE.search(value) is not None:
        raise _boundary("privacy_payload_forbidden")


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


def _require_time(value: object, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _boundary(code)
    return value


def _require_scope(value: object) -> ScopeRef:
    if not isinstance(value, ScopeRef):
        raise _boundary("scope_required")
    _require_identifier(value.correlation_id, "correlation_id_required")
    return value


def _require_text_input(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise _boundary(code)
    _reject_sensitive_text(value)
    return value


def _require_synthetic_local(
    is_synthetic: object,
    external_execution_allowed: object,
) -> None:
    if is_synthetic is not True:
        raise _boundary("synthetic_input_required")
    if external_execution_allowed is not False:
        raise _boundary("external_execution_forbidden")


def _same_scope(expected: ScopeRef, actual: ScopeRef) -> None:
    if actual != expected:
        raise _boundary("cross_scope_forbidden")


@dataclass(frozen=True)
class ApprovedFactRef:
    """Synthetic approved fact version reference consumable by P06-02."""

    scope: ScopeRef
    fact_ref: str
    fact_type: str
    subject_ref: str
    version_id: UUID
    version_no: int
    approval_state: FactApprovalState
    data_state: DataState
    observed_at: datetime
    expires_at: datetime
    source_ref: str
    evidence_ref: str
    value_hash: str
    policy_version: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_identifier(self.fact_ref, "fact_ref_required")
        _require_identifier(self.fact_type, "fact_type_required")
        _require_identifier(self.subject_ref, "subject_ref_required")
        _require_uuid(self.version_id, "fact_version_id_required")
        if not isinstance(self.version_no, int) or isinstance(self.version_no, bool) or self.version_no < 1:
            raise _boundary("fact_version_required")
        if not isinstance(self.approval_state, FactApprovalState):
            raise _boundary("approval_state_required")
        if self.data_state is not DataState.FIXTURE:
            raise _boundary("synthetic_fact_state_required")
        observed_at = _require_time(self.observed_at, "observed_at_required")
        expires_at = _require_time(self.expires_at, "expires_at_required")
        if expires_at <= observed_at:
            raise _boundary("fact_window_invalid")
        _require_identifier(self.source_ref, "source_ref_required")
        _require_identifier(self.evidence_ref, "evidence_ref_required")
        _require_hash(self.value_hash, "value_hash_required")
        _require_identifier(self.policy_version, "fact_policy_version_required")
        _require_synthetic_local(self.is_synthetic, self.external_execution_allowed)

    def denial_code(self, checked_at: datetime) -> str | None:
        _require_time(checked_at, "checked_at_required")
        if self.approval_state is FactApprovalState.CONFLICT:
            return "approved_fact_conflict"
        if self.approval_state is FactApprovalState.REVOKED:
            return "approved_fact_revoked"
        if self.approval_state is FactApprovalState.BLOCKED:
            return "approved_fact_blocked"
        if self.approval_state is FactApprovalState.SUPERSEDED:
            return "approved_fact_superseded"
        if self.approval_state is FactApprovalState.EXPIRED or self.expires_at <= checked_at:
            return "approved_fact_expired"
        if self.approval_state is not FactApprovalState.APPROVED:
            return "approved_fact_missing"
        return None

    def safe_summary(self) -> dict[str, object]:
        return {
            "fact_ref": self.fact_ref,
            "fact_type": self.fact_type,
            "subject_ref": self.subject_ref,
            "version_id": str(self.version_id),
            "version_no": self.version_no,
            "approval_state": self.approval_state.value,
            "data_state": self.data_state.value,
            "observed_at": self.observed_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "source_ref": self.source_ref,
            "evidence_ref": self.evidence_ref,
            "value_hash": self.value_hash,
            "policy_version": self.policy_version,
            "external_execution_allowed": self.external_execution_allowed,
        }


@dataclass(frozen=True)
class ForbiddenExpressionPolicy:
    """Synthetic forbidden-expression policy for draft review."""

    scope: ScopeRef
    locale: str
    policy_version: str
    denied_tokens: tuple[str, ...]
    observed_at: datetime
    expires_at: datetime
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_identifier(self.locale, "locale_required")
        _require_identifier(self.policy_version, "forbidden_policy_version_required")
        if not isinstance(self.denied_tokens, tuple):
            raise _boundary("forbidden_policy_required")
        for token in self.denied_tokens:
            _require_text_input(token, "forbidden_token_required")
        observed_at = _require_time(self.observed_at, "observed_at_required")
        expires_at = _require_time(self.expires_at, "expires_at_required")
        if expires_at <= observed_at:
            raise _boundary("policy_window_invalid")
        _require_synthetic_local(self.is_synthetic, self.external_execution_allowed)

    def owner_ready(self, checked_at: datetime) -> bool:
        _require_time(checked_at, "checked_at_required")
        return bool(self.denied_tokens) and self.expires_at > checked_at

    def denied_token_hashes(self) -> tuple[str, ...]:
        return tuple(_digest("forbidden_token", token) for token in self.denied_tokens)

    def contains_forbidden(self, output_text: str) -> bool:
        text = output_text.lower()
        return any(token.lower() in text for token in self.denied_tokens)

    def safe_summary(self) -> dict[str, object]:
        return {
            "locale": self.locale,
            "policy_version": self.policy_version,
            "denied_token_hashes": self.denied_token_hashes(),
            "observed_at": self.observed_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "external_execution_allowed": self.external_execution_allowed,
        }


@dataclass(frozen=True)
class FactQueryResult:
    facts: tuple[ApprovedFactRef, ...]
    denial_code: str | None = None


class InMemoryApprovedFactQuery:
    """Read-only synthetic fact query port."""

    def __init__(
        self,
        facts: tuple[ApprovedFactRef, ...],
        *,
        fail_code: str | None = None,
    ) -> None:
        if not isinstance(facts, tuple):
            raise _boundary("fact_set_required")
        self._facts = facts
        self._fail_code = fail_code
        self.call_count = 0

    def query(
        self,
        *,
        scope: ScopeRef,
        fact_type: str,
        subject_ref: str,
        checked_at: datetime,
    ) -> FactQueryResult:
        self.call_count += 1
        if self._fail_code is not None:
            return FactQueryResult((), self._fail_code)
        scope = _require_scope(scope)
        fact_type = _require_identifier(fact_type, "fact_type_required")
        subject_ref = _require_identifier(subject_ref, "subject_ref_required")
        checked_at = _require_time(checked_at, "checked_at_required")

        matching: list[ApprovedFactRef] = []
        for candidate in self._facts:
            if not isinstance(candidate, ApprovedFactRef):
                raise _boundary("approved_fact_required")
            if candidate.fact_type == fact_type and candidate.subject_ref == subject_ref:
                _same_scope(scope, candidate.scope)
                matching.append(candidate)
        if not matching:
            return FactQueryResult((), "approved_fact_missing")

        available: list[ApprovedFactRef] = []
        denials: list[str] = []
        for candidate in matching:
            denial = candidate.denial_code(checked_at)
            if denial is None:
                available.append(candidate)
            else:
                denials.append(denial)
        if available:
            return FactQueryResult(tuple(available), None)
        return FactQueryResult((), _first_denial(denials))


def _first_denial(denials: list[str]) -> str:
    priority = (
        "approved_fact_conflict",
        "approved_fact_revoked",
        "approved_fact_expired",
        "approved_fact_blocked",
        "approved_fact_superseded",
    )
    for code in priority:
        if code in denials:
            return code
    return denials[0] if denials else "approved_fact_missing"


class FakeDraftModel:
    """Deterministic fake model. It never receives or returns through a provider."""

    model_ref = "fake_model:support_draft_v1"

    def __init__(
        self,
        *,
        outputs: dict[str, str],
        fail_code: str | None = None,
    ) -> None:
        self._outputs = dict(outputs)
        self._fail_code = fail_code
        self.call_count = 0

    def generate(
        self,
        *,
        intent_label: str,
        locale: str,
        fact_locks: tuple["DraftFactLock", ...],
        template_version: str,
    ) -> str:
        self.call_count += 1
        _require_identifier(intent_label, "intent_label_required")
        _require_identifier(locale, "locale_required")
        _require_identifier(template_version, "template_version_required")
        if not fact_locks:
            raise _boundary("fact_lock_required")
        if self._fail_code is not None:
            raise _boundary(self._fail_code)
        output = self._outputs.get(intent_label)
        if output is None:
            raise _boundary("model_output_missing")
        return _require_text_input(output, "model_output_required")


@dataclass(frozen=True)
class DraftFactLock:
    fact_ref: str
    fact_type: str
    subject_ref: str
    version_id: UUID
    version_no: int
    approval_state: FactApprovalState
    data_state: DataState
    evidence_ref: str
    policy_version: str
    value_hash: str
    external_execution_allowed: bool = False

    @classmethod
    def from_fact(cls, fact: ApprovedFactRef) -> "DraftFactLock":
        return cls(
            fact_ref=fact.fact_ref,
            fact_type=fact.fact_type,
            subject_ref=fact.subject_ref,
            version_id=fact.version_id,
            version_no=fact.version_no,
            approval_state=fact.approval_state,
            data_state=fact.data_state,
            evidence_ref=fact.evidence_ref,
            policy_version=fact.policy_version,
            value_hash=fact.value_hash,
            external_execution_allowed=fact.external_execution_allowed,
        )

    def __post_init__(self) -> None:
        _require_identifier(self.fact_ref, "fact_ref_required")
        _require_identifier(self.fact_type, "fact_type_required")
        _require_identifier(self.subject_ref, "subject_ref_required")
        _require_uuid(self.version_id, "fact_version_id_required")
        if not isinstance(self.version_no, int) or isinstance(self.version_no, bool) or self.version_no < 1:
            raise _boundary("fact_version_required")
        if self.approval_state is not FactApprovalState.APPROVED:
            raise _boundary("approved_fact_required")
        if self.data_state is not DataState.FIXTURE:
            raise _boundary("synthetic_fact_state_required")
        _require_identifier(self.evidence_ref, "evidence_ref_required")
        _require_identifier(self.policy_version, "fact_policy_version_required")
        _require_hash(self.value_hash, "value_hash_required")
        if self.external_execution_allowed is not False:
            raise _boundary("external_execution_forbidden")

    def safe_summary(self) -> dict[str, object]:
        return {
            "fact_ref": self.fact_ref,
            "fact_type": self.fact_type,
            "subject_ref": self.subject_ref,
            "version_id": str(self.version_id),
            "version_no": self.version_no,
            "approval_state": self.approval_state.value,
            "data_state": self.data_state.value,
            "evidence_ref": self.evidence_ref,
            "policy_version": self.policy_version,
            "value_hash": self.value_hash,
            "external_execution_allowed": self.external_execution_allowed,
        }


@dataclass(frozen=True)
class DraftReviewRecord:
    id: UUID
    scope: ScopeRef
    conversation_id: UUID
    message_id: UUID
    draft_ref: str
    locale: str
    original_text_hash: str
    translated_text_hash: str
    translation_ref: str
    translation_model_ref: str
    prompt_hash: str
    output_hash: str
    fact_locks: tuple[DraftFactLock, ...]
    fact_version_set_hash: str
    policy_version: str
    forbidden_policy_version: str
    model_ref: str
    template_version: str
    created_at: datetime
    created_by: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    send_allowed: bool = False
    truth_write_allowed: bool = False
    approval_write_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_uuid(self.conversation_id, "conversation_id_required")
        _require_uuid(self.message_id, "message_id_required")
        _require_identifier(self.draft_ref, "draft_ref_required")
        _require_identifier(self.locale, "locale_required")
        _require_hash(self.original_text_hash, "original_text_hash_required")
        _require_hash(self.translated_text_hash, "translated_text_hash_required")
        _require_identifier(self.translation_ref, "translation_ref_required")
        _require_identifier(self.translation_model_ref, "translation_model_ref_required")
        _require_hash(self.prompt_hash, "prompt_hash_required")
        _require_hash(self.output_hash, "output_hash_required")
        if not self.fact_locks:
            raise _boundary("fact_lock_required")
        for fact_lock in self.fact_locks:
            if not isinstance(fact_lock, DraftFactLock):
                raise _boundary("fact_lock_required")
        _require_hash(self.fact_version_set_hash, "fact_version_set_hash_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_identifier(self.forbidden_policy_version, "forbidden_policy_version_required")
        _require_identifier(self.model_ref, "model_ref_required")
        _require_identifier(self.template_version, "template_version_required")
        _require_time(self.created_at, "created_at_required")
        _require_identifier(self.created_by, "created_by_required")
        _require_synthetic_local(self.is_synthetic, self.external_execution_allowed)
        if self.send_allowed or self.truth_write_allowed or self.approval_write_allowed:
            raise _boundary("external_execution_forbidden")

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "message_id": str(self.message_id),
            "draft_ref": self.draft_ref,
            "locale": self.locale,
            "original_text_hash": self.original_text_hash,
            "translated_text_hash": self.translated_text_hash,
            "translation_ref": self.translation_ref,
            "translation_model_ref": self.translation_model_ref,
            "prompt_hash": self.prompt_hash,
            "output_hash": self.output_hash,
            "fact_locks": [fact.safe_summary() for fact in self.fact_locks],
            "fact_version_set_hash": self.fact_version_set_hash,
            "policy_version": self.policy_version,
            "forbidden_policy_version": self.forbidden_policy_version,
            "model_ref": self.model_ref,
            "template_version": self.template_version,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "external_execution_allowed": self.external_execution_allowed,
            "send_allowed": self.send_allowed,
            "truth_write_allowed": self.truth_write_allowed,
            "approval_write_allowed": self.approval_write_allowed,
        }


@dataclass(frozen=True)
class ManualHandoffRecord:
    id: UUID
    scope: ScopeRef | None
    conversation_id: UUID | None
    message_id: UUID | None
    reason_code: str
    locale: str
    policy_version: str
    original_text_hash: str
    translated_text_hash: str
    fact_query_ref: str
    model_ref: str
    created_at: datetime
    created_by: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    send_allowed: bool = False
    truth_write_allowed: bool = False
    approval_write_allowed: bool = False

    def __post_init__(self) -> None:
        if self.scope is not None:
            _require_scope(self.scope)
        if self.conversation_id is not None:
            _require_uuid(self.conversation_id, "conversation_id_required")
        if self.message_id is not None:
            _require_uuid(self.message_id, "message_id_required")
        _require_identifier(self.reason_code, "handoff_reason_required")
        _require_identifier(self.locale, "locale_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_hash(self.original_text_hash, "original_text_hash_required")
        _require_hash(self.translated_text_hash, "translated_text_hash_required")
        _require_identifier(self.fact_query_ref, "fact_query_ref_required")
        _require_identifier(self.model_ref, "model_ref_required")
        _require_time(self.created_at, "created_at_required")
        _require_identifier(self.created_by, "created_by_required")
        _require_synthetic_local(self.is_synthetic, self.external_execution_allowed)
        if self.send_allowed or self.truth_write_allowed or self.approval_write_allowed:
            raise _boundary("external_execution_forbidden")

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "scope_known": self.scope is not None,
            "conversation_id": None if self.conversation_id is None else str(self.conversation_id),
            "message_id": None if self.message_id is None else str(self.message_id),
            "reason_code": self.reason_code,
            "locale": self.locale,
            "policy_version": self.policy_version,
            "original_text_hash": self.original_text_hash,
            "translated_text_hash": self.translated_text_hash,
            "fact_query_ref": self.fact_query_ref,
            "model_ref": self.model_ref,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "external_execution_allowed": self.external_execution_allowed,
            "send_allowed": self.send_allowed,
            "truth_write_allowed": self.truth_write_allowed,
            "approval_write_allowed": self.approval_write_allowed,
        }


@dataclass(frozen=True)
class DraftOutcome:
    disposition: DraftDisposition
    draft: DraftReviewRecord | None
    handoff: ManualHandoffRecord | None

    def safe_summary(self) -> dict[str, object]:
        return {
            "disposition": self.disposition.value,
            "draft": None if self.draft is None else self.draft.safe_summary(),
            "handoff": None if self.handoff is None else self.handoff.safe_summary(),
        }


class SupportDraftPipeline:
    """Risk-first synthetic draft pipeline."""

    def __init__(
        self,
        *,
        fact_query: InMemoryApprovedFactQuery,
        model: FakeDraftModel,
        forbidden_policy: ForbiddenExpressionPolicy,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(fact_query, InMemoryApprovedFactQuery):
            raise _boundary("fact_query_required")
        if not isinstance(model, FakeDraftModel):
            raise _boundary("fake_model_required")
        if not isinstance(forbidden_policy, ForbiddenExpressionPolicy):
            raise _boundary("forbidden_policy_required")
        self._fact_query = fact_query
        self._model = model
        self._forbidden_policy = forbidden_policy
        self._now = now or _now_utc

    def prepare(
        self,
        receipt: ConversationReceipt,
        *,
        locale: str,
        subject_ref: str,
        original_text: str,
        translated_text: str,
        translation_ref: str,
        translation_model_ref: str,
        template_version: str,
    ) -> DraftOutcome:
        if not isinstance(receipt, ConversationReceipt):
            raise _boundary("conversation_receipt_required")
        locale = _require_identifier(locale, "locale_required")
        subject_ref = _require_identifier(subject_ref, "subject_ref_required")
        original_text = _require_text_input(original_text, "original_text_required")
        translated_text = _require_text_input(translated_text, "translated_text_required")
        translation_ref = _require_identifier(translation_ref, "translation_ref_required")
        translation_model_ref = _require_identifier(
            translation_model_ref,
            "translation_model_ref_required",
        )
        template_version = _require_identifier(template_version, "template_version_required")
        original_hash = _digest("original", original_text)
        translated_hash = _digest("translated", translated_text)
        checked_at = self._now()

        if receipt.disposition is not SupportDisposition.DRAFT_READY:
            return self._handoff(
                receipt,
                reason_code="conversation_handoff_required",
                locale=locale,
                policy_version=_receipt_policy(receipt),
                original_text_hash=original_hash,
                translated_text_hash=translated_hash,
                checked_at=checked_at,
            )
        if receipt.message is None or receipt.intent is None or receipt.conversation is None:
            return self._handoff(
                receipt,
                reason_code="conversation_context_missing",
                locale=locale,
                policy_version=_receipt_policy(receipt),
                original_text_hash=original_hash,
                translated_text_hash=translated_hash,
                checked_at=checked_at,
            )
        _same_scope(receipt.message.scope, receipt.intent.scope)
        _same_scope(receipt.message.scope, receipt.conversation.scope)

        intent_label = receipt.intent.intent_label
        if _requires_manual_risk(intent_label, receipt.intent.risk_level):
            return self._handoff(
                receipt,
                reason_code="risk_policy_manual_required",
                locale=locale,
                policy_version=receipt.intent.policy_version,
                original_text_hash=original_hash,
                translated_text_hash=translated_hash,
                checked_at=checked_at,
            )
        if not self._forbidden_policy.owner_ready(checked_at):
            return self._handoff(
                receipt,
                reason_code="policy_owner_missing",
                locale=locale,
                policy_version=receipt.intent.policy_version,
                original_text_hash=original_hash,
                translated_text_hash=translated_hash,
                checked_at=checked_at,
            )
        _same_scope(receipt.message.scope, self._forbidden_policy.scope)

        fact_result = self._fact_query.query(
            scope=receipt.message.scope,
            fact_type=intent_label,
            subject_ref=subject_ref,
            checked_at=checked_at,
        )
        if fact_result.denial_code is not None:
            return self._handoff(
                receipt,
                reason_code=fact_result.denial_code,
                locale=locale,
                policy_version=receipt.intent.policy_version,
                original_text_hash=original_hash,
                translated_text_hash=translated_hash,
                checked_at=checked_at,
            )
        fact_locks = tuple(DraftFactLock.from_fact(fact) for fact in fact_result.facts)
        try:
            output_text = self._model.generate(
                intent_label=intent_label,
                locale=locale,
                fact_locks=fact_locks,
                template_version=template_version,
            )
        except DraftBoundaryError as exc:
            return self._handoff(
                receipt,
                reason_code=exc.code,
                locale=locale,
                policy_version=receipt.intent.policy_version,
                original_text_hash=original_hash,
                translated_text_hash=translated_hash,
                checked_at=checked_at,
            )
        if self._forbidden_policy.contains_forbidden(output_text):
            return self._handoff(
                receipt,
                reason_code="forbidden_expression_detected",
                locale=locale,
                policy_version=receipt.intent.policy_version,
                original_text_hash=original_hash,
                translated_text_hash=translated_hash,
                checked_at=checked_at,
            )

        fact_version_set_hash = _digest(
            "fact_version_set",
            tuple(str(fact.version_id) for fact in fact_locks),
            tuple(fact.value_hash for fact in fact_locks),
        )
        prompt_hash = _digest(
            "prompt",
            locale,
            receipt.message.content_hash,
            translated_hash,
            fact_version_set_hash,
            self._forbidden_policy.policy_version,
            template_version,
        )
        output_hash = _digest("output", output_text)
        draft = DraftReviewRecord(
            id=_stable_id("p06_02_draft", receipt.message.id, fact_version_set_hash, output_hash),
            scope=receipt.message.scope,
            conversation_id=receipt.conversation.id,
            message_id=receipt.message.id,
            draft_ref="draft_ref:" + output_hash[:32],
            locale=locale,
            original_text_hash=original_hash,
            translated_text_hash=translated_hash,
            translation_ref=translation_ref,
            translation_model_ref=translation_model_ref,
            prompt_hash=prompt_hash,
            output_hash=output_hash,
            fact_locks=fact_locks,
            fact_version_set_hash=fact_version_set_hash,
            policy_version=receipt.intent.policy_version,
            forbidden_policy_version=self._forbidden_policy.policy_version,
            model_ref=self._model.model_ref,
            template_version=template_version,
            created_at=self._now(),
            created_by="synthetic_support_draft_worker",
        )
        return DraftOutcome(DraftDisposition.DRAFT_READY, draft, None)

    def _handoff(
        self,
        receipt: ConversationReceipt,
        *,
        reason_code: str,
        locale: str,
        policy_version: str,
        original_text_hash: str,
        translated_text_hash: str,
        checked_at: datetime,
    ) -> DraftOutcome:
        scope = None if receipt.message is None else receipt.message.scope
        conversation_id = None if receipt.conversation is None else receipt.conversation.id
        message_id = None if receipt.message is None else receipt.message.id
        handoff = ManualHandoffRecord(
            id=_stable_id(
                "p06_02_handoff",
                scope,
                conversation_id,
                message_id,
                reason_code,
                checked_at.isoformat(),
            ),
            scope=scope,
            conversation_id=conversation_id,
            message_id=message_id,
            reason_code=reason_code,
            locale=locale,
            policy_version=policy_version,
            original_text_hash=original_text_hash,
            translated_text_hash=translated_text_hash,
            fact_query_ref="fact_query:p06_02_read_only",
            model_ref=self._model.model_ref,
            created_at=self._now(),
            created_by="synthetic_support_handoff_worker",
        )
        return DraftOutcome(DraftDisposition.HANDOFF_REQUIRED, None, handoff)


def _receipt_policy(receipt: ConversationReceipt) -> str:
    if receipt.intent is not None:
        return receipt.intent.policy_version
    if receipt.handoff is not None:
        return receipt.handoff.policy_version
    if receipt.quarantine is not None:
        return receipt.quarantine.policy_version
    return "support_contract_v2"


def _requires_manual_risk(intent_label: str, risk_level: RiskLevel) -> bool:
    if risk_level is RiskLevel.HIGH:
        return True
    if intent_label in _BUSINESS_GATE_INTENTS:
        return True
    return intent_label not in _LOW_RISK_DRAFT_INTENTS


__all__ = [
    "ApprovedFactRef",
    "DraftBoundaryError",
    "DraftDisposition",
    "DraftFactLock",
    "DraftOutcome",
    "DraftReviewRecord",
    "FactApprovalState",
    "FactQueryResult",
    "FakeDraftModel",
    "ForbiddenExpressionPolicy",
    "InMemoryApprovedFactQuery",
    "ManualHandoffRecord",
    "SupportDraftPipeline",
]
