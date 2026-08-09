"""P06-01 local customer-service conversation contracts.

The module is stdlib-only and synthetic. It records only scoped metadata,
content hashes, opaque content references, draft references, and handoff
references. It does not provide channel adapters, webhooks, or outbound
endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import re
from typing import Callable
from uuid import NAMESPACE_URL, UUID, uuid5

from core.contracts import ContractValidationError, ScopeRef


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_REF = re.compile(r"^ref:[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_EMAIL_LIKE = re.compile(r"(?i)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)


class ConversationBoundaryError(ContractValidationError):
    """Stable, value-free P06-01 boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ScopeStatus(str, Enum):
    KNOWN = "known"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    HIGH = "high"


class SupportDisposition(str, Enum):
    DRAFT_READY = "draft_ready"
    HANDOFF_REQUIRED = "handoff_required"
    QUARANTINED = "quarantined"


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    HELD = "held"
    HANDOFF_REQUIRED = "handoff_required"


class MessageDirection(str, Enum):
    INBOUND = "inbound"


class DraftState(str, Enum):
    DRAFT_ONLY = "draft_only"


class HandoffReason(str, Enum):
    UNKNOWN_SCOPE = "unknown_scope"
    DNC_BLOCKED = "dnc_blocked"
    PRIVACY_REVIEW_REQUIRED = "privacy_review_required"
    HIGH_RISK = "high_risk"


class HandoffStatus(str, Enum):
    OPEN = "open"


def _boundary(code: str) -> ConversationBoundaryError:
    return ConversationBoundaryError(code)


def _require_identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _boundary(code)
    _reject_sensitive_text(value)
    return value


def _require_ref(value: object, code: str) -> str:
    if not isinstance(value, str) or _REF.fullmatch(value) is None:
        raise _boundary(code)
    _reject_sensitive_text(value)
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


def _reject_sensitive_text(value: object) -> None:
    if not isinstance(value, str):
        return
    local_user_root = "/" + "Users" + "/"
    local_volume_root = "/" + "Volumes" + "/"
    if value.startswith("/") or "\\" in value or local_user_root in value or local_volume_root in value:
        raise _boundary("privacy_payload_forbidden")
    if _SENSITIVE.search(value) is not None:
        raise _boundary("privacy_payload_forbidden")


def _validate_body(body_text: object, *, personal_data_detected: bool) -> str:
    if not isinstance(body_text, str) or not body_text:
        raise _boundary("message_body_required")
    _reject_sensitive_text(body_text)
    if _EMAIL_LIKE.search(body_text) is not None and personal_data_detected is not True:
        raise _boundary("privacy_payload_forbidden")
    return body_text


def _digest(*parts: object) -> str:
    return sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _stable_id(kind: str, *parts: object) -> UUID:
    return uuid5(NAMESPACE_URL, "|".join((kind, *(str(part) for part in parts))))


def _scope_key(scope: ScopeRef) -> tuple[UUID, UUID, UUID]:
    return (scope.tenant_id, scope.project_id, scope.business_line_id)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class InboundMessageCommand:
    """Synthetic inbound message vector. Body text is input-only, never stored."""

    scope: ScopeRef | None
    scope_status: ScopeStatus
    channel_ref: str
    external_conversation_ref: str
    external_message_ref: str
    received_at: datetime
    received_by: str
    body_text: str
    content_ref: str
    intent_label: str
    risk_level: RiskLevel
    retention_policy_ref: str
    consent_ref: str
    dnc_blocked: bool
    personal_data_detected: bool
    policy_version: str
    idempotency_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.scope_status, ScopeStatus):
            raise _boundary("scope_status_required")
        if self.scope_status is ScopeStatus.KNOWN:
            _require_scope(self.scope)
        elif self.scope is not None:
            raise _boundary("unknown_scope_must_not_bind_scope")
        _require_identifier(self.channel_ref, "channel_ref_required")
        _require_ref(self.external_conversation_ref, "external_conversation_ref_required")
        _require_ref(self.external_message_ref, "external_message_ref_required")
        _require_time(self.received_at, "received_at_required")
        _require_identifier(self.received_by, "received_by_required")
        if not isinstance(self.personal_data_detected, bool):
            raise _boundary("personal_data_status_required")
        _validate_body(
            self.body_text,
            personal_data_detected=self.personal_data_detected,
        )
        _require_ref(self.content_ref, "content_ref_required")
        _require_identifier(self.intent_label, "intent_label_required")
        if not isinstance(self.risk_level, RiskLevel):
            raise _boundary("risk_level_required")
        _require_identifier(self.retention_policy_ref, "retention_policy_ref_required")
        _require_identifier(self.consent_ref, "consent_ref_required")
        if not isinstance(self.dnc_blocked, bool):
            raise _boundary("dnc_status_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_identifier(self.idempotency_key, "idempotency_key_required")

    @property
    def content_hash(self) -> str:
        return _digest("support_content", self.body_text)

    @property
    def input_fingerprint(self) -> str:
        scope_key = self.scope if self.scope is None else _scope_key(self.scope)
        return _digest(
            scope_key,
            self.scope_status.value,
            self.channel_ref,
            self.external_conversation_ref,
            self.external_message_ref,
            self.content_hash,
            self.content_ref,
            self.intent_label,
            self.risk_level.value,
            self.retention_policy_ref,
            self.consent_ref,
            self.dnc_blocked,
            self.personal_data_detected,
            self.policy_version,
            self.idempotency_key,
        )


@dataclass(frozen=True)
class ConversationRecord:
    id: UUID
    scope: ScopeRef
    channel_ref: str
    external_conversation_ref: str
    status: ConversationStatus
    retention_policy_ref: str
    consent_ref: str
    created_at: datetime
    created_by: str
    correlation_id: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_identifier(self.channel_ref, "channel_ref_required")
        _require_ref(self.external_conversation_ref, "external_conversation_ref_required")
        if not isinstance(self.status, ConversationStatus):
            raise _boundary("conversation_status_required")
        _require_identifier(self.retention_policy_ref, "retention_policy_ref_required")
        _require_identifier(self.consent_ref, "consent_ref_required")
        _require_time(self.created_at, "created_at_required")
        _require_identifier(self.created_by, "created_by_required")
        _require_identifier(self.correlation_id, "correlation_id_required")
        if self.correlation_id != self.scope.correlation_id:
            raise _boundary("correlation_mismatch")
        _require_synthetic_local(self.is_synthetic, self.external_execution_allowed)

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "channel_ref": self.channel_ref,
            "external_conversation_ref": self.external_conversation_ref,
            "status": self.status.value,
            "retention_policy_ref": self.retention_policy_ref,
            "consent_ref": self.consent_ref,
            "correlation_id": self.correlation_id,
            "is_synthetic": self.is_synthetic,
            "external_execution_allowed": self.external_execution_allowed,
        }


@dataclass(frozen=True)
class MessageRecord:
    id: UUID
    conversation_id: UUID
    scope: ScopeRef
    direction: MessageDirection
    external_message_ref: str
    content_hash: str
    content_ref: str
    received_at: datetime
    received_by: str
    retention_policy_ref: str
    redaction_ref: str
    consent_ref: str
    correlation_id: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        if self.direction is not MessageDirection.INBOUND:
            raise _boundary("message_direction_required")
        _require_ref(self.external_message_ref, "external_message_ref_required")
        _require_hash(self.content_hash, "content_hash_required")
        _require_ref(self.content_ref, "content_ref_required")
        _require_time(self.received_at, "received_at_required")
        _require_identifier(self.received_by, "received_by_required")
        _require_identifier(self.retention_policy_ref, "retention_policy_ref_required")
        _require_identifier(self.redaction_ref, "redaction_ref_required")
        _require_identifier(self.consent_ref, "consent_ref_required")
        _require_identifier(self.correlation_id, "correlation_id_required")
        if self.correlation_id != self.scope.correlation_id:
            raise _boundary("correlation_mismatch")
        _require_synthetic_local(self.is_synthetic, self.external_execution_allowed)

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "direction": self.direction.value,
            "external_message_ref": self.external_message_ref,
            "content_hash": self.content_hash,
            "content_ref": self.content_ref,
            "retention_policy_ref": self.retention_policy_ref,
            "redaction_ref": self.redaction_ref,
            "consent_ref": self.consent_ref,
            "correlation_id": self.correlation_id,
            "is_synthetic": self.is_synthetic,
            "external_execution_allowed": self.external_execution_allowed,
        }


@dataclass(frozen=True)
class IntentRecord:
    id: UUID
    message_id: UUID
    scope: ScopeRef
    intent_label: str
    risk_level: RiskLevel
    policy_version: str
    model_ref: str
    correlation_id: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_identifier(self.intent_label, "intent_label_required")
        if not isinstance(self.risk_level, RiskLevel):
            raise _boundary("risk_level_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_identifier(self.model_ref, "model_ref_required")
        _require_identifier(self.correlation_id, "correlation_id_required")
        if self.correlation_id != self.scope.correlation_id:
            raise _boundary("correlation_mismatch")
        _require_synthetic_local(self.is_synthetic, self.external_execution_allowed)

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "message_id": str(self.message_id),
            "intent_label": self.intent_label,
            "risk_level": self.risk_level.value,
            "policy_version": self.policy_version,
            "model_ref": self.model_ref,
            "correlation_id": self.correlation_id,
            "external_execution_allowed": self.external_execution_allowed,
        }


@dataclass(frozen=True)
class DraftReplyRecord:
    id: UUID
    message_id: UUID
    scope: ScopeRef
    draft_ref: str
    fact_version_set_hash: str
    policy_version: str
    state: DraftState
    correlation_id: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_ref(self.draft_ref, "draft_ref_required")
        _require_hash(self.fact_version_set_hash, "fact_version_set_hash_required")
        _require_identifier(self.policy_version, "policy_version_required")
        if self.state is not DraftState.DRAFT_ONLY:
            raise _boundary("draft_state_required")
        _require_identifier(self.correlation_id, "correlation_id_required")
        if self.correlation_id != self.scope.correlation_id:
            raise _boundary("correlation_mismatch")
        _require_synthetic_local(self.is_synthetic, self.external_execution_allowed)

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "message_id": str(self.message_id),
            "draft_ref": self.draft_ref,
            "fact_version_set_hash": self.fact_version_set_hash,
            "policy_version": self.policy_version,
            "state": self.state.value,
            "correlation_id": self.correlation_id,
            "external_execution_allowed": self.external_execution_allowed,
        }


@dataclass(frozen=True)
class HandoffCase:
    id: UUID
    scope: ScopeRef
    conversation_id: UUID
    message_id: UUID
    reason: HandoffReason
    status: HandoffStatus
    policy_version: str
    correlation_id: str
    created_at: datetime
    created_by: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_uuid(self.conversation_id, "conversation_id_required")
        _require_uuid(self.message_id, "message_id_required")
        if not isinstance(self.reason, HandoffReason):
            raise _boundary("handoff_reason_required")
        if self.reason is HandoffReason.UNKNOWN_SCOPE:
            raise _boundary("unknown_scope_quarantine_required")
        if self.status is not HandoffStatus.OPEN:
            raise _boundary("handoff_status_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_identifier(self.correlation_id, "correlation_id_required")
        if self.correlation_id != self.scope.correlation_id:
            raise _boundary("correlation_mismatch")
        _require_time(self.created_at, "created_at_required")
        _require_identifier(self.created_by, "created_by_required")
        _require_synthetic_local(self.is_synthetic, self.external_execution_allowed)

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "scope_known": True,
            "conversation_id": str(self.conversation_id),
            "message_id": str(self.message_id),
            "reason": self.reason.value,
            "status": self.status.value,
            "policy_version": self.policy_version,
            "correlation_id": self.correlation_id,
            "external_execution_allowed": self.external_execution_allowed,
        }


@dataclass(frozen=True)
class UnknownScopeQuarantineRecord:
    id: UUID
    channel_ref: str
    external_conversation_ref: str
    external_message_ref: str
    content_hash: str
    content_ref: str
    reason: HandoffReason
    status: HandoffStatus
    policy_version: str
    correlation_id: str
    retention_policy_ref: str
    redaction_ref: str
    received_at: datetime
    received_by: str
    created_at: datetime
    created_by: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.channel_ref, "channel_ref_required")
        _require_ref(self.external_conversation_ref, "external_conversation_ref_required")
        _require_ref(self.external_message_ref, "external_message_ref_required")
        _require_hash(self.content_hash, "content_hash_required")
        _require_ref(self.content_ref, "content_ref_required")
        if self.reason is not HandoffReason.UNKNOWN_SCOPE:
            raise _boundary("unknown_scope_reason_required")
        if self.status is not HandoffStatus.OPEN:
            raise _boundary("handoff_status_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_identifier(self.correlation_id, "correlation_id_required")
        _require_identifier(self.retention_policy_ref, "retention_policy_ref_required")
        _require_identifier(self.redaction_ref, "redaction_ref_required")
        _require_time(self.received_at, "received_at_required")
        _require_identifier(self.received_by, "received_by_required")
        _require_time(self.created_at, "created_at_required")
        _require_identifier(self.created_by, "created_by_required")
        _require_synthetic_local(self.is_synthetic, self.external_execution_allowed)

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "channel_ref": self.channel_ref,
            "external_conversation_ref": self.external_conversation_ref,
            "external_message_ref": self.external_message_ref,
            "content_hash": self.content_hash,
            "content_ref": self.content_ref,
            "reason": self.reason.value,
            "status": self.status.value,
            "policy_version": self.policy_version,
            "correlation_id": self.correlation_id,
            "retention_policy_ref": self.retention_policy_ref,
            "redaction_ref": self.redaction_ref,
            "is_synthetic": self.is_synthetic,
            "external_execution_allowed": self.external_execution_allowed,
        }


@dataclass(frozen=True)
class SupportAuditEvent:
    sequence: int
    event_kind: str
    scope: ScopeRef | None
    target_ref: str
    result_code: str
    correlation_id: str
    occurred_at: datetime

    def safe_summary(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "event_kind": self.event_kind,
            "scope_known": self.scope is not None,
            "target_ref": self.target_ref,
            "result_code": self.result_code,
            "correlation_id": self.correlation_id,
            "occurred_at": self.occurred_at.isoformat(),
        }


@dataclass(frozen=True)
class ConversationReceipt:
    disposition: SupportDisposition
    conversation: ConversationRecord | None
    message: MessageRecord | None
    intent: IntentRecord | None
    draft: DraftReplyRecord | None
    handoff: HandoffCase | None
    quarantine: UnknownScopeQuarantineRecord | None
    audit_event: SupportAuditEvent | None
    replayed: bool = False

    def safe_summary(self) -> dict[str, object]:
        return {
            "disposition": self.disposition.value,
            "conversation": None if self.conversation is None else self.conversation.safe_summary(),
            "message": None if self.message is None else self.message.safe_summary(),
            "intent": None if self.intent is None else self.intent.safe_summary(),
            "draft": None if self.draft is None else self.draft.safe_summary(),
            "handoff": None if self.handoff is None else self.handoff.safe_summary(),
            "quarantine": None if self.quarantine is None else self.quarantine.safe_summary(),
            "audit_event": None if self.audit_event is None else self.audit_event.safe_summary(),
            "replayed": self.replayed,
        }


class InMemoryConversationStore:
    """Append-only synthetic store for contract probes."""

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or _now_utc
        self._conversations: tuple[ConversationRecord, ...] = ()
        self._messages: tuple[MessageRecord, ...] = ()
        self._intents: tuple[IntentRecord, ...] = ()
        self._drafts: tuple[DraftReplyRecord, ...] = ()
        self._handoffs: tuple[HandoffCase, ...] = ()
        self._unknown_quarantines: tuple[UnknownScopeQuarantineRecord, ...] = ()
        self._audit_events: tuple[SupportAuditEvent, ...] = ()
        self._conversation_scope_by_external_ref: dict[tuple[str, str], tuple[UUID, UUID, UUID]] = {}
        self._conversation_by_external_ref: dict[tuple[tuple[UUID, UUID, UUID], str, str], ConversationRecord] = {}
        self._fingerprint_by_message: dict[tuple[tuple[UUID, UUID, UUID], str, str], str] = {}
        self._receipt_by_message: dict[tuple[tuple[UUID, UUID, UUID], str, str], ConversationReceipt] = {}
        self._fingerprint_by_unknown: dict[tuple[str, str], str] = {}
        self._receipt_by_unknown: dict[tuple[str, str], ConversationReceipt] = {}

    @property
    def conversations(self) -> tuple[ConversationRecord, ...]:
        return self._conversations

    @property
    def messages(self) -> tuple[MessageRecord, ...]:
        return self._messages

    @property
    def intents(self) -> tuple[IntentRecord, ...]:
        return self._intents

    @property
    def drafts(self) -> tuple[DraftReplyRecord, ...]:
        return self._drafts

    @property
    def handoff_cases(self) -> tuple[HandoffCase, ...]:
        return self._handoffs

    @property
    def unknown_quarantines(self) -> tuple[UnknownScopeQuarantineRecord, ...]:
        return self._unknown_quarantines

    @property
    def audit_events(self) -> tuple[SupportAuditEvent, ...]:
        return self._audit_events

    def receive(self, command: InboundMessageCommand) -> ConversationReceipt:
        if not isinstance(command, InboundMessageCommand):
            raise _boundary("inbound_message_command_required")
        if command.scope_status is ScopeStatus.UNKNOWN:
            return self._receive_unknown_scope(command)
        return self._receive_known_scope(command)

    def snapshot_counts(self) -> dict[str, int]:
        return {
            "conversations": len(self._conversations),
            "messages": len(self._messages),
            "intents": len(self._intents),
            "drafts": len(self._drafts),
            "handoffs": len(self._handoffs),
            "unknown_quarantines": len(self._unknown_quarantines),
            "audit_events": len(self._audit_events),
        }

    def _receive_unknown_scope(self, command: InboundMessageCommand) -> ConversationReceipt:
        external_message_ref = command.external_message_ref
        key = (command.channel_ref, external_message_ref)
        existing_fingerprint = self._fingerprint_by_unknown.get(key)
        if existing_fingerprint is not None:
            if existing_fingerprint != command.input_fingerprint:
                raise _boundary("idempotency_conflict")
            return _replayed(self._receipt_by_unknown[key])

        quarantine = UnknownScopeQuarantineRecord(
            id=_stable_id(
                "unknown_quarantine",
                command.channel_ref,
                command.external_conversation_ref,
                command.external_message_ref,
                command.content_hash,
            ),
            channel_ref=command.channel_ref,
            external_conversation_ref=command.external_conversation_ref,
            external_message_ref=command.external_message_ref,
            content_hash=command.content_hash,
            content_ref=command.content_ref,
            reason=HandoffReason.UNKNOWN_SCOPE,
            status=HandoffStatus.OPEN,
            policy_version=command.policy_version,
            correlation_id="unknown_scope",
            retention_policy_ref=command.retention_policy_ref,
            redaction_ref="redaction:hash_only",
            received_at=command.received_at,
            received_by=command.received_by,
            created_at=self._now(),
            created_by=command.received_by,
        )
        event = self._append_event(
            event_kind="support_handoff_required",
            scope=None,
            target_ref="unknown_scope",
            result_code=HandoffReason.UNKNOWN_SCOPE.value,
            correlation_id=quarantine.correlation_id,
        )
        self._unknown_quarantines = (*self._unknown_quarantines, quarantine)
        receipt = ConversationReceipt(
            disposition=SupportDisposition.QUARANTINED,
            conversation=None,
            message=None,
            intent=None,
            draft=None,
            handoff=None,
            quarantine=quarantine,
            audit_event=event,
        )
        self._fingerprint_by_unknown[key] = command.input_fingerprint
        self._receipt_by_unknown[key] = receipt
        return receipt

    def _receive_known_scope(self, command: InboundMessageCommand) -> ConversationReceipt:
        if command.scope is None:
            raise _boundary("scope_required")
        scope = _require_scope(command.scope)
        scope_key = _scope_key(scope)
        external_conversation_ref = command.external_conversation_ref
        external_message_ref = command.external_message_ref
        external_conversation_key = (
            command.channel_ref,
            external_conversation_ref,
        )
        existing_scope = self._conversation_scope_by_external_ref.get(external_conversation_key)
        if existing_scope is not None and existing_scope != scope_key:
            raise _boundary("cross_scope_forbidden")

        message_key = (scope_key, command.channel_ref, external_message_ref)
        existing_fingerprint = self._fingerprint_by_message.get(message_key)
        if existing_fingerprint is not None:
            if existing_fingerprint != command.input_fingerprint:
                raise _boundary("idempotency_conflict")
            return _replayed(self._receipt_by_message[message_key])

        conversation = self._conversation_by_external_ref.get(
            (
                scope_key,
                command.channel_ref,
                external_conversation_ref,
            )
        )
        if conversation is None:
            conversation = self._create_conversation(command, scope, external_conversation_ref)
            self._conversations = (*self._conversations, conversation)
            self._conversation_scope_by_external_ref[external_conversation_key] = scope_key
            self._conversation_by_external_ref[
                (
                    scope_key,
                    command.channel_ref,
                    external_conversation_ref,
                )
            ] = conversation

        message = self._create_message(command, scope, conversation, external_message_ref)
        intent = self._create_intent(command, scope, message)
        disposition, draft, handoff = self._draft_or_handoff(command, scope, conversation, message)
        event = self._append_event(
            event_kind="support_message_recorded",
            scope=scope,
            target_ref=external_message_ref,
            result_code=disposition.value,
            correlation_id=scope.correlation_id,
        )
        self._messages = (*self._messages, message)
        self._intents = (*self._intents, intent)
        if draft is not None:
            self._drafts = (*self._drafts, draft)
        if handoff is not None:
            self._handoffs = (*self._handoffs, handoff)
        receipt = ConversationReceipt(
            disposition=disposition,
            conversation=conversation,
            message=message,
            intent=intent,
            draft=draft,
            handoff=handoff,
            quarantine=None,
            audit_event=event,
        )
        self._fingerprint_by_message[message_key] = command.input_fingerprint
        self._receipt_by_message[message_key] = receipt
        return receipt

    def _create_conversation(
        self,
        command: InboundMessageCommand,
        scope: ScopeRef,
        external_conversation_ref: str,
    ) -> ConversationRecord:
        status = (
            ConversationStatus.HANDOFF_REQUIRED
            if _requires_handoff(command)
            else ConversationStatus.ACTIVE
        )
        return ConversationRecord(
            id=_stable_id(
                "conversation",
                _scope_key(scope),
                command.channel_ref,
                external_conversation_ref,
            ),
            scope=scope,
            channel_ref=command.channel_ref,
            external_conversation_ref=external_conversation_ref,
            status=status,
            retention_policy_ref=command.retention_policy_ref,
            consent_ref=command.consent_ref,
            created_at=self._now(),
            created_by=command.received_by,
            correlation_id=scope.correlation_id,
        )

    def _create_message(
        self,
        command: InboundMessageCommand,
        scope: ScopeRef,
        conversation: ConversationRecord,
        external_message_ref: str,
    ) -> MessageRecord:
        return MessageRecord(
            id=_stable_id(
                "message",
                conversation.id,
                external_message_ref,
                command.content_hash,
            ),
            conversation_id=conversation.id,
            scope=scope,
            direction=MessageDirection.INBOUND,
            external_message_ref=external_message_ref,
            content_hash=command.content_hash,
            content_ref=command.content_ref,
            received_at=command.received_at,
            received_by=command.received_by,
            retention_policy_ref=command.retention_policy_ref,
            redaction_ref="redaction:hash_only",
            consent_ref=command.consent_ref,
            correlation_id=scope.correlation_id,
        )

    def _create_intent(
        self,
        command: InboundMessageCommand,
        scope: ScopeRef,
        message: MessageRecord,
    ) -> IntentRecord:
        return IntentRecord(
            id=_stable_id("intent", message.id, command.policy_version),
            message_id=message.id,
            scope=scope,
            intent_label=command.intent_label,
            risk_level=command.risk_level,
            policy_version=command.policy_version,
            model_ref="synthetic_classifier_v1",
            correlation_id=scope.correlation_id,
        )

    def _draft_or_handoff(
        self,
        command: InboundMessageCommand,
        scope: ScopeRef,
        conversation: ConversationRecord,
        message: MessageRecord,
    ) -> tuple[SupportDisposition, DraftReplyRecord | None, HandoffCase | None]:
        reason = _handoff_reason(command)
        if reason is not None:
            return (
                SupportDisposition.HANDOFF_REQUIRED,
                None,
                HandoffCase(
                    id=_stable_id("handoff", message.id, reason.value),
                    scope=scope,
                    conversation_id=conversation.id,
                    message_id=message.id,
                    reason=reason,
                    status=HandoffStatus.OPEN,
                    policy_version=command.policy_version,
                    correlation_id=scope.correlation_id,
                    created_at=self._now(),
                    created_by=command.received_by,
                ),
            )
        draft = DraftReplyRecord(
            id=_stable_id("draft", message.id, command.policy_version),
            message_id=message.id,
            scope=scope,
            draft_ref="ref:draft:" + message.id.hex,
            fact_version_set_hash=_digest(
                "pending_fact_refs",
                command.intent_label,
                command.policy_version,
            ),
            policy_version=command.policy_version,
            state=DraftState.DRAFT_ONLY,
            correlation_id=scope.correlation_id,
        )
        return SupportDisposition.DRAFT_READY, draft, None

    def _append_event(
        self,
        *,
        event_kind: str,
        scope: ScopeRef | None,
        target_ref: str,
        result_code: str,
        correlation_id: str,
    ) -> SupportAuditEvent:
        event = SupportAuditEvent(
            sequence=len(self._audit_events) + 1,
            event_kind=_require_identifier(event_kind, "event_kind_required"),
            scope=scope,
            target_ref=_require_identifier(target_ref, "target_ref_required"),
            result_code=_require_identifier(result_code, "result_code_required"),
            correlation_id=_require_identifier(correlation_id, "correlation_id_required"),
            occurred_at=self._now(),
        )
        self._audit_events = (*self._audit_events, event)
        return event


def _require_hash(value: object, code: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"^[0-9a-f]{64}$", value) is None:
        raise _boundary(code)
    return value


def _require_uuid(value: object, code: str) -> UUID:
    if not isinstance(value, UUID) or value.int == 0:
        raise _boundary(code)
    return value


def _require_synthetic_local(
    is_synthetic: object,
    external_execution_allowed: object,
) -> None:
    if is_synthetic is not True:
        raise _boundary("synthetic_input_required")
    if external_execution_allowed is not False:
        raise _boundary("external_execution_forbidden")


def _requires_handoff(command: InboundMessageCommand) -> bool:
    return _handoff_reason(command) is not None


def _handoff_reason(command: InboundMessageCommand) -> HandoffReason | None:
    if command.dnc_blocked:
        return HandoffReason.DNC_BLOCKED
    if command.personal_data_detected:
        return HandoffReason.PRIVACY_REVIEW_REQUIRED
    if command.risk_level is RiskLevel.HIGH:
        return HandoffReason.HIGH_RISK
    return None


def _replayed(receipt: ConversationReceipt) -> ConversationReceipt:
    return ConversationReceipt(
        disposition=receipt.disposition,
        conversation=receipt.conversation,
        message=receipt.message,
        intent=receipt.intent,
        draft=receipt.draft,
        handoff=receipt.handoff,
        quarantine=receipt.quarantine,
        audit_event=receipt.audit_event,
        replayed=True,
    )
