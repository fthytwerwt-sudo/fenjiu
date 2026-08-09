"""P04-02 scoped RBAC, approval, and action-policy contracts.

The contracts are stdlib-only and local. They do not create real users,
permissions, external adapters, or business authority.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from hashlib import sha256
import re
from typing import Callable

from core.contracts import ContractValidationError, DataState, ScopeRef
from core.security.feature_flags import FeatureFlagName


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)


class ActionPolicyError(ContractValidationError):
    """Stable, value-free P04-02 policy boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ActorRole(str, Enum):
    SYSTEM_WORKER = "system_worker"
    DATA_REVIEWER = "data_reviewer"
    CONTENT_REVIEWER = "content_reviewer"
    SUPPORT_AGENT = "support_agent"
    PROJECT_OWNER = "project_owner"
    AUDITOR = "auditor"


class ActionName(str, Enum):
    RUN_INTERNAL_WORKFLOW = "run_internal_workflow"
    APPROVE_DATA_CANDIDATE = "approve_data_candidate"
    EXPORT_CONTENT_INTERNAL = "export_content_internal"
    APPLY_SUPPORT_DRAFT = "apply_support_draft"
    APPROVE_SUPPORT_DRAFT = "approve_support_draft"
    APPROVE_OUTREACH_DRAFT = "approve_outreach_draft"
    CONFIGURE_SAFE_FLAG = "configure_safe_flag"
    READ_AUDIT = "read_audit"
    EXTERNAL_SEND = "external_send"
    CONTENT_PUBLISH = "content_publish"
    PRICE_QUOTE = "price_quote"
    PAYMENT = "payment"
    ORDER = "order"
    REFUND = "refund"
    INVENTORY_WRITE = "inventory_write"


class ApprovalState(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"
    EXPIRED = "expired"


class ApprovalAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"
    EXPIRE = "expire"


class Environment(str, Enum):
    LOCAL = "local"
    TEST = "test"
    PRODUCTION = "production"


class PolicyPhase(str, Enum):
    REQUEST = "request"
    DECISION = "decision"
    EXECUTION = "execution"


def _boundary(code: str) -> ActionPolicyError:
    return ActionPolicyError(code)


def _reject_sensitive_text(value: object) -> None:
    if isinstance(value, str) and _SENSITIVE.search(value) is not None:
        raise _boundary("sensitive_metadata_forbidden")


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


def _require_time(value: object, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _boundary(code)
    return value


def _require_positive_version(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise _boundary("subject_version_required")
    return value


def _require_ttl(value: object) -> timedelta:
    if not isinstance(value, timedelta) or value.total_seconds() <= 0:
        raise _boundary("fact_ttl_required")
    return value


def _normalize_role(value: object) -> ActorRole | object:
    if isinstance(value, ActorRole):
        return value
    if isinstance(value, str):
        try:
            return ActorRole(value)
        except ValueError:
            return value
    return value


def _normalize_action(value: object) -> ActionName | object:
    if isinstance(value, ActionName):
        return value
    if isinstance(value, str):
        try:
            return ActionName(value)
        except ValueError:
            return value
    return value


def _digest(*parts: object) -> str:
    return sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PolicyActor:
    actor_ref: str
    role: ActorRole | str
    scope: ScopeRef

    def __post_init__(self) -> None:
        _require_identifier(self.actor_ref, "actor_ref_required")
        _require_scope(self.scope)
        object.__setattr__(self, "role", _normalize_role(self.role))


@dataclass(frozen=True)
class PolicyRequest:
    actor: PolicyActor
    action: ActionName | str
    phase: PolicyPhase
    scope: ScopeRef
    target_ref: str
    data_state: DataState
    approval_state: ApprovalState
    fact_observed_at: datetime
    fact_ttl: timedelta
    required_evidence_refs: tuple[str, ...]
    feature_flag_snapshot: tuple[tuple[str, bool], ...]
    dnc_blocked: bool
    consent_granted: bool
    environment: Environment
    evaluated_at: datetime
    policy_version: str
    correlation_id: str
    subject_version: int

    def __post_init__(self) -> None:
        if not isinstance(self.actor, PolicyActor):
            raise _boundary("actor_required")
        _require_scope(self.scope)
        object.__setattr__(self, "action", _normalize_action(self.action))
        if not isinstance(self.phase, PolicyPhase):
            raise _boundary("policy_phase_required")
        _require_identifier(self.target_ref, "target_ref_required")
        if not isinstance(self.data_state, DataState):
            raise _boundary("data_state_required")
        if not isinstance(self.approval_state, ApprovalState):
            raise _boundary("approval_state_required")
        _require_time(self.fact_observed_at, "fact_observed_at_required")
        _require_ttl(self.fact_ttl)
        if not isinstance(self.required_evidence_refs, tuple):
            raise _boundary("required_evidence_missing")
        for evidence_ref in self.required_evidence_refs:
            _require_identifier(evidence_ref, "required_evidence_missing")
        self._validate_flags_shape(self.feature_flag_snapshot)
        if not isinstance(self.dnc_blocked, bool):
            raise _boundary("dnc_status_required")
        if not isinstance(self.consent_granted, bool):
            raise _boundary("consent_status_required")
        if not isinstance(self.environment, Environment):
            raise _boundary("environment_required")
        _require_time(self.evaluated_at, "evaluated_at_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_identifier(self.correlation_id, "correlation_id_required")
        if self.correlation_id != self.scope.correlation_id:
            raise _boundary("correlation_mismatch")
        _require_positive_version(self.subject_version)

    @staticmethod
    def _validate_flags_shape(snapshot: object) -> None:
        if not isinstance(snapshot, tuple):
            raise _boundary("feature_flag_snapshot_invalid")
        seen: set[str] = set()
        expected = {flag.value for flag in FeatureFlagName}
        for item in snapshot:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not isinstance(item[1], bool)
                or item[0] in seen
            ):
                raise _boundary("feature_flag_snapshot_invalid")
            seen.add(item[0])
        if seen != expected:
            raise _boundary("feature_flag_snapshot_invalid")


@dataclass(frozen=True)
class PolicyDecision:
    decision_ref: str
    allowed: bool
    policy_result: str
    error_code: str | None
    scope: ScopeRef
    action: ActionName | str
    phase: PolicyPhase
    actor_ref: str
    actor_role: str
    target_ref: str
    correlation_id: str
    policy_version: str
    evaluated_at: datetime
    evidence_refs: tuple[str, ...]
    subject_version: int
    external_execution_attempted: bool

    def safe_summary(self) -> dict[str, object]:
        return {
            "decision_ref": self.decision_ref,
            "allowed": self.allowed,
            "policy_result": self.policy_result,
            "error_code": self.error_code,
            "action": self.action.value if isinstance(self.action, ActionName) else str(self.action),
            "phase": self.phase.value,
            "actor_ref": self.actor_ref,
            "actor_role": self.actor_role,
            "target_ref": self.target_ref,
            "correlation_id": self.correlation_id,
            "policy_version": self.policy_version,
            "subject_version": self.subject_version,
            "external_execution_attempted": self.external_execution_attempted,
        }


@dataclass(frozen=True)
class _ActionContract:
    allowed_roles: frozenset[ActorRole]
    request_roles: frozenset[ActorRole]
    allowed_data_states: frozenset[DataState]
    requires_approval: bool
    required_flag: FeatureFlagName | None = None
    forbidden_external: bool = False


_DIRECT_ROLE_ACTIONS: dict[ActorRole, tuple[ActionName, ...]] = {
    ActorRole.SYSTEM_WORKER: (ActionName.RUN_INTERNAL_WORKFLOW,),
    ActorRole.DATA_REVIEWER: (ActionName.APPROVE_DATA_CANDIDATE,),
    ActorRole.CONTENT_REVIEWER: (ActionName.EXPORT_CONTENT_INTERNAL,),
    ActorRole.SUPPORT_AGENT: (
        ActionName.APPLY_SUPPORT_DRAFT,
        ActionName.APPROVE_SUPPORT_DRAFT,
        ActionName.APPROVE_OUTREACH_DRAFT,
    ),
    ActorRole.PROJECT_OWNER: (ActionName.CONFIGURE_SAFE_FLAG,),
    ActorRole.AUDITOR: (ActionName.READ_AUDIT,),
}

_REVIEW_REQUEST_ROLES = frozenset(
    {
        ActorRole.SYSTEM_WORKER,
        ActorRole.DATA_REVIEWER,
        ActorRole.CONTENT_REVIEWER,
        ActorRole.SUPPORT_AGENT,
        ActorRole.PROJECT_OWNER,
    }
)

_ACTION_CONTRACTS: dict[ActionName, _ActionContract] = {
    ActionName.RUN_INTERNAL_WORKFLOW: _ActionContract(
        allowed_roles=frozenset({ActorRole.SYSTEM_WORKER}),
        request_roles=frozenset({ActorRole.SYSTEM_WORKER}),
        allowed_data_states=frozenset(
            {DataState.FIXTURE, DataState.MOCK, DataState.STAGING, DataState.APPROVED}
        ),
        requires_approval=False,
    ),
    ActionName.APPROVE_DATA_CANDIDATE: _ActionContract(
        allowed_roles=frozenset({ActorRole.DATA_REVIEWER}),
        request_roles=_REVIEW_REQUEST_ROLES,
        allowed_data_states=frozenset({DataState.STAGING}),
        requires_approval=True,
    ),
    ActionName.EXPORT_CONTENT_INTERNAL: _ActionContract(
        allowed_roles=frozenset({ActorRole.CONTENT_REVIEWER}),
        request_roles=_REVIEW_REQUEST_ROLES,
        allowed_data_states=frozenset({DataState.APPROVED}),
        requires_approval=True,
    ),
    ActionName.APPLY_SUPPORT_DRAFT: _ActionContract(
        allowed_roles=frozenset({ActorRole.SUPPORT_AGENT}),
        request_roles=_REVIEW_REQUEST_ROLES,
        allowed_data_states=frozenset({DataState.APPROVED}),
        requires_approval=True,
        required_flag=FeatureFlagName.EXTERNAL_SEND,
    ),
    ActionName.APPROVE_SUPPORT_DRAFT: _ActionContract(
        allowed_roles=frozenset({ActorRole.SUPPORT_AGENT}),
        request_roles=frozenset({ActorRole.SYSTEM_WORKER, ActorRole.SUPPORT_AGENT}),
        allowed_data_states=frozenset({DataState.FIXTURE}),
        requires_approval=True,
    ),
    ActionName.APPROVE_OUTREACH_DRAFT: _ActionContract(
        allowed_roles=frozenset({ActorRole.SUPPORT_AGENT}),
        request_roles=frozenset({ActorRole.SYSTEM_WORKER, ActorRole.SUPPORT_AGENT}),
        allowed_data_states=frozenset({DataState.FIXTURE}),
        requires_approval=True,
    ),
    ActionName.CONFIGURE_SAFE_FLAG: _ActionContract(
        allowed_roles=frozenset({ActorRole.PROJECT_OWNER}),
        request_roles=frozenset({ActorRole.PROJECT_OWNER}),
        allowed_data_states=frozenset({DataState.APPROVED}),
        requires_approval=False,
    ),
    ActionName.READ_AUDIT: _ActionContract(
        allowed_roles=frozenset({ActorRole.AUDITOR}),
        request_roles=frozenset({ActorRole.AUDITOR}),
        allowed_data_states=frozenset(
            {DataState.FIXTURE, DataState.MOCK, DataState.STAGING, DataState.APPROVED}
        ),
        requires_approval=False,
    ),
}

for _forbidden_action in (
    ActionName.EXTERNAL_SEND,
    ActionName.CONTENT_PUBLISH,
    ActionName.PRICE_QUOTE,
    ActionName.PAYMENT,
    ActionName.ORDER,
    ActionName.REFUND,
    ActionName.INVENTORY_WRITE,
):
    _ACTION_CONTRACTS[_forbidden_action] = _ActionContract(
        allowed_roles=frozenset(),
        request_roles=frozenset(),
        allowed_data_states=frozenset({DataState.APPROVED}),
        requires_approval=True,
        forbidden_external=True,
    )


class ActionPolicy:
    """Evaluate scoped action requests with fail-closed local policy."""

    __slots__ = ()

    def role_action_matrix(self) -> dict[str, tuple[str, ...]]:
        return {
            role.value: tuple(action.value for action in actions)
            for role, actions in _DIRECT_ROLE_ACTIONS.items()
        }

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        if not isinstance(request, PolicyRequest):
            raise _boundary("policy_request_required")
        actor_role = request.actor.role
        action = request.action
        if not isinstance(actor_role, ActorRole):
            return self._decision(request, False, "actor_role_unknown")
        if not isinstance(action, ActionName) or action not in _ACTION_CONTRACTS:
            return self._decision(request, False, "action_unknown")
        contract = _ACTION_CONTRACTS[action]
        if request.actor.scope != request.scope:
            return self._decision(request, False, "cross_scope_forbidden")
        if contract.forbidden_external:
            return self._decision(
                request,
                False,
                "external_action_forbidden",
                external_execution_attempted=True,
            )
        if request.environment not in {Environment.LOCAL, Environment.TEST}:
            return self._decision(request, False, "environment_forbidden")
        if request.phase is PolicyPhase.REQUEST:
            if actor_role not in contract.request_roles:
                return self._decision(request, False, "role_not_permitted")
        elif request.phase in {PolicyPhase.DECISION, PolicyPhase.EXECUTION}:
            if actor_role not in contract.allowed_roles:
                return self._decision(request, False, "role_not_permitted")
        else:
            return self._decision(request, False, "policy_phase_required")
        if not request.required_evidence_refs:
            return self._decision(request, False, "required_evidence_missing")
        if request.data_state not in contract.allowed_data_states:
            if contract.allowed_data_states == frozenset({DataState.APPROVED}):
                return self._decision(request, False, "data_state_not_approved")
            return self._decision(request, False, "data_state_not_allowed")
        if request.fact_observed_at + request.fact_ttl < request.evaluated_at:
            return self._decision(request, False, "fact_stale")
        if request.dnc_blocked:
            return self._decision(request, False, "dnc_blocked")
        if not request.consent_granted:
            return self._decision(request, False, "consent_required")
        if contract.required_flag is not None:
            flags = dict(request.feature_flag_snapshot)
            if flags.get(contract.required_flag.value) is not True:
                return self._decision(request, False, "feature_flag_disabled")
        if contract.requires_approval:
            if request.phase is PolicyPhase.REQUEST and request.approval_state is not ApprovalState.PENDING:
                return self._decision(request, False, "approval_state_invalid")
            if request.phase is PolicyPhase.EXECUTION and request.approval_state is not ApprovalState.APPROVED:
                return self._decision(request, False, "approval_required")
        return self._decision(request, True, None)

    @staticmethod
    def _decision(
        request: PolicyRequest,
        allowed: bool,
        error_code: str | None,
        *,
        external_execution_attempted: bool = False,
    ) -> PolicyDecision:
        action_value = request.action.value if isinstance(request.action, ActionName) else str(request.action)
        actor_role = request.actor.role.value if isinstance(request.actor.role, ActorRole) else str(request.actor.role)
        decision_ref = "policy_decision:" + _digest(
            request.scope.tenant_id,
            request.scope.project_id,
            request.scope.business_line_id,
            request.correlation_id,
            action_value,
            request.phase.value,
            request.actor.actor_ref,
            actor_role,
            request.target_ref,
            request.policy_version,
            request.subject_version,
            error_code or "allowed",
        )[:32]
        return PolicyDecision(
            decision_ref=decision_ref,
            allowed=allowed,
            policy_result="allowed" if allowed else "denied",
            error_code=error_code,
            scope=request.scope,
            action=request.action,
            phase=request.phase,
            actor_ref=request.actor.actor_ref,
            actor_role=actor_role,
            target_ref=request.target_ref,
            correlation_id=request.correlation_id,
            policy_version=request.policy_version,
            evaluated_at=request.evaluated_at,
            evidence_refs=request.required_evidence_refs,
            subject_version=request.subject_version,
            external_execution_attempted=external_execution_attempted,
        )


@dataclass(frozen=True)
class ActionApprovalRequest:
    id: str
    scope: ScopeRef
    action: ActionName
    target_ref: str
    creator_actor_ref: str
    state: ApprovalState
    requested_at: datetime
    expires_at: datetime
    policy_version: str
    evidence_refs: tuple[str, ...]
    subject_version: int
    correlation_id: str
    idempotency_key: str
    request_policy_decision_ref: str

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": self.id,
            "action": self.action.value,
            "target_ref": self.target_ref,
            "creator_actor_ref": self.creator_actor_ref,
            "state": self.state.value,
            "policy_version": self.policy_version,
            "subject_version": self.subject_version,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True)
class ActionApprovalDecision:
    id: str
    request_id: str
    action: ApprovalAction
    scope: ScopeRef
    actor_ref: str
    decided_at: datetime
    evidence_ref: str
    policy_version: str
    subject_version: int
    correlation_id: str
    idempotency_key: str
    policy_decision_ref: str
    revision_ref: str | None = None

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": self.id,
            "request_id": self.request_id,
            "action": self.action.value,
            "actor_ref": self.actor_ref,
            "evidence_ref": self.evidence_ref,
            "policy_version": self.policy_version,
            "subject_version": self.subject_version,
            "correlation_id": self.correlation_id,
            "policy_decision_ref": self.policy_decision_ref,
            "revision_ref": self.revision_ref,
        }


@dataclass(frozen=True)
class ActionApprovalAuditEvent:
    sequence: int
    event_kind: str
    request_id: str | None
    decision_id: str | None
    actor_ref: str
    scope: ScopeRef
    action: str
    target_ref: str
    correlation_id: str
    policy_version: str
    evidence_ref: str | None
    subject_version: int
    occurred_at: datetime
    policy_decision_ref: str
    error_code: str | None = None

    def safe_summary(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "event_kind": self.event_kind,
            "request_id": self.request_id,
            "decision_id": self.decision_id,
            "actor_ref": self.actor_ref,
            "action": self.action,
            "target_ref": self.target_ref,
            "correlation_id": self.correlation_id,
            "policy_version": self.policy_version,
            "evidence_ref": self.evidence_ref,
            "subject_version": self.subject_version,
            "policy_decision_ref": self.policy_decision_ref,
            "error_code": self.error_code,
        }


class ActionApprovalService:
    """Append-only local approval flow for action-policy probes."""

    __slots__ = (
        "_audit_events",
        "_decision_by_idempotency",
        "_decision_by_request",
        "_decisions",
        "_fingerprint_by_idempotency",
        "_now",
        "_policy",
        "_request_by_id",
        "_request_by_idempotency",
        "_request_policy",
        "_request_state",
        "_requests",
    )

    def __init__(
        self,
        *,
        policy: ActionPolicy | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._policy = policy or ActionPolicy()
        self._now = now
        self._requests: tuple[ActionApprovalRequest, ...] = ()
        self._request_by_id: dict[str, ActionApprovalRequest] = {}
        self._request_by_idempotency: dict[str, ActionApprovalRequest] = {}
        self._fingerprint_by_idempotency: dict[str, str] = {}
        self._request_policy: dict[str, PolicyRequest] = {}
        self._request_state: dict[str, ApprovalState] = {}
        self._decisions: tuple[ActionApprovalDecision, ...] = ()
        self._decision_by_idempotency: dict[str, ActionApprovalDecision] = {}
        self._decision_by_request: dict[str, ActionApprovalDecision] = {}
        self._audit_events: tuple[ActionApprovalAuditEvent, ...] = ()

    @property
    def requests(self) -> tuple[ActionApprovalRequest, ...]:
        return self._requests

    @property
    def decisions(self) -> tuple[ActionApprovalDecision, ...]:
        return self._decisions

    @property
    def audit_events(self) -> tuple[ActionApprovalAuditEvent, ...]:
        return self._audit_events

    def request_approval(
        self,
        policy_request: PolicyRequest,
        *,
        idempotency_key: str,
        creator_actor_ref: str,
        expires_at: datetime,
    ) -> ActionApprovalRequest:
        key = _require_identifier(idempotency_key, "idempotency_key_required")
        creator = _require_identifier(creator_actor_ref, "actor_ref_required")
        expires = _require_time(expires_at, "expires_at_required")
        now = self._current_time(policy_request.evaluated_at)
        if expires <= now:
            raise _boundary("approval_request_expired")
        if policy_request.phase is not PolicyPhase.REQUEST:
            raise _boundary("policy_phase_required")
        fingerprint = self._request_fingerprint(policy_request, creator, expires)
        existing = self._request_by_idempotency.get(key)
        if existing is not None:
            if self._fingerprint_by_idempotency[key] != fingerprint:
                raise _boundary("idempotency_conflict")
            return existing
        evaluation = self._policy.evaluate(policy_request)
        if not evaluation.allowed:
            raise _boundary(evaluation.error_code or "policy_denied")
        request_id = "approval_request:" + _digest(policy_request.scope, key)[:32]
        request = ActionApprovalRequest(
            id=request_id,
            scope=policy_request.scope,
            action=policy_request.action,
            target_ref=policy_request.target_ref,
            creator_actor_ref=creator,
            state=ApprovalState.PENDING,
            requested_at=now,
            expires_at=expires,
            policy_version=policy_request.policy_version,
            evidence_refs=policy_request.required_evidence_refs,
            subject_version=policy_request.subject_version,
            correlation_id=policy_request.correlation_id,
            idempotency_key=key,
            request_policy_decision_ref=evaluation.decision_ref,
        )
        self._requests = (*self._requests, request)
        self._request_by_id[request.id] = request
        self._request_by_idempotency[key] = request
        self._fingerprint_by_idempotency[key] = fingerprint
        self._request_policy[request.id] = policy_request
        self._request_state[request.id] = ApprovalState.PENDING
        self._append_audit(
            event_kind="approval_request_created",
            request_id=request.id,
            decision_id=None,
            actor_ref=creator,
            request=request,
            evidence_ref=None,
            policy_decision_ref=evaluation.decision_ref,
            occurred_at=now,
        )
        return request

    def decide(
        self,
        request_id: str,
        *,
        action: ApprovalAction,
        reviewer: PolicyActor,
        evidence_ref: str,
        idempotency_key: str,
        revision_ref: str | None = None,
    ) -> ActionApprovalDecision:
        normalized_request_id = _require_identifier(request_id, "approval_request_id_required")
        key = _require_identifier(idempotency_key, "idempotency_key_required")
        evidence = _require_identifier(evidence_ref, "approval_evidence_ref_required")
        if not isinstance(action, ApprovalAction) or action is ApprovalAction.EXPIRE:
            raise _boundary("approval_action_required")
        if not isinstance(reviewer, PolicyActor):
            raise _boundary("actor_required")
        if action is ApprovalAction.REVISE and revision_ref is None:
            raise _boundary("revision_ref_required")
        if revision_ref is not None:
            _require_identifier(revision_ref, "revision_ref_required")
        existing = self._decision_by_idempotency.get(key)
        if existing is not None:
            self._assert_same_decision(existing, normalized_request_id, action, reviewer, evidence, revision_ref)
            return existing
        request = self._pending_request(normalized_request_id)
        if self._current_time() >= request.expires_at:
            self._expire_request(
                request,
                actor_ref=reviewer.actor_ref,
                idempotency_key="auto_expire:" + key,
                evidence_ref=evidence,
            )
            raise _boundary("approval_request_expired")
        if action is ApprovalAction.APPROVE and reviewer.actor_ref == request.creator_actor_ref:
            raise _boundary("self_approval_forbidden")
        base_policy = self._request_policy[request.id]
        evaluation = self._policy.evaluate(
            replace(
                base_policy,
                actor=reviewer,
                phase=PolicyPhase.DECISION,
                approval_state=ApprovalState.PENDING,
                evaluated_at=self._current_time(base_policy.evaluated_at),
            )
        )
        if not evaluation.allowed:
            raise _boundary(evaluation.error_code or "policy_denied")
        next_state = {
            ApprovalAction.APPROVE: ApprovalState.APPROVED,
            ApprovalAction.REJECT: ApprovalState.REJECTED,
            ApprovalAction.REVISE: ApprovalState.REVISED,
        }[action]
        decision = self._append_decision(
            request=request,
            action=action,
            actor_ref=reviewer.actor_ref,
            evidence_ref=evidence,
            idempotency_key=key,
            policy_decision_ref=evaluation.decision_ref,
            decided_at=self._current_time(),
            revision_ref=revision_ref,
        )
        self._request_state[request.id] = next_state
        return decision

    def expire(
        self,
        request_id: str,
        *,
        actor_ref: str,
        idempotency_key: str,
    ) -> ActionApprovalDecision:
        normalized_request_id = _require_identifier(request_id, "approval_request_id_required")
        key = _require_identifier(idempotency_key, "idempotency_key_required")
        existing = self._decision_by_idempotency.get(key)
        if existing is not None:
            if existing.request_id != normalized_request_id or existing.action is not ApprovalAction.EXPIRE:
                raise _boundary("idempotency_conflict")
            return existing
        request = self._pending_request(normalized_request_id)
        now = self._current_time()
        if now < request.expires_at:
            raise _boundary("approval_request_not_expired")
        return self._expire_request(
            request,
            actor_ref=actor_ref,
            idempotency_key=key,
            evidence_ref="expiry_evidence_ref",
        )

    def pre_execution_recheck(
        self,
        request_id: str,
        policy_request: PolicyRequest,
    ) -> PolicyDecision:
        request = self._request_by_id.get(_require_identifier(request_id, "approval_request_id_required"))
        if request is None:
            raise _boundary("approval_request_not_found")
        if self._request_state.get(request.id) is not ApprovalState.APPROVED:
            raise _boundary("approval_not_approved")
        if (
            policy_request.scope != request.scope
            or policy_request.action != request.action
            or policy_request.target_ref != request.target_ref
            or policy_request.correlation_id != request.correlation_id
        ):
            raise _boundary("approval_scope_mismatch")
        execution_request = replace(
            policy_request,
            phase=PolicyPhase.EXECUTION,
            approval_state=ApprovalState.APPROVED,
        )
        if execution_request.subject_version != request.subject_version:
            return ActionPolicy._decision(
                execution_request,
                False,
                "approval_subject_version_mismatch",
            )
        return self._policy.evaluate(execution_request)

    def request_state(self, request_id: str) -> ApprovalState:
        request = self._request_by_id.get(_require_identifier(request_id, "approval_request_id_required"))
        if request is None:
            raise _boundary("approval_request_not_found")
        return self._request_state[request.id]

    def _pending_request(self, request_id: str) -> ActionApprovalRequest:
        request = self._request_by_id.get(_require_identifier(request_id, "approval_request_id_required"))
        if request is None:
            raise _boundary("approval_request_not_found")
        state = self._request_state.get(request.id)
        if state is not ApprovalState.PENDING:
            if state is ApprovalState.EXPIRED:
                raise _boundary("approval_request_expired")
            raise _boundary("duplicate_decision")
        return request

    def _append_decision(
        self,
        *,
        request: ActionApprovalRequest,
        action: ApprovalAction,
        actor_ref: str,
        evidence_ref: str,
        idempotency_key: str,
        policy_decision_ref: str,
        decided_at: datetime,
        revision_ref: str | None = None,
    ) -> ActionApprovalDecision:
        decision = ActionApprovalDecision(
            id="approval_decision:" + _digest(request.id, idempotency_key)[:32],
            request_id=request.id,
            action=action,
            scope=request.scope,
            actor_ref=_require_identifier(actor_ref, "actor_ref_required"),
            decided_at=decided_at,
            evidence_ref=evidence_ref,
            policy_version=request.policy_version,
            subject_version=request.subject_version,
            correlation_id=request.correlation_id,
            idempotency_key=idempotency_key,
            policy_decision_ref=policy_decision_ref,
            revision_ref=revision_ref,
        )
        self._decisions = (*self._decisions, decision)
        self._decision_by_idempotency[idempotency_key] = decision
        self._decision_by_request[request.id] = decision
        self._append_audit(
            event_kind="approval_decision_appended",
            request_id=request.id,
            decision_id=decision.id,
            actor_ref=decision.actor_ref,
            request=request,
            evidence_ref=evidence_ref,
            policy_decision_ref=policy_decision_ref,
            occurred_at=decided_at,
        )
        return decision

    def _expire_request(
        self,
        request: ActionApprovalRequest,
        *,
        actor_ref: str,
        idempotency_key: str,
        evidence_ref: str,
    ) -> ActionApprovalDecision:
        key = _require_identifier(idempotency_key, "idempotency_key_required")
        actor_ref = _require_identifier(actor_ref, "actor_ref_required")
        evidence_ref = _require_identifier(evidence_ref, "approval_evidence_ref_required")
        existing = self._decision_by_idempotency.get(key)
        if existing is not None:
            if existing.request_id != request.id or existing.action is not ApprovalAction.EXPIRE:
                raise _boundary("idempotency_conflict")
            return existing
        decision = self._append_decision(
            request=request,
            action=ApprovalAction.EXPIRE,
            actor_ref=actor_ref,
            evidence_ref=evidence_ref,
            idempotency_key=key,
            policy_decision_ref=request.request_policy_decision_ref,
            decided_at=self._current_time(),
        )
        self._request_state[request.id] = ApprovalState.EXPIRED
        return decision

    def _append_audit(
        self,
        *,
        event_kind: str,
        request_id: str | None,
        decision_id: str | None,
        actor_ref: str,
        request: ActionApprovalRequest,
        evidence_ref: str | None,
        policy_decision_ref: str,
        occurred_at: datetime,
        error_code: str | None = None,
    ) -> None:
        self._audit_events = (
            *self._audit_events,
            ActionApprovalAuditEvent(
                sequence=len(self._audit_events) + 1,
                event_kind=event_kind,
                request_id=request_id,
                decision_id=decision_id,
                actor_ref=actor_ref,
                scope=request.scope,
                action=request.action.value,
                target_ref=request.target_ref,
                correlation_id=request.correlation_id,
                policy_version=request.policy_version,
                evidence_ref=evidence_ref,
                subject_version=request.subject_version,
                occurred_at=occurred_at,
                policy_decision_ref=policy_decision_ref,
                error_code=error_code,
            ),
        )

    @staticmethod
    def _request_fingerprint(
        policy_request: PolicyRequest,
        creator_actor_ref: str,
        expires_at: datetime,
    ) -> str:
        action_value = (
            policy_request.action.value
            if isinstance(policy_request.action, ActionName)
            else str(policy_request.action)
        )
        actor_role = (
            policy_request.actor.role.value
            if isinstance(policy_request.actor.role, ActorRole)
            else str(policy_request.actor.role)
        )
        return _digest(
            policy_request.scope.tenant_id,
            policy_request.scope.project_id,
            policy_request.scope.business_line_id,
            policy_request.correlation_id,
            action_value,
            policy_request.phase.value,
            policy_request.actor.actor_ref,
            actor_role,
            policy_request.actor.scope,
            policy_request.target_ref,
            policy_request.data_state.value,
            policy_request.approval_state.value,
            policy_request.fact_observed_at.isoformat(),
            policy_request.fact_ttl.total_seconds(),
            policy_request.required_evidence_refs,
            policy_request.feature_flag_snapshot,
            policy_request.dnc_blocked,
            policy_request.consent_granted,
            policy_request.environment.value,
            policy_request.policy_version,
            policy_request.subject_version,
            creator_actor_ref,
            expires_at.isoformat(),
        )

    @staticmethod
    def _assert_same_decision(
        existing: ActionApprovalDecision,
        request_id: str,
        action: ApprovalAction,
        reviewer: PolicyActor,
        evidence_ref: str,
        revision_ref: str | None,
    ) -> None:
        if (
            existing.request_id != request_id
            or existing.action is not action
            or existing.actor_ref != reviewer.actor_ref
            or existing.evidence_ref != evidence_ref
            or existing.revision_ref != revision_ref
        ):
            raise _boundary("idempotency_conflict")

    def _current_time(self, fallback: datetime | None = None) -> datetime:
        if self._now is None:
            return fallback or datetime.now(timezone.utc)
        return self._now()
