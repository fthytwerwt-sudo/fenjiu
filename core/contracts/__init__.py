"""Stable contracts shared across packages."""

from core.contracts.errors import BoundaryViolationError, FenjiuSkeletonError
from core.contracts.scope import (
    ExecutionPolicy,
    ScopeRef,
    default_execution_policy,
    synthetic_scope,
)

__all__ = [
    "BoundaryViolationError",
    "ExecutionPolicy",
    "FenjiuSkeletonError",
    "ScopeRef",
    "default_execution_policy",
    "synthetic_scope",
]
