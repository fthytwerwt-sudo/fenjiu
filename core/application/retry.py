"""P04-03 retry classification and dead-letter contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Callable

from core.contracts import ContractValidationError, ScopeRef


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)


class RetryBoundaryError(ContractValidationError):
    """Stable, value-free P04-03 retry boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class RetryEffect(str, Enum):
    INTERNAL_TRANSIENT = "internal_transient"
    INTERNAL_PERMANENT = "internal_permanent"
    EXTERNAL_SIDE_EFFECT = "external_side_effect"
    UNKNOWN_SIDE_EFFECT = "unknown_side_effect"
    BROKER_UNAVAILABLE = "broker_unavailable"


class RetryClass(str, Enum):
    AUTO_RETRY = "auto_retry"
    NO_RETRY = "no_retry"
    MANUAL_REVIEW = "manual_review"


class QueueDeliveryState(str, Enum):
    RETRY_SCHEDULED = "retry_scheduled"
    DEAD_LETTERED = "dead_lettered"
    MANUAL_QUEUE = "manual_queue"
    PENDING_MANUAL = "pending_manual"


def _boundary(code: str) -> RetryBoundaryError:
    return RetryBoundaryError(code)


def _reject_sensitive_text(value: object) -> None:
    if not isinstance(value, str):
        return
    if _SENSITIVE.search(value) is not None:
        raise _boundary("retry_payload_forbidden")
    local_user_root = "/" + "Users" + "/"
    local_volume_root = "/" + "Volumes" + "/"
    if value.startswith("/") or "\\" in value or local_user_root in value or local_volume_root in value:
        raise _boundary("retry_payload_forbidden")


def _require_identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _boundary(code)
    _reject_sensitive_text(value)
    return value


def _require_scope(value: object) -> ScopeRef:
    if not isinstance(value, ScopeRef):
        raise _boundary("scope_required")
    _require_identifier(value.correlation_id, "correlation_id_required")
    return value


def _require_attempt(value: object, code: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise _boundary(code)
    return value


def _require_time(value: object, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _boundary(code)
    return value


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class RetryDecision:
    scope: ScopeRef
    source_ref: str
    checkpoint_ref: str
    correlation_id: str
    effect: RetryEffect
    retry_class: RetryClass
    delivery_state: QueueDeliveryState
    attempt: int
    max_attempts: int
    error_code: str
    reason_code: str
    may_auto_retry: bool
    manual_required: bool
    decided_at: datetime

    def __post_init__(self) -> None:
        scope = _require_scope(self.scope)
        _require_identifier(self.source_ref, "source_ref_required")
        _require_identifier(self.checkpoint_ref, "checkpoint_ref_required")
        _require_identifier(self.correlation_id, "correlation_id_required")
        if self.correlation_id != scope.correlation_id:
            raise _boundary("correlation_mismatch")
        if not isinstance(self.effect, RetryEffect):
            raise _boundary("retry_effect_required")
        if not isinstance(self.retry_class, RetryClass):
            raise _boundary("retry_class_required")
        if not isinstance(self.delivery_state, QueueDeliveryState):
            raise _boundary("delivery_state_required")
        attempt = _require_attempt(self.attempt, "attempt_required")
        max_attempts = _require_attempt(self.max_attempts, "max_attempts_required")
        if attempt > max_attempts:
            raise _boundary("attempt_exceeds_max_attempts")
        _require_identifier(self.error_code, "error_code_required")
        _require_identifier(self.reason_code, "reason_code_required")
        if not isinstance(self.may_auto_retry, bool):
            raise _boundary("retry_flag_required")
        if not isinstance(self.manual_required, bool):
            raise _boundary("manual_flag_required")
        _require_time(self.decided_at, "decided_at_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "source_ref": self.source_ref,
            "checkpoint_ref": self.checkpoint_ref,
            "correlation_id": self.correlation_id,
            "effect": self.effect.value,
            "retry_class": self.retry_class.value,
            "delivery_state": self.delivery_state.value,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "error_code": self.error_code,
            "reason_code": self.reason_code,
            "may_auto_retry": self.may_auto_retry,
            "manual_required": self.manual_required,
        }


@dataclass(frozen=True)
class DeadLetterItem:
    source_ref: str
    checkpoint_ref: str
    correlation_id: str
    error_code: str
    reason_code: str
    attempts: int
    created_at: datetime

    def __post_init__(self) -> None:
        _require_identifier(self.source_ref, "source_ref_required")
        _require_identifier(self.checkpoint_ref, "checkpoint_ref_required")
        _require_identifier(self.correlation_id, "correlation_id_required")
        _require_identifier(self.error_code, "error_code_required")
        _require_identifier(self.reason_code, "reason_code_required")
        _require_attempt(self.attempts, "attempt_required")
        _require_time(self.created_at, "created_at_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "source_ref": self.source_ref,
            "checkpoint_ref": self.checkpoint_ref,
            "correlation_id": self.correlation_id,
            "error_code": self.error_code,
            "reason_code": self.reason_code,
            "attempts": self.attempts,
            "created_at": self.created_at.isoformat(),
        }


class RetryClassifier:
    """Classify retry safety without guessing external side-effect state."""

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or _now_utc

    def classify(
        self,
        *,
        scope: ScopeRef,
        source_ref: str,
        checkpoint_ref: str,
        effect: RetryEffect,
        attempt: int,
        max_attempts: int,
        error_code: str,
    ) -> RetryDecision:
        checked_scope = _require_scope(scope)
        checked_attempt = _require_attempt(attempt, "attempt_required")
        checked_max = _require_attempt(max_attempts, "max_attempts_required")
        if checked_attempt > checked_max:
            raise _boundary("attempt_exceeds_max_attempts")
        if not isinstance(effect, RetryEffect):
            raise _boundary("retry_effect_required")
        if effect is RetryEffect.INTERNAL_TRANSIENT and checked_attempt < checked_max:
            return self._decision(
                scope=checked_scope,
                source_ref=source_ref,
                checkpoint_ref=checkpoint_ref,
                effect=effect,
                retry_class=RetryClass.AUTO_RETRY,
                delivery_state=QueueDeliveryState.RETRY_SCHEDULED,
                attempt=checked_attempt,
                max_attempts=checked_max,
                error_code=error_code,
                reason_code="safe_retry_scheduled",
                may_auto_retry=True,
                manual_required=False,
            )
        if effect in {RetryEffect.INTERNAL_TRANSIENT, RetryEffect.INTERNAL_PERMANENT}:
            return self._decision(
                scope=checked_scope,
                source_ref=source_ref,
                checkpoint_ref=checkpoint_ref,
                effect=effect,
                retry_class=RetryClass.NO_RETRY,
                delivery_state=QueueDeliveryState.DEAD_LETTERED,
                attempt=checked_attempt,
                max_attempts=checked_max,
                error_code=error_code,
                reason_code="max_attempts_exhausted"
                if effect is RetryEffect.INTERNAL_TRANSIENT
                else "internal_permanent_dead_letter",
                may_auto_retry=False,
                manual_required=False,
            )
        if effect is RetryEffect.BROKER_UNAVAILABLE:
            return self._decision(
                scope=checked_scope,
                source_ref=source_ref,
                checkpoint_ref=checkpoint_ref,
                effect=effect,
                retry_class=RetryClass.MANUAL_REVIEW,
                delivery_state=QueueDeliveryState.PENDING_MANUAL,
                attempt=checked_attempt,
                max_attempts=checked_max,
                error_code=error_code,
                reason_code="broker_unavailable_pending_manual",
                may_auto_retry=False,
                manual_required=True,
            )
        return self._decision(
            scope=checked_scope,
            source_ref=source_ref,
            checkpoint_ref=checkpoint_ref,
            effect=effect,
            retry_class=RetryClass.MANUAL_REVIEW,
            delivery_state=QueueDeliveryState.MANUAL_QUEUE,
            attempt=checked_attempt,
            max_attempts=checked_max,
            error_code=error_code,
            reason_code="side_effect_manual_review",
            may_auto_retry=False,
            manual_required=True,
        )

    def _decision(
        self,
        *,
        scope: ScopeRef,
        source_ref: str,
        checkpoint_ref: str,
        effect: RetryEffect,
        retry_class: RetryClass,
        delivery_state: QueueDeliveryState,
        attempt: int,
        max_attempts: int,
        error_code: str,
        reason_code: str,
        may_auto_retry: bool,
        manual_required: bool,
    ) -> RetryDecision:
        return RetryDecision(
            scope=scope,
            source_ref=source_ref,
            checkpoint_ref=checkpoint_ref,
            correlation_id=scope.correlation_id,
            effect=effect,
            retry_class=retry_class,
            delivery_state=delivery_state,
            attempt=attempt,
            max_attempts=max_attempts,
            error_code=_require_identifier(error_code, "error_code_required"),
            reason_code=reason_code,
            may_auto_retry=may_auto_retry,
            manual_required=manual_required,
            decided_at=self._now(),
        )


class LocalDeadLetterQueue:
    """Visible local DLQ retaining only source, checkpoint, and correlation refs."""

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or _now_utc
        self._items: tuple[DeadLetterItem, ...] = ()

    @property
    def items(self) -> tuple[DeadLetterItem, ...]:
        return self._items

    def enqueue(self, decision: RetryDecision) -> DeadLetterItem:
        if not isinstance(decision, RetryDecision):
            raise _boundary("retry_decision_required")
        if decision.delivery_state is not QueueDeliveryState.DEAD_LETTERED:
            raise _boundary("dead_letter_decision_required")
        for item in self._items:
            if item.source_ref == decision.source_ref and item.correlation_id == decision.correlation_id:
                return item
        item = DeadLetterItem(
            source_ref=decision.source_ref,
            checkpoint_ref=decision.checkpoint_ref,
            correlation_id=decision.correlation_id,
            error_code=decision.error_code,
            reason_code=decision.reason_code,
            attempts=decision.attempt,
            created_at=self._now(),
        )
        self._items = (*self._items, item)
        return item
