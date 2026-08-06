"""Local command handler for policy-gated current-truth consumption."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from core.contracts import ContractValidationError, ScopeRef
from core.contracts.scope import _require_identifier, _require_uuid
from core.security.isolation import (
    AuditPolicyResult,
    InMemoryIsolationAuditLog,
    IsolationAction,
    IsolationPolicy,
    IsolationTarget,
    PolicyDeniedError,
)
from modules.truth_center.models import TruthEntityKind, TruthVersion
from modules.truth_center.repository import (
    InMemoryTruthRepository,
    TruthPolicyTarget,
)


@dataclass(frozen=True)
class TruthConsumerCommand:
    """Command envelope validated by the handler so invalid input is audited."""

    scope: object
    entity_kind: object
    subject_ref: object
    data_version_id: object
    read_at: object
    action: object
    actor_ref: object
    idempotency_key: object
    policy_decision_ref: object
    feature_flag_snapshot: object


class ScopedTruthConsumer:
    """Only application entrypoint for downstream current-truth reads."""

    def __init__(
        self,
        repository: InMemoryTruthRepository,
        policy: IsolationPolicy,
        audit_log: InMemoryIsolationAuditLog,
    ) -> None:
        self._repository = repository
        self._policy = policy
        self._audit_log = audit_log
        self._repository._bind_read_context(policy, audit_log)

    def execute(self, command: TruthConsumerCommand) -> TruthVersion:
        if not isinstance(command, TruthConsumerCommand):
            raise TypeError("truth_consumer_command_required")
        validation_code = self._validate_command(command)
        if validation_code is not None:
            self._deny(command, validation_code)
        assert isinstance(command.scope, ScopeRef)
        assert isinstance(command.entity_kind, TruthEntityKind)
        assert isinstance(command.subject_ref, str)
        assert isinstance(command.data_version_id, UUID)
        assert isinstance(command.read_at, datetime)
        assert isinstance(command.policy_decision_ref, str)

        try:
            target = self._repository.policy_target(
                command.scope,
                command.data_version_id,
            )
        except ContractValidationError as exc:
            self._deny(command, str(exc))
        if target is None:
            self._deny(command, "truth_target_not_found")
        assert isinstance(target, TruthPolicyTarget)
        if (
            target.entity_kind is not command.entity_kind
            or target.subject_ref != command.subject_ref
        ):
            self._deny(command, "truth_target_mismatch", target)

        evaluation = self._policy.evaluate(
            scope=command.scope,
            target=IsolationTarget(
                scope=target.scope,
                data_version_id=target.data_version_id,
                data_state=target.data_state,
                sensitivity=target.sensitivity,
                is_synthetic=target.is_synthetic,
            ),
            action=command.action,
            feature_flag_snapshot=command.feature_flag_snapshot,
            read_at=command.read_at,
            policy_decision_ref=command.policy_decision_ref,
        )
        if not evaluation.allowed or evaluation.grant is None:
            self._deny(
                command,
                evaluation.error_code or "policy_denied",
                target,
            )
        try:
            current = self._repository.current(
                evaluation.grant,
                command.entity_kind,
                command.subject_ref,
                actor_ref=command.actor_ref,
            )
        except ContractValidationError as exc:
            self._deny(command, str(exc), target)
        if current is None or current.version.id != command.data_version_id:
            self._deny(command, "truth_not_current", target)
        return current

    def _validate_command(self, command: TruthConsumerCommand) -> str | None:
        if not isinstance(command.scope, ScopeRef):
            return "scope_required"
        if not isinstance(command.entity_kind, TruthEntityKind):
            return "truth_entity_kind_required"
        try:
            _require_identifier(command.subject_ref, "truth_subject_ref_required")
            _require_uuid(command.data_version_id, "data_version_id_required")
            _require_identifier(command.actor_ref, "actor_ref_required")
            _require_identifier(command.idempotency_key, "idempotency_key_required")
            _require_identifier(
                command.policy_decision_ref,
                "policy_decision_ref_required",
            )
        except ContractValidationError as exc:
            return str(exc)
        if (
            not isinstance(command.read_at, datetime)
            or command.read_at.tzinfo is None
            or command.read_at.utcoffset() is None
        ):
            return "read_time_required"
        return None

    def _deny(
        self,
        command: TruthConsumerCommand,
        code: str,
        target: TruthPolicyTarget | None = None,
    ) -> None:
        scope = command.scope if isinstance(command.scope, ScopeRef) else None
        correlation_id = scope.correlation_id if scope is not None else "unscoped_request"
        action = (
            command.action.value
            if isinstance(command.action, IsolationAction)
            else "invalid_action"
        )
        actor_ref = self._safe_identifier(command.actor_ref, "invalid_actor")
        target_ref = self._safe_identifier(command.subject_ref, "invalid_target")
        policy_ref = self._safe_identifier(
            command.policy_decision_ref,
            "invalid_policy",
        )
        version_id = (
            command.data_version_id
            if isinstance(command.data_version_id, UUID)
            else None
        )
        event = self._audit_log.record(
            scope=scope,
            correlation_id=correlation_id,
            action=action,
            actor_ref=actor_ref,
            target_ref=target_ref,
            data_version_id=version_id,
            data_state=target.data_state if target is not None else None,
            sensitivity=target.sensitivity if target is not None else None,
            policy_decision_ref=policy_ref,
            policy_result=AuditPolicyResult.DENIED,
            error_code=code,
            external_execution_attempted=(
                isinstance(command.action, IsolationAction)
                and command.action is not IsolationAction.INTERNAL_TRUTH_READ
            ),
        )
        raise PolicyDeniedError(code, event)

    @staticmethod
    def _safe_identifier(value: object, fallback: str) -> str:
        try:
            _require_identifier(value, "invalid")
        except ContractValidationError:
            return fallback
        assert isinstance(value, str)
        return value
