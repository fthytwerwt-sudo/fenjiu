"""P06-03 zero-send fake support adapter.

The adapter accepts synthetic inbound envelopes, maps external IDs to opaque
refs, and delegates conversation storage to the P06-01 contract. It has no
approved-send path, provider endpoint, SDK, webhook server, or network call.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import re
from typing import Callable

from core.contracts import ContractValidationError, ScopeRef
from modules.customer_service.contracts import (
    ConversationReceipt,
    InMemoryConversationStore,
    InboundMessageCommand,
    RiskLevel,
    ScopeStatus,
)
from modules.customer_service.takeover import SupportZeroSendProof


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_RAW_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)


class SupportAdapterBoundaryError(ContractValidationError):
    """Stable, value-free P06-03 support adapter boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _boundary(code: str) -> SupportAdapterBoundaryError:
    return SupportAdapterBoundaryError(code)


def _reject_sensitive_text(value: object) -> None:
    if not isinstance(value, str):
        return
    local_user_root = "/" + "Users" + "/"
    local_volume_root = "/" + "Volumes" + "/"
    if value.startswith("/") or "\\" in value or local_user_root in value or local_volume_root in value:
        raise _boundary("adapter_payload_forbidden")
    if _SENSITIVE.search(value) is not None:
        raise _boundary("adapter_payload_forbidden")


def _require_identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _boundary(code)
    _reject_sensitive_text(value)
    return value


def _require_raw_ref(value: object, code: str) -> str:
    if not isinstance(value, str) or _RAW_REF.fullmatch(value) is None:
        raise _boundary(code)
    _reject_sensitive_text(value)
    return value


def _opaque_ref(kind: str, value: str) -> str:
    digest = sha256(f"{kind}\x1f{value}".encode("utf-8")).hexdigest()[:32]
    return f"ref:{kind}:{digest}"


@dataclass(frozen=True)
class SupportInboundEnvelope:
    """Synthetic inbound support message envelope.

    Raw external identifiers are accepted only as input and converted to opaque
    refs before entering customer-service records.
    """

    scope: ScopeRef | None
    channel_ref: str
    raw_external_conversation_id: str
    raw_external_message_id: str
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
        if self.scope is not None and not isinstance(self.scope, ScopeRef):
            raise _boundary("scope_required")
        _require_identifier(self.channel_ref, "channel_ref_required")
        _require_raw_ref(self.raw_external_conversation_id, "external_conversation_ref_required")
        _require_raw_ref(self.raw_external_message_id, "external_message_ref_required")
        if not isinstance(self.received_at, datetime) or self.received_at.tzinfo is None:
            raise _boundary("received_at_required")
        _require_identifier(self.received_by, "received_by_required")
        if not isinstance(self.body_text, str) or not self.body_text:
            raise _boundary("message_body_required")
        _reject_sensitive_text(self.body_text)
        _require_identifier(self.content_ref, "content_ref_required")
        _require_identifier(self.intent_label, "intent_label_required")
        if not isinstance(self.risk_level, RiskLevel):
            raise _boundary("risk_level_required")
        _require_identifier(self.retention_policy_ref, "retention_policy_ref_required")
        _require_identifier(self.consent_ref, "consent_ref_required")
        if not isinstance(self.dnc_blocked, bool):
            raise _boundary("dnc_status_required")
        if not isinstance(self.personal_data_detected, bool):
            raise _boundary("personal_data_status_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_identifier(self.idempotency_key, "idempotency_key_required")

    def to_command(self) -> InboundMessageCommand:
        return InboundMessageCommand(
            scope=self.scope,
            scope_status=ScopeStatus.KNOWN if self.scope is not None else ScopeStatus.UNKNOWN,
            channel_ref=self.channel_ref,
            external_conversation_ref=_opaque_ref(
                "external_conversation",
                self.raw_external_conversation_id,
            ),
            external_message_ref=_opaque_ref("external_message", self.raw_external_message_id),
            received_at=self.received_at,
            received_by=self.received_by,
            body_text=self.body_text,
            content_ref=self.content_ref,
            intent_label=self.intent_label,
            risk_level=self.risk_level,
            retention_policy_ref=self.retention_policy_ref,
            consent_ref=self.consent_ref,
            dnc_blocked=self.dnc_blocked,
            personal_data_detected=self.personal_data_detected,
            policy_version=self.policy_version,
            idempotency_key=self.idempotency_key,
        )


class FakeSupportPort:
    """Receive-only fake support port with idempotent replay through P06-01."""

    __slots__ = ("_store",)

    def __init__(
        self,
        *,
        store: InMemoryConversationStore | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store or InMemoryConversationStore(now=now)

    @property
    def store(self) -> InMemoryConversationStore:
        return self._store

    def receive(self, envelope: SupportInboundEnvelope) -> ConversationReceipt:
        if not isinstance(envelope, SupportInboundEnvelope):
            raise _boundary("support_inbound_envelope_required")
        return self._store.receive(envelope.to_command())

    def zero_send_proof(self) -> SupportZeroSendProof:
        return SupportZeroSendProof(
            external_send_attempts=0,
            external_execution_allowed=False,
            send_approved_present=False,
            provider_endpoint_present=False,
        )


__all__ = [
    "FakeSupportPort",
    "SupportAdapterBoundaryError",
    "SupportInboundEnvelope",
]
