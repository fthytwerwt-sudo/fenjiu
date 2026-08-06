"""Fail-closed local isolation policy and payload-free audit contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable
from uuid import UUID

from core.contracts import DataState, ScopeRef, Sensitivity
from core.contracts.access import (
    RepositoryAuditRecorder,
    RepositoryGrantVerifier,
    RepositoryReadGrant,
    _issue_repository_read_grant,
    validate_repository_read_grant,
)
from core.contracts.errors import ContractValidationError
from core.security.feature_flags import FailClosedFeatureFlags, FeatureFlagName


class IsolationAction(str, Enum):
    INTERNAL_TRUTH_READ = "internal_truth_read"
    EXTERNAL_SEND = "external_send"
    CONTENT_PUBLISH = "content_publish"
    PRICE_QUOTE = "price_quote"
    REFUND = "refund"
    ORDER = "order"
    PAYMENT = "payment"
    INVENTORY_WRITE = "inventory_write"
    REAL_CRAWL = "real_crawl"
    REAL_VIDEO_PROVIDER = "real_video_provider"


class AuditPolicyResult(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"


@dataclass(frozen=True)
class IsolationTarget:
    """Value-free metadata required for one access-policy decision."""

    scope: ScopeRef
    data_version_id: UUID
    data_state: DataState
    sensitivity: Sensitivity
    is_synthetic: bool


@dataclass(frozen=True)
class PolicyEvaluation:
    allowed: bool
    error_code: str | None
    grant: RepositoryReadGrant | None


@dataclass(frozen=True)
class IsolationAuditEvent:
    """Append-only audit result containing references, never truth payloads."""

    sequence: int
    recorded_at: datetime
    scope: ScopeRef | None
    correlation_id: str
    command_name: str
    action: str
    actor_ref: str
    target_ref: str
    data_version_id: UUID | None
    data_state: DataState | None
    sensitivity: Sensitivity | None
    policy_decision_ref: str
    policy_result: AuditPolicyResult
    error_code: str | None
    external_execution_attempted: bool


class PolicyDeniedError(Exception):
    """Stable denial code paired with the audit event that recorded it."""

    def __init__(self, code: str, audit_event: IsolationAuditEvent) -> None:
        super().__init__(code)
        self.code = code
        self.audit_event = audit_event


class InMemoryIsolationAuditLog(RepositoryAuditRecorder):
    """Local append-only audit probe; no update or delete surface exists."""

    __slots__ = ("__clock", "__events")

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self.__clock = clock or (lambda: datetime.now(timezone.utc))
        self.__events: tuple[IsolationAuditEvent, ...] = ()

    @property
    def events(self) -> tuple[IsolationAuditEvent, ...]:
        return self.__events

    def record(
        self,
        *,
        scope: ScopeRef | None,
        correlation_id: str,
        action: str,
        actor_ref: str,
        target_ref: str,
        data_version_id: UUID | None,
        data_state: DataState | None,
        sensitivity: Sensitivity | None,
        policy_decision_ref: str,
        policy_result: AuditPolicyResult,
        error_code: str | None,
        external_execution_attempted: bool,
    ) -> IsolationAuditEvent:
        event = IsolationAuditEvent(
            sequence=len(self.__events) + 1,
            recorded_at=self.__clock(),
            scope=scope,
            correlation_id=correlation_id,
            command_name="consume_current_truth",
            action=action,
            actor_ref=actor_ref,
            target_ref=target_ref,
            data_version_id=data_version_id,
            data_state=data_state,
            sensitivity=sensitivity,
            policy_decision_ref=policy_decision_ref,
            policy_result=policy_result,
            error_code=error_code,
            external_execution_attempted=external_execution_attempted,
        )
        self.__events = (*self.__events, event)
        return event

    def record_repository_read_allowed(
        self,
        *,
        scope: ScopeRef,
        actor_ref: str,
        target_ref: str,
        data_version_id: UUID,
        data_state: DataState,
        sensitivity: Sensitivity,
        policy_decision_ref: str,
    ) -> IsolationAuditEvent:
        """Append the mandatory audit event before returning current truth."""

        return self.record(
            scope=scope,
            correlation_id=scope.correlation_id,
            action=IsolationAction.INTERNAL_TRUTH_READ.value,
            actor_ref=actor_ref,
            target_ref=target_ref,
            data_version_id=data_version_id,
            data_state=data_state,
            sensitivity=sensitivity,
            policy_decision_ref=policy_decision_ref,
            policy_result=AuditPolicyResult.ALLOWED,
            error_code=None,
            external_execution_attempted=False,
        )


def disabled_feature_flag_snapshot() -> tuple[tuple[str, bool], ...]:
    """Return a complete immutable snapshot of the static disabled flags."""

    snapshot = FailClosedFeatureFlags().snapshot()
    return tuple(sorted(snapshot.items()))


class IsolationPolicy(RepositoryGrantVerifier):
    """Issue repository grants only for complete local internal reads."""

    _expected_flags = frozenset(flag.value for flag in FeatureFlagName)
    _allowed_sensitivities = frozenset({Sensitivity.INTERNAL})
    __slots__ = ("__issued_grants",)

    def __init__(self) -> None:
        self.__issued_grants: dict[UUID, RepositoryReadGrant] = {}

    def evaluate(
        self,
        *,
        scope: ScopeRef,
        target: IsolationTarget,
        action: object,
        feature_flag_snapshot: object,
        read_at: datetime,
        policy_decision_ref: str,
    ) -> PolicyEvaluation:
        flag_error = self._validate_feature_flags(feature_flag_snapshot)
        if flag_error is not None:
            return PolicyEvaluation(False, flag_error, None)
        if not isinstance(action, IsolationAction):
            return PolicyEvaluation(False, "isolation_action_invalid", None)
        if target.scope != scope:
            return PolicyEvaluation(False, "cross_scope_forbidden", None)
        if action is not IsolationAction.INTERNAL_TRUTH_READ:
            if target.is_synthetic or target.data_state in {
                DataState.FIXTURE,
                DataState.MOCK,
            }:
                return PolicyEvaluation(
                    False,
                    "fixture_external_action_forbidden",
                    None,
                )
            return PolicyEvaluation(False, "external_action_disabled", None)
        if target.data_state is not DataState.APPROVED or target.is_synthetic:
            return PolicyEvaluation(False, "truth_not_current", None)
        if target.sensitivity not in self._allowed_sensitivities:
            return PolicyEvaluation(False, "sensitivity_forbidden", None)
        grant = _issue_repository_read_grant(
            scope=scope,
            data_version_id=target.data_version_id,
            read_at=read_at,
            policy_decision_ref=policy_decision_ref,
            data_state=target.data_state,
            sensitivity=target.sensitivity,
            is_synthetic=target.is_synthetic,
        )
        self.__issued_grants[grant.grant_id] = grant
        return PolicyEvaluation(True, None, grant)

    def assert_repository_grant(self, grant: object) -> RepositoryReadGrant:
        """Reject grants not issued by this exact policy instance."""

        validated = validate_repository_read_grant(grant)
        registered = self.__issued_grants.get(validated.grant_id)
        if registered is not validated:
            raise ContractValidationError("repository_read_grant_not_issued")
        return validated

    def _validate_feature_flags(self, snapshot: object) -> str | None:
        if not isinstance(snapshot, tuple):
            return "feature_flag_snapshot_invalid"
        normalized: dict[str, bool] = {}
        for item in snapshot:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not isinstance(item[1], bool)
                or item[0] in normalized
            ):
                return "feature_flag_snapshot_invalid"
            normalized[item[0]] = item[1]
        if frozenset(normalized) != self._expected_flags:
            return "feature_flag_snapshot_invalid"
        if any(normalized.values()):
            return "external_flags_must_remain_false"
        return None
