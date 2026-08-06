"""Immutable, scoped truth contracts with no business payload values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
from uuid import UUID

from core.contracts import (
    BaseMetadata,
    ContractValidationError,
    DataState,
    DataVersionRef,
    ScopeRef,
    SourceRef,
    assert_metadata_lineage,
    assert_same_scope,
)
from core.contracts.scope import _require_identifier, _require_uuid


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_READABLE_STATE = DataState.APPROVED
_NON_CURRENT_STATES = frozenset(
    {
        DataState.FIXTURE,
        DataState.MOCK,
        DataState.STAGING,
        DataState.EXPIRED,
        DataState.BLOCKED,
        DataState.CONFLICT,
        DataState.SUPERSEDED,
    }
)


class TruthEntityKind(str, Enum):
    PRODUCT = "product"
    SKU = "sku"
    PRICE = "price"
    INVENTORY = "inventory"
    DELIVERY_RULE = "delivery_rule"
    COMPLIANCE_DOCUMENT = "compliance_document"
    CONTENT_ASSET = "content_asset"
    APPROVED_FACT = "approved_fact"
    FORBIDDEN_EXPRESSION = "forbidden_expression"


def _require_aware_timestamp(value: object, code: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ContractValidationError(code)


def _require_hash(value: object, code: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ContractValidationError(code)


def _require_identifier_tuple(value: object, code: str) -> None:
    if not isinstance(value, tuple) or not value:
        raise ContractValidationError(code)
    for item in value:
        _require_identifier(item, code)
    if len(set(value)) != len(value):
        raise ContractValidationError(code)


@dataclass(frozen=True)
class TruthPayloadRef:
    """Value-free payload locator used by contract probes and future storage ports."""

    subject_ref: str
    field_names: tuple[str, ...]
    payload_hash: str
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.subject_ref, "truth_subject_ref_required")
        _require_identifier_tuple(self.field_names, "truth_field_names_required")
        _require_hash(self.payload_hash, "truth_payload_hash_required")
        if self.external_execution_allowed is not False:
            raise ContractValidationError("external_execution_forbidden")


@dataclass(frozen=True)
class ApprovalEvidence:
    """Append-only human approval reference bound to one source and version."""

    id: UUID
    scope: ScopeRef
    source_ref_id: UUID
    data_version_id: UUID
    actor_ref: str
    decision_ref: str
    evidence_ref: str
    policy_version: str
    approved_at: datetime
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "approval_evidence_id_required")
        if not isinstance(self.scope, ScopeRef):
            raise ContractValidationError("scope_required")
        _require_uuid(self.source_ref_id, "source_ref_id_required")
        _require_uuid(self.data_version_id, "data_version_id_required")
        _require_identifier(self.actor_ref, "approval_actor_ref_required")
        _require_identifier(self.decision_ref, "approval_decision_ref_required")
        _require_identifier(self.evidence_ref, "approval_evidence_ref_required")
        _require_identifier(self.policy_version, "approval_policy_version_required")
        _require_aware_timestamp(self.approved_at, "approved_at_required")
        if self.external_execution_allowed is not False:
            raise ContractValidationError("external_execution_forbidden")


@dataclass(frozen=True)
class TruthVersion:
    """One immutable entity version with explicit lineage and lifecycle state."""

    entity_kind: TruthEntityKind
    payload: TruthPayloadRef
    source: SourceRef
    version: DataVersionRef
    metadata: BaseMetadata
    changed_fields: tuple[str, ...]
    diff_hash: str
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    parent_version_id: UUID | None = None
    approval: ApprovalEvidence | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.entity_kind, TruthEntityKind):
            raise ContractValidationError("truth_entity_kind_required")
        if not isinstance(self.payload, TruthPayloadRef):
            raise ContractValidationError("truth_payload_required")
        if not isinstance(self.source, SourceRef):
            raise ContractValidationError("source_ref_required")
        if not isinstance(self.version, DataVersionRef):
            raise ContractValidationError("data_version_required")
        if not isinstance(self.metadata, BaseMetadata):
            raise ContractValidationError("metadata_required")
        assert_metadata_lineage(self.source, self.version, self.metadata)
        if self.version.data_state != self.metadata.data_state:
            raise ContractValidationError("truth_state_lineage_mismatch")
        if not (
            self.source.sensitivity
            == self.version.sensitivity
            == self.metadata.sensitivity
        ):
            raise ContractValidationError("truth_sensitivity_lineage_mismatch")
        _require_identifier_tuple(self.changed_fields, "changed_fields_required")
        _require_hash(self.diff_hash, "truth_diff_hash_required")
        if set(self.changed_fields) - set(self.payload.field_names):
            raise ContractValidationError("changed_fields_not_in_payload")
        if self.parent_version_id is not None:
            _require_uuid(self.parent_version_id, "parent_version_id_required")
            if self.parent_version_id == self.version.id:
                raise ContractValidationError("self_parent_forbidden")
        if self.effective_from is not None:
            _require_aware_timestamp(self.effective_from, "effective_from_required")
        if self.effective_until is not None:
            _require_aware_timestamp(self.effective_until, "effective_until_required")
            if self.effective_from is None or self.effective_until <= self.effective_from:
                raise ContractValidationError("effective_window_invalid")
        if self.metadata.data_state is DataState.EXPIRED and self.effective_until is None:
            raise ContractValidationError("expired_window_required")
        if self.metadata.data_state is _READABLE_STATE:
            if self.approval is None:
                raise ContractValidationError("approval_evidence_required")
            if self.effective_from is None:
                raise ContractValidationError("effective_from_required")
            self._assert_approval_lineage()
        elif self.metadata.data_state in {
            DataState.FIXTURE,
            DataState.MOCK,
            DataState.STAGING,
        } and self.approval is not None:
            raise ContractValidationError("unapproved_state_has_approval")
        elif self.approval is not None:
            self._assert_approval_lineage()

    @property
    def scope(self) -> ScopeRef:
        return self.metadata.scope

    @property
    def data_state(self) -> DataState:
        return self.metadata.data_state

    @property
    def is_candidate(self) -> bool:
        return self.data_state is DataState.STAGING

    def is_fresh_at(self, at: datetime) -> bool:
        _require_aware_timestamp(at, "read_time_required")
        if self.effective_from is None or at < self.effective_from:
            return False
        return self.effective_until is None or at < self.effective_until

    def _assert_approval_lineage(self) -> None:
        if self.approval is None:
            raise ContractValidationError("approval_evidence_required")
        assert_same_scope(self, self.approval)
        if self.approval.source_ref_id != self.source.id:
            raise ContractValidationError("approval_source_lineage_mismatch")
        if self.approval.data_version_id != self.version.id:
            raise ContractValidationError("approval_version_lineage_mismatch")


ALLOWED_TRANSITIONS: dict[DataState, frozenset[DataState]] = {
    DataState.FIXTURE: frozenset(),
    DataState.MOCK: frozenset(),
    DataState.STAGING: frozenset(
        {
            DataState.APPROVED,
            DataState.BLOCKED,
            DataState.CONFLICT,
            DataState.SUPERSEDED,
        }
    ),
    DataState.APPROVED: frozenset(
        {
            DataState.EXPIRED,
            DataState.BLOCKED,
            DataState.CONFLICT,
            DataState.SUPERSEDED,
        }
    ),
    DataState.EXPIRED: frozenset({DataState.STAGING}),
    DataState.BLOCKED: frozenset({DataState.STAGING}),
    DataState.CONFLICT: frozenset({DataState.STAGING, DataState.APPROVED}),
    DataState.SUPERSEDED: frozenset({DataState.STAGING}),
}


def validate_transition(parent: TruthVersion, child: TruthVersion) -> None:
    """Validate an append-only successor; never mutates or deletes history."""

    if not isinstance(parent, TruthVersion) or not isinstance(child, TruthVersion):
        raise ContractValidationError("truth_version_required")
    assert_same_scope(parent, child)
    if parent.entity_kind is not child.entity_kind:
        raise ContractValidationError("truth_entity_kind_mismatch")
    if parent.payload.subject_ref != child.payload.subject_ref:
        raise ContractValidationError("truth_subject_mismatch")
    if child.parent_version_id != parent.version.id:
        raise ContractValidationError("parent_version_lineage_mismatch")
    if child.version.version_no != parent.version.version_no + 1:
        raise ContractValidationError("truth_version_sequence_invalid")
    if child.data_state not in ALLOWED_TRANSITIONS[parent.data_state]:
        raise ContractValidationError("truth_state_transition_forbidden")


def is_current_readable_state(state: DataState) -> bool:
    if not isinstance(state, DataState):
        raise ContractValidationError("data_state_required")
    if state in _NON_CURRENT_STATES:
        return False
    return state is _READABLE_STATE
