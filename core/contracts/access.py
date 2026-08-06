"""Repository access grants issued by the local isolation policy.

The grant is an in-process contract capability, not authentication or a
production authorization token.  Its signature prevents ordinary dataclass
replacement from silently widening scope, target, or read time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from uuid import uuid4

from core.contracts.errors import ContractValidationError
from core.contracts.metadata import DataState, Sensitivity
from core.contracts.scope import ScopeRef, _require_identifier, _require_uuid


_GRANT_ISSUER = object()


@dataclass(frozen=True)
class RepositoryReadGrant:
    """Immutable grant bound to one scope, truth version, and read instant."""

    grant_id: UUID
    scope: ScopeRef
    data_version_id: UUID
    read_at: datetime
    policy_decision_ref: str
    data_state: DataState
    sensitivity: Sensitivity
    is_synthetic: bool
    _signature: tuple[object, ...] = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        validate_repository_read_grant(self)


def _grant_signature(
    grant_id: UUID,
    scope: ScopeRef,
    data_version_id: UUID,
    read_at: datetime,
    policy_decision_ref: str,
    data_state: DataState,
    sensitivity: Sensitivity,
    is_synthetic: bool,
) -> tuple[object, ...]:
    return (
        _GRANT_ISSUER,
        grant_id,
        scope,
        data_version_id,
        read_at,
        policy_decision_ref,
        data_state,
        sensitivity,
        is_synthetic,
    )


def _issue_repository_read_grant(
    *,
    scope: ScopeRef,
    data_version_id: UUID,
    read_at: datetime,
    policy_decision_ref: str,
    data_state: DataState,
    sensitivity: Sensitivity,
    is_synthetic: bool,
) -> RepositoryReadGrant:
    """Issue a grant for ``core.security`` after policy evaluation."""

    grant_id = uuid4()
    return RepositoryReadGrant(
        grant_id=grant_id,
        scope=scope,
        data_version_id=data_version_id,
        read_at=read_at,
        policy_decision_ref=policy_decision_ref,
        data_state=data_state,
        sensitivity=sensitivity,
        is_synthetic=is_synthetic,
        _signature=_grant_signature(
            grant_id,
            scope,
            data_version_id,
            read_at,
            policy_decision_ref,
            data_state,
            sensitivity,
            is_synthetic,
        ),
    )


def validate_repository_read_grant(grant: object) -> RepositoryReadGrant:
    """Reject missing, malformed, or field-replaced repository grants."""

    if not isinstance(grant, RepositoryReadGrant):
        raise ContractValidationError("repository_read_grant_required")
    if not isinstance(grant.scope, ScopeRef):
        raise ContractValidationError("repository_read_grant_invalid")
    _require_uuid(grant.grant_id, "repository_read_grant_invalid")
    _require_uuid(grant.data_version_id, "repository_read_grant_invalid")
    if (
        not isinstance(grant.read_at, datetime)
        or grant.read_at.tzinfo is None
        or grant.read_at.utcoffset() is None
    ):
        raise ContractValidationError("repository_read_grant_invalid")
    _require_identifier(
        grant.policy_decision_ref,
        "repository_read_grant_invalid",
    )
    if grant.data_state is not DataState.APPROVED:
        raise ContractValidationError("repository_read_grant_invalid")
    if not isinstance(grant.sensitivity, Sensitivity):
        raise ContractValidationError("repository_read_grant_invalid")
    if grant.is_synthetic is not False:
        raise ContractValidationError("repository_read_grant_invalid")
    expected = _grant_signature(
        grant.grant_id,
        grant.scope,
        grant.data_version_id,
        grant.read_at,
        grant.policy_decision_ref,
        grant.data_state,
        grant.sensitivity,
        grant.is_synthetic,
    )
    if grant._signature != expected:
        raise ContractValidationError("repository_read_grant_invalid")
    return grant


class RepositoryGrantVerifier:
    """Sealed nominal base for the repository's real isolation policy."""

    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if (
            cls.__module__ != "core.security.isolation"
            or cls.__name__ != "IsolationPolicy"
        ):
            raise ContractValidationError("repository_grant_verifier_forbidden")

    def assert_repository_grant(self, grant: object) -> RepositoryReadGrant:
        raise NotImplementedError("sealed verifier must implement grant validation")


class RepositoryAuditRecorder:
    """Sealed nominal sink required before a repository read can return truth."""

    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if (
            cls.__module__ != "core.security.isolation"
            or cls.__name__ != "InMemoryIsolationAuditLog"
        ):
            raise ContractValidationError("repository_audit_recorder_forbidden")

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
    ) -> object:
        raise NotImplementedError("sealed recorder must implement repository audit")
