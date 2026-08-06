"""Stdlib-only source, version, state, and base metadata contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from core.contracts.errors import ContractValidationError
from core.contracts.scope import ScopeRef, _require_identifier, _require_uuid


class DataState(str, Enum):
    FIXTURE = "fixture"
    MOCK = "mock"
    STAGING = "staging"
    APPROVED = "approved"
    EXPIRED = "expired"
    BLOCKED = "blocked"
    CONFLICT = "conflict"
    SUPERSEDED = "superseded"


class Sensitivity(str, Enum):
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PERSONAL = "personal"


def _require_enum(value: object, enum_type: type[Enum], code: str) -> None:
    if not isinstance(value, enum_type):
        raise ContractValidationError(code)


def _require_positive_version(value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ContractValidationError("version_number_required")


def _require_aware_timestamp(value: object, code: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ContractValidationError(code)


def _require_fixture_boundary(
    data_state: DataState,
    is_synthetic: object,
    external_execution_allowed: object,
) -> None:
    if not isinstance(is_synthetic, bool):
        raise ContractValidationError("synthetic_marker_required")
    if external_execution_allowed is not False:
        raise ContractValidationError("external_execution_forbidden")
    fixture_state = data_state in {DataState.FIXTURE, DataState.MOCK}
    if fixture_state is not is_synthetic:
        raise ContractValidationError("synthetic_state_mismatch")


@dataclass(frozen=True)
class SourceRef:
    """Scoped source identity with explicit version and classification."""

    id: UUID
    scope: ScopeRef
    source_kind: str
    source_version: str
    data_state: DataState
    sensitivity: Sensitivity
    is_synthetic: bool
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "source_ref_id_required")
        if not isinstance(self.scope, ScopeRef):
            raise ContractValidationError("scope_required")
        _require_identifier(self.source_kind, "source_kind_required")
        _require_identifier(self.source_version, "source_version_required")
        _require_enum(self.data_state, DataState, "data_state_required")
        _require_enum(self.sensitivity, Sensitivity, "sensitivity_required")
        _require_fixture_boundary(
            self.data_state,
            self.is_synthetic,
            self.external_execution_allowed,
        )


@dataclass(frozen=True)
class DataVersionRef:
    """Scoped immutable version reference tied to one source."""

    id: UUID
    scope: ScopeRef
    source_ref_id: UUID
    version_no: int
    data_state: DataState
    sensitivity: Sensitivity
    is_synthetic: bool
    external_execution_allowed: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "data_version_id_required")
        if not isinstance(self.scope, ScopeRef):
            raise ContractValidationError("scope_required")
        _require_uuid(self.source_ref_id, "source_ref_id_required")
        _require_positive_version(self.version_no)
        _require_enum(self.data_state, DataState, "data_state_required")
        _require_enum(self.sensitivity, Sensitivity, "sensitivity_required")
        _require_fixture_boundary(
            self.data_state,
            self.is_synthetic,
            self.external_execution_allowed,
        )


@dataclass(frozen=True)
class BaseMetadata:
    """Mandatory metadata shared by all future scoped business entities."""

    id: UUID
    scope: ScopeRef
    data_state: DataState
    source_ref_id: UUID
    data_version_id: UUID
    sensitivity: Sensitivity
    is_synthetic: bool
    external_execution_allowed: bool
    created_at: datetime
    updated_at: datetime
    created_by: str

    def __post_init__(self) -> None:
        _require_uuid(self.id, "entity_id_required")
        if not isinstance(self.scope, ScopeRef):
            raise ContractValidationError("scope_required")
        _require_enum(self.data_state, DataState, "data_state_required")
        _require_uuid(self.source_ref_id, "source_ref_id_required")
        _require_uuid(self.data_version_id, "data_version_id_required")
        _require_enum(self.sensitivity, Sensitivity, "sensitivity_required")
        _require_fixture_boundary(
            self.data_state,
            self.is_synthetic,
            self.external_execution_allowed,
        )
        _require_aware_timestamp(self.created_at, "created_at_required")
        _require_aware_timestamp(self.updated_at, "updated_at_required")
        if self.updated_at < self.created_at:
            raise ContractValidationError("timestamp_order_invalid")
        _require_identifier(self.created_by, "created_by_required")


def assert_same_scope(*scoped_contracts: object) -> ScopeRef:
    """Return the shared scope or reject missing/cross-scope contracts."""

    scopes = [getattr(contract, "scope", None) for contract in scoped_contracts]
    if not scopes or any(not isinstance(scope, ScopeRef) for scope in scopes):
        raise ContractValidationError("scope_required")
    first = scopes[0]
    if any(scope != first for scope in scopes[1:]):
        raise ContractValidationError("cross_scope_forbidden")
    return first


def assert_metadata_lineage(
    source: SourceRef,
    version: DataVersionRef,
    metadata: BaseMetadata,
) -> None:
    """Reject a source/version/entity chain that is missing or mismatched."""

    assert_same_scope(source, version, metadata)
    if version.source_ref_id != source.id or metadata.source_ref_id != source.id:
        raise ContractValidationError("source_lineage_mismatch")
    if metadata.data_version_id != version.id:
        raise ContractValidationError("version_lineage_mismatch")
    if not (source.is_synthetic == version.is_synthetic == metadata.is_synthetic):
        raise ContractValidationError("synthetic_lineage_mismatch")
