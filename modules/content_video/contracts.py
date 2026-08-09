"""P07-01 synthetic content/video fact-lock contracts.

These contracts only model internal synthetic briefs, locked fact/asset/policy
versions, review state, and QC handoff state. They do not call providers,
render media, export files, publish content, or write approved business facts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
from uuid import UUID

from core.contracts import ContractValidationError, DataState, ScopeRef


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


class ContentVideoBoundaryError(ContractValidationError):
    """Stable, value-free P07-01 boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _boundary(code: str) -> ContentVideoBoundaryError:
    return ContentVideoBoundaryError(code)


class FactApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AssetOrigin(str, Enum):
    AI_GENERATED = "ai_generated"
    SUPPLIER_AUTHORIZED = "supplier_authorized"
    UNKNOWN = "unknown"


class AssetRightsState(str, Enum):
    AUTHORIZED = "authorized"
    UNKNOWN = "unknown"
    EXPIRED = "expired"


class BriefDataOrigin(str, Enum):
    SYNTHETIC = "synthetic"
    UNKNOWN = "unknown"


class PolicyBoundaryState(str, Enum):
    APPROVED = "approved"
    UNKNOWN = "unknown"
    EXPIRED = "expired"


class ContentTaskState(str, Enum):
    DRAFT = "draft"
    REVIEW_PENDING = "review_pending"
    BLOCKED = "blocked"


class ContentReviewState(str, Enum):
    REVIEW_PENDING = "review_pending"
    BLOCKED = "blocked"


class VideoTaskState(str, Enum):
    QC_PENDING = "qc_pending"
    BLOCKED = "blocked"


def _require_identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
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


def _require_positive_version(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise _boundary("version_number_required")
    return value


def _require_identifier_tuple(value: object, code: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, tuple) or (not value and not allow_empty):
        raise _boundary(code)
    for item in value:
        _require_identifier(item, code)
    if len(set(value)) != len(value):
        raise _boundary(code)
    return value


def _require_uuid_tuple(value: object, code: str, *, allow_empty: bool = False) -> tuple[UUID, ...]:
    if not isinstance(value, tuple) or (not value and not allow_empty):
        raise _boundary(code)
    for item in value:
        _require_uuid(item, code)
    if len(set(value)) != len(value):
        raise _boundary(code)
    return value


def _require_internal_synthetic(
    *,
    is_synthetic: object,
    external_execution_allowed: object,
    code: str,
) -> None:
    if is_synthetic is not True or external_execution_allowed is not False:
        raise _boundary(code)


def _require_same_scope(scope: ScopeRef, *contracts: object) -> None:
    for contract in contracts:
        if getattr(contract, "scope", None) != scope:
            raise _boundary("cross_scope_forbidden")


@dataclass(frozen=True)
class FactVersionLock:
    """Reference to an approved synthetic fact version without fact values."""

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
    source_label: str
    evidence_ref: str
    policy_version: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_identifier(self.fact_ref, "fact_ref_required")
        _require_identifier(self.fact_type, "fact_type_required")
        _require_identifier(self.subject_ref, "subject_ref_required")
        _require_uuid(self.version_id, "fact_version_id_required")
        _require_positive_version(self.version_no)
        if not isinstance(self.approval_state, FactApprovalState):
            raise _boundary("fact_approval_state_required")
        if not isinstance(self.data_state, DataState):
            raise _boundary("data_state_required")
        observed = _require_time(self.observed_at, "fact_observed_at_required")
        expires = _require_time(self.expires_at, "fact_expires_at_required")
        if expires <= observed:
            raise _boundary("fact_lock_expired")
        _require_identifier(self.source_label, "fact_source_label_required")
        _require_identifier(self.evidence_ref, "fact_evidence_ref_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_fact_lock_required",
        )


@dataclass(frozen=True)
class AssetRightsVersionLock:
    """Reference to a synthetic asset rights version without binary assets."""

    scope: ScopeRef
    asset_ref: str
    version_id: UUID
    version_no: int
    origin: AssetOrigin
    rights_state: AssetRightsState
    rights_version: str
    evidence_ref: str
    observed_at: datetime
    expires_at: datetime
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_identifier(self.asset_ref, "asset_ref_required")
        _require_uuid(self.version_id, "asset_version_id_required")
        _require_positive_version(self.version_no)
        if not isinstance(self.origin, AssetOrigin):
            raise _boundary("asset_origin_required")
        if not isinstance(self.rights_state, AssetRightsState):
            raise _boundary("asset_rights_state_required")
        _require_identifier(self.rights_version, "asset_rights_version_required")
        _require_identifier(self.evidence_ref, "asset_evidence_ref_required")
        observed = _require_time(self.observed_at, "asset_observed_at_required")
        expires = _require_time(self.expires_at, "asset_expires_at_required")
        if expires <= observed:
            raise _boundary("asset_rights_expired")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_asset_lock_required",
        )


@dataclass(frozen=True)
class ForbiddenExpressionPolicy:
    """Versioned forbidden-token policy for synthetic brief probes."""

    scope: ScopeRef
    version_id: UUID
    policy_version: str
    denied_tokens: tuple[str, ...]
    observed_at: datetime
    expires_at: datetime
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_uuid(self.version_id, "policy_version_id_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_identifier_tuple(self.denied_tokens, "forbidden_expression_policy_required")
        observed = _require_time(self.observed_at, "policy_observed_at_required")
        expires = _require_time(self.expires_at, "policy_expires_at_required")
        if expires <= observed:
            raise _boundary("policy_lock_expired")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_policy_required",
        )


@dataclass(frozen=True)
class PolicyVersionLock:
    """Locked content policy boundary plus forbidden expression policy."""

    scope: ScopeRef
    policy_version: str
    boundary_state: PolicyBoundaryState
    forbidden_policy: ForbiddenExpressionPolicy
    observed_at: datetime
    expires_at: datetime
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_identifier(self.policy_version, "policy_version_required")
        if not isinstance(self.boundary_state, PolicyBoundaryState):
            raise _boundary("policy_boundary_state_required")
        if not isinstance(self.forbidden_policy, ForbiddenExpressionPolicy):
            raise _boundary("forbidden_expression_policy_required")
        _require_same_scope(self.scope, self.forbidden_policy)
        observed = _require_time(self.observed_at, "policy_observed_at_required")
        expires = _require_time(self.expires_at, "policy_expires_at_required")
        if expires <= observed:
            raise _boundary("policy_lock_expired")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_policy_required",
        )


@dataclass(frozen=True)
class SyntheticBrief:
    """Synthetic-only brief made from safe tokens instead of raw copy."""

    scope: ScopeRef
    brief_ref: str
    locale: str
    topic_ref: str
    tokens: tuple[str, ...]
    data_origin: BriefDataOrigin
    is_synthetic: bool = True
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_scope(self.scope)
        _require_identifier(self.brief_ref, "brief_ref_required")
        _require_identifier(self.locale, "brief_locale_required")
        _require_identifier(self.topic_ref, "topic_ref_required")
        _require_identifier_tuple(self.tokens, "brief_tokens_required")
        if self.data_origin is not BriefDataOrigin.SYNTHETIC:
            raise _boundary("synthetic_brief_required")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_brief_required",
        )


@dataclass(frozen=True)
class ContentTask:
    """Draft content task with fact, asset, and policy versions locked."""

    id: UUID
    scope: ScopeRef
    brief: SyntheticBrief
    fact_locks: tuple[FactVersionLock, ...]
    asset_locks: tuple[AssetRightsVersionLock, ...]
    policy_lock: PolicyVersionLock
    state: ContentTaskState
    created_at: datetime
    created_by: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    provider_call_requested: bool = False
    public_publish_allowed: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "content_task_id_required")
        _require_scope(self.scope)
        if not isinstance(self.brief, SyntheticBrief):
            raise _boundary("synthetic_brief_required")
        if not isinstance(self.fact_locks, tuple):
            raise _boundary("fact_lock_required")
        if not isinstance(self.asset_locks, tuple):
            raise _boundary("asset_rights_required")
        for fact in self.fact_locks:
            if not isinstance(fact, FactVersionLock):
                raise _boundary("fact_lock_required")
        for asset in self.asset_locks:
            if not isinstance(asset, AssetRightsVersionLock):
                raise _boundary("asset_rights_required")
        if not isinstance(self.policy_lock, PolicyVersionLock):
            raise _boundary("policy_lock_required")
        _require_same_scope(self.scope, self.brief, self.policy_lock, *self.fact_locks, *self.asset_locks)
        if not isinstance(self.state, ContentTaskState):
            raise _boundary("content_task_state_required")
        _require_time(self.created_at, "created_at_required")
        _require_identifier(self.created_by, "created_by_required")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_content_task_required",
        )
        if self.provider_call_requested is not False:
            raise _boundary("video_call_forbidden")
        if self.public_publish_allowed is not False:
            raise _boundary("public_publish_forbidden")


@dataclass(frozen=True)
class ContentReviewRecord:
    """Review handoff created only after lock and policy checks pass."""

    id: UUID
    scope: ScopeRef
    content_task_id: UUID
    state: ContentReviewState
    checked_at: datetime
    locked_fact_versions: tuple[UUID, ...]
    locked_asset_versions: tuple[UUID, ...]
    policy_version: str
    forbidden_expression_version_id: UUID
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    provider_call_requested: bool = False
    public_publish_allowed: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "content_review_id_required")
        _require_scope(self.scope)
        _require_uuid(self.content_task_id, "content_task_id_required")
        if not isinstance(self.state, ContentReviewState):
            raise _boundary("content_review_state_required")
        _require_time(self.checked_at, "checked_at_required")
        _require_uuid_tuple(self.locked_fact_versions, "fact_lock_required")
        _require_uuid_tuple(self.locked_asset_versions, "asset_rights_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_uuid(self.forbidden_expression_version_id, "policy_version_id_required")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_review_required",
        )
        if self.provider_call_requested is not False:
            raise _boundary("video_call_forbidden")
        if self.public_publish_allowed is not False:
            raise _boundary("public_publish_forbidden")

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": str(self.id),
            "content_task_id": str(self.content_task_id),
            "state": self.state.value,
            "locked_fact_versions": [str(value) for value in self.locked_fact_versions],
            "locked_asset_versions": [str(value) for value in self.locked_asset_versions],
            "policy_version": self.policy_version,
            "is_synthetic": True,
            "external_execution_allowed": False,
            "provider_call_requested": False,
            "public_publish_allowed": False,
        }


@dataclass(frozen=True)
class VideoTask:
    """QC handoff contract; provider calls and exports are forbidden in P07-01."""

    id: UUID
    scope: ScopeRef
    content_task_id: UUID
    locked_fact_versions: tuple[UUID, ...]
    locked_asset_versions: tuple[UUID, ...]
    policy_version: str
    state: VideoTaskState
    created_at: datetime
    created_by: str
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    provider_call_requested: bool = False
    internal_export_allowed: bool = False
    public_publish_allowed: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "video_task_id_required")
        _require_scope(self.scope)
        _require_uuid(self.content_task_id, "content_task_id_required")
        _require_uuid_tuple(self.locked_fact_versions, "fact_lock_required")
        _require_uuid_tuple(self.locked_asset_versions, "asset_rights_required")
        _require_identifier(self.policy_version, "policy_version_required")
        if not isinstance(self.state, VideoTaskState):
            raise _boundary("video_task_state_required")
        _require_time(self.created_at, "created_at_required")
        _require_identifier(self.created_by, "created_by_required")
        _require_internal_synthetic(
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            code="synthetic_video_task_required",
        )
        if self.provider_call_requested is not False:
            raise _boundary("video_call_forbidden")
        if self.internal_export_allowed is not False:
            raise _boundary("internal_export_forbidden")
        if self.public_publish_allowed is not False:
            raise _boundary("public_publish_forbidden")

    @classmethod
    def from_review(
        cls,
        *,
        id: UUID,
        review: ContentReviewRecord,
        created_at: datetime,
        created_by: str,
    ) -> "VideoTask":
        if not isinstance(review, ContentReviewRecord):
            raise _boundary("content_review_required")
        if review.state is not ContentReviewState.REVIEW_PENDING:
            raise _boundary("content_review_state_required")
        return cls(
            id=id,
            scope=review.scope,
            content_task_id=review.content_task_id,
            locked_fact_versions=review.locked_fact_versions,
            locked_asset_versions=review.locked_asset_versions,
            policy_version=review.policy_version,
            state=VideoTaskState.QC_PENDING,
            created_at=created_at,
            created_by=created_by,
            is_synthetic=True,
            external_execution_allowed=False,
            provider_call_requested=False,
            internal_export_allowed=False,
            public_publish_allowed=False,
        )


class ContentPolicySuite:
    """Local-only checker for P07-01 fact, asset, policy, and brief locks."""

    __slots__ = ()

    def submit_for_review(
        self,
        task: ContentTask,
        *,
        checked_at: datetime,
        current_fact_versions: Mapping[str, UUID],
        current_asset_versions: Mapping[str, UUID],
        current_policy_version: str,
    ) -> ContentReviewRecord:
        if not isinstance(task, ContentTask):
            raise _boundary("content_task_required")
        checked = _require_time(checked_at, "checked_at_required")
        if task.state is not ContentTaskState.DRAFT:
            raise _boundary("content_task_state_required")
        self._validate_policy(task.policy_lock, checked, current_policy_version)
        self._validate_facts(task.fact_locks, checked, current_fact_versions)
        self._validate_assets(task.asset_locks, checked, current_asset_versions)
        self._validate_forbidden_tokens(task.brief, task.policy_lock.forbidden_policy)
        return ContentReviewRecord(
            id=task.id,
            scope=task.scope,
            content_task_id=task.id,
            state=ContentReviewState.REVIEW_PENDING,
            checked_at=checked,
            locked_fact_versions=tuple(lock.version_id for lock in task.fact_locks),
            locked_asset_versions=tuple(lock.version_id for lock in task.asset_locks),
            policy_version=task.policy_lock.policy_version,
            forbidden_expression_version_id=task.policy_lock.forbidden_policy.version_id,
            is_synthetic=True,
            external_execution_allowed=False,
            provider_call_requested=False,
            public_publish_allowed=False,
        )

    def _validate_facts(
        self,
        locks: tuple[FactVersionLock, ...],
        checked_at: datetime,
        current_versions: Mapping[str, UUID],
    ) -> None:
        if not locks:
            raise _boundary("fact_lock_required")
        if not isinstance(current_versions, Mapping):
            raise _boundary("current_fact_versions_required")
        seen: set[str] = set()
        for lock in locks:
            if lock.fact_ref in seen:
                raise _boundary("fact_lock_duplicate")
            seen.add(lock.fact_ref)
            if (
                lock.approval_state is not FactApprovalState.APPROVED
                or lock.data_state is not DataState.FIXTURE
                or lock.source_label != "approved_synthetic"
            ):
                raise _boundary("unapproved_fact_lock")
            if lock.expires_at <= checked_at:
                raise _boundary("fact_lock_expired")
            current = current_versions.get(lock.fact_ref)
            if current is None:
                raise _boundary("fact_version_invalidated")
            if current != lock.version_id:
                raise _boundary("fact_version_invalidated")

    def _validate_assets(
        self,
        locks: tuple[AssetRightsVersionLock, ...],
        checked_at: datetime,
        current_versions: Mapping[str, UUID],
    ) -> None:
        if not locks:
            raise _boundary("asset_rights_required")
        if not isinstance(current_versions, Mapping):
            raise _boundary("current_asset_versions_required")
        seen: set[str] = set()
        for lock in locks:
            if lock.asset_ref in seen:
                raise _boundary("asset_lock_duplicate")
            seen.add(lock.asset_ref)
            if lock.origin is AssetOrigin.UNKNOWN or lock.rights_state is AssetRightsState.UNKNOWN:
                raise _boundary("asset_rights_unknown")
            if lock.rights_state is AssetRightsState.EXPIRED or lock.expires_at <= checked_at:
                raise _boundary("asset_rights_expired")
            current = current_versions.get(lock.asset_ref)
            if current is None:
                raise _boundary("asset_version_invalidated")
            if current != lock.version_id:
                raise _boundary("asset_version_invalidated")

    def _validate_policy(
        self,
        lock: PolicyVersionLock,
        checked_at: datetime,
        current_policy_version: str,
    ) -> None:
        _require_identifier(current_policy_version, "current_policy_version_required")
        if lock.policy_version != current_policy_version:
            raise _boundary("policy_version_invalidated")
        if lock.forbidden_policy.policy_version != lock.policy_version:
            raise _boundary("policy_version_invalidated")
        if lock.boundary_state is PolicyBoundaryState.UNKNOWN:
            raise _boundary("policy_boundary_unknown")
        if lock.boundary_state is PolicyBoundaryState.EXPIRED:
            raise _boundary("policy_lock_expired")
        if lock.expires_at <= checked_at or lock.forbidden_policy.expires_at <= checked_at:
            raise _boundary("policy_lock_expired")

    def _validate_forbidden_tokens(
        self,
        brief: SyntheticBrief,
        policy: ForbiddenExpressionPolicy,
    ) -> None:
        denied = set(policy.denied_tokens)
        if denied.intersection(brief.tokens):
            raise _boundary("forbidden_expression_detected")
