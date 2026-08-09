"""P04-03 append-only audit contracts.

Audit events are evidence, not logs. They carry only safe references, scoped
metadata, result codes, and a deterministic chain hash.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any

from core.contracts import ContractValidationError, ScopeRef


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)
_FORBIDDEN_METADATA_KEY = re.compile(
    r"(?i)(raw|content|body|message|payload|pii|personal|contact|email|phone|price|inventory|path|file|"
    r"secret|token|cookie|password|credential)"
)


class AuditBoundaryError(ContractValidationError):
    """Stable, value-free P04-03 audit boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _boundary(code: str) -> AuditBoundaryError:
    return AuditBoundaryError(code)


def _require_identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _boundary(code)
    _reject_sensitive_text(value)
    return value


def _require_hash_or_none(value: object, code: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise _boundary(code)
    return value


def _require_positive_int(value: object, code: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
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


def _reject_sensitive_text(value: object) -> None:
    if not isinstance(value, str):
        return
    if _SENSITIVE.search(value) is not None:
        raise _boundary("audit_payload_forbidden")
    local_user_root = "/" + "Users" + "/"
    local_volume_root = "/" + "Volumes" + "/"
    if value.startswith("/") or "\\" in value or local_user_root in value or local_volume_root in value:
        raise _boundary("audit_payload_forbidden")


def _safe_value(value: object) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, str):
        _reject_sensitive_text(value)
        if _IDENTIFIER.fullmatch(value) is None and _SHA256.fullmatch(value) is None:
            raise _boundary("audit_payload_forbidden")
        return value
    if isinstance(value, tuple):
        return tuple(_safe_value(item) for item in value)
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, Mapping):
        return _safe_metadata(value)
    raise _boundary("audit_payload_forbidden")


def _safe_metadata(metadata: Mapping[str, object] | None) -> dict[str, Any]:
    if metadata is None:
        return {}
    if not isinstance(metadata, Mapping):
        raise _boundary("audit_payload_forbidden")
    result: dict[str, Any] = {}
    for key, value in metadata.items():
        if not isinstance(key, str) or _IDENTIFIER.fullmatch(key) is None:
            raise _boundary("audit_payload_forbidden")
        if _FORBIDDEN_METADATA_KEY.search(key) is not None:
            raise _boundary("audit_payload_forbidden")
        result[key] = _safe_value(value)
    return result


def _canonical(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)


def _digest(*parts: object) -> str:
    return sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    event_ref: str
    event_kind: str
    actor_ref: str
    scope: ScopeRef
    command_ref: str
    target_ref: str
    policy_version: str
    subject_version: int
    correlation_id: str
    result_code: str
    occurred_at: datetime
    before_version_hash: str | None
    after_version_hash: str | None
    metadata: Mapping[str, object]
    previous_chain_hash: str
    chain_hash: str

    def __post_init__(self) -> None:
        _require_positive_int(self.sequence, "audit_sequence_required")
        _require_identifier(self.event_ref, "audit_event_ref_required")
        _require_identifier(self.event_kind, "audit_event_kind_required")
        _require_identifier(self.actor_ref, "actor_ref_required")
        scope = _require_scope(self.scope)
        _require_identifier(self.command_ref, "command_ref_required")
        _require_identifier(self.target_ref, "target_ref_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_positive_int(self.subject_version, "subject_version_required")
        _require_identifier(self.correlation_id, "correlation_id_required")
        if self.correlation_id != scope.correlation_id:
            raise _boundary("correlation_mismatch")
        _require_identifier(self.result_code, "result_code_required")
        _require_time(self.occurred_at, "audit_time_required")
        _require_hash_or_none(self.before_version_hash, "version_hash_required")
        _require_hash_or_none(self.after_version_hash, "version_hash_required")
        object.__setattr__(self, "metadata", _safe_metadata(self.metadata))
        if not isinstance(self.previous_chain_hash, str) or _SHA256.fullmatch(self.previous_chain_hash) is None:
            raise _boundary("audit_chain_hash_required")
        if not isinstance(self.chain_hash, str) or _SHA256.fullmatch(self.chain_hash) is None:
            raise _boundary("audit_chain_hash_required")

    def chain_material(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "event_kind": self.event_kind,
            "actor_ref": self.actor_ref,
            "scope": {
                "tenant_id": str(self.scope.tenant_id),
                "project_id": str(self.scope.project_id),
                "business_line_id": str(self.scope.business_line_id),
            },
            "command_ref": self.command_ref,
            "target_ref": self.target_ref,
            "policy_version": self.policy_version,
            "subject_version": self.subject_version,
            "correlation_id": self.correlation_id,
            "result_code": self.result_code,
            "occurred_at": self.occurred_at.isoformat(),
            "before_version_hash": self.before_version_hash,
            "after_version_hash": self.after_version_hash,
            "metadata": self.metadata,
            "previous_chain_hash": self.previous_chain_hash,
        }

    def safe_summary(self) -> dict[str, object]:
        result = self.chain_material()
        result["event_ref"] = self.event_ref
        result["chain_hash"] = self.chain_hash
        return result


class InMemoryAuditLog:
    """Append-only local audit sink used by P04 contract probes."""

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or _now_utc
        self._events: tuple[AuditEvent, ...] = ()

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return self._events

    def record(
        self,
        *,
        event_kind: str,
        actor_ref: str,
        scope: ScopeRef,
        command_ref: str,
        target_ref: str,
        policy_version: str,
        subject_version: int,
        result_code: str,
        before_version_hash: str | None = None,
        after_version_hash: str | None = None,
        metadata: Mapping[str, object] | None = None,
        occurred_at: datetime | None = None,
    ) -> AuditEvent:
        safe_metadata = _safe_metadata(metadata)
        sequence = len(self._events) + 1
        previous = self._events[-1].chain_hash if self._events else "0" * 64
        event_time = occurred_at or self._now()
        draft = {
            "sequence": sequence,
            "event_kind": _require_identifier(event_kind, "audit_event_kind_required"),
            "actor_ref": _require_identifier(actor_ref, "actor_ref_required"),
            "scope": _require_scope(scope),
            "command_ref": _require_identifier(command_ref, "command_ref_required"),
            "target_ref": _require_identifier(target_ref, "target_ref_required"),
            "policy_version": _require_identifier(policy_version, "policy_version_required"),
            "subject_version": _require_positive_int(subject_version, "subject_version_required"),
            "correlation_id": scope.correlation_id,
            "result_code": _require_identifier(result_code, "result_code_required"),
            "occurred_at": _require_time(event_time, "audit_time_required"),
            "before_version_hash": _require_hash_or_none(before_version_hash, "version_hash_required"),
            "after_version_hash": _require_hash_or_none(after_version_hash, "version_hash_required"),
            "metadata": safe_metadata,
            "previous_chain_hash": previous,
        }
        chain_hash = _digest(_canonical(_jsonable_chain_material(draft)))
        event = AuditEvent(
            event_ref="audit_event:" + chain_hash[:32],
            chain_hash=chain_hash,
            **draft,
        )
        self._events = (*self._events, event)
        return event

    def verify_chain(self) -> bool:
        previous = "0" * 64
        for expected_sequence, event in enumerate(self._events, start=1):
            if event.sequence != expected_sequence or event.previous_chain_hash != previous:
                return False
            if _digest(_canonical(event.chain_material())) != event.chain_hash:
                return False
            previous = event.chain_hash
        return True

    def snapshot_counts(self) -> dict[str, int]:
        return {"audit_events": len(self._events)}


def _jsonable_chain_material(payload: Mapping[str, object]) -> dict[str, object]:
    scope = payload["scope"]
    if not isinstance(scope, ScopeRef):
        raise _boundary("scope_required")
    return {
        "sequence": payload["sequence"],
        "event_kind": payload["event_kind"],
        "actor_ref": payload["actor_ref"],
        "scope": {
            "tenant_id": str(scope.tenant_id),
            "project_id": str(scope.project_id),
            "business_line_id": str(scope.business_line_id),
        },
        "command_ref": payload["command_ref"],
        "target_ref": payload["target_ref"],
        "policy_version": payload["policy_version"],
        "subject_version": payload["subject_version"],
        "correlation_id": payload["correlation_id"],
        "result_code": payload["result_code"],
        "occurred_at": payload["occurred_at"].isoformat()
        if isinstance(payload["occurred_at"], datetime)
        else payload["occurred_at"],
        "before_version_hash": payload["before_version_hash"],
        "after_version_hash": payload["after_version_hash"],
        "metadata": payload["metadata"],
        "previous_chain_hash": payload["previous_chain_hash"],
    }


class AuditRequiredCommandExecutor:
    """Run a mutating local command only after audit intent is persisted."""

    def __init__(
        self,
        *,
        audit_log: object,
        actor_ref: str,
        scope: ScopeRef,
        command_ref: str,
        target_ref: str,
        policy_version: str,
        subject_version: int,
    ) -> None:
        self._audit_log = audit_log
        self._actor_ref = _require_identifier(actor_ref, "actor_ref_required")
        self._scope = _require_scope(scope)
        self._command_ref = _require_identifier(command_ref, "command_ref_required")
        self._target_ref = _require_identifier(target_ref, "target_ref_required")
        self._policy_version = _require_identifier(policy_version, "policy_version_required")
        self._subject_version = _require_positive_int(subject_version, "subject_version_required")

    def run(self, mutation: Callable[[], Any], *, result_code: str) -> Any:
        if not callable(mutation):
            raise _boundary("mutation_required")
        self._record(result_code="started", event_kind="command_started")
        try:
            result = mutation()
        except Exception:
            self._record(result_code="failed", event_kind="command_failed")
            raise
        self._record(result_code=result_code, event_kind="command_succeeded")
        return result

    def _record(self, *, result_code: str, event_kind: str) -> None:
        record = getattr(self._audit_log, "record", None)
        if not callable(record):
            raise _boundary("audit_persistence_required")
        record(
            event_kind=event_kind,
            actor_ref=self._actor_ref,
            scope=self._scope,
            command_ref=self._command_ref,
            target_ref=self._target_ref,
            policy_version=self._policy_version,
            subject_version=self._subject_version,
            result_code=result_code,
        )
