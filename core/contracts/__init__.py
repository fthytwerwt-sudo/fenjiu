"""Stable contracts shared across packages."""

from core.contracts.errors import (
    BoundaryViolationError,
    ContractValidationError,
    FenjiuSkeletonError,
)
from core.contracts.metadata import (
    BaseMetadata,
    DataState,
    DataVersionRef,
    Sensitivity,
    SourceRef,
    assert_metadata_lineage,
    assert_same_scope,
)
from core.contracts.scope import (
    BusinessLineContract,
    ExecutionPolicy,
    ProjectContract,
    ScopeRef,
    TenantContract,
    default_execution_policy,
    synthetic_scope,
)

__all__ = [
    "BoundaryViolationError",
    "BusinessLineContract",
    "BaseMetadata",
    "ContractValidationError",
    "DataState",
    "DataVersionRef",
    "ExecutionPolicy",
    "FenjiuSkeletonError",
    "ProjectContract",
    "ScopeRef",
    "Sensitivity",
    "SourceRef",
    "TenantContract",
    "assert_metadata_lineage",
    "assert_same_scope",
    "default_execution_policy",
    "synthetic_scope",
]
