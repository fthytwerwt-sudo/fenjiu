"""Synthetic scope and execution-policy contracts.

These contracts contain no real business values. They exist only to keep future
scope propagation and external-action defaults explicit.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScopeRef:
    """Minimal non-business scope reference required by future commands."""

    tenant_id: str
    project_id: str
    business_line_id: str
    correlation_id: str


@dataclass(frozen=True)
class ExecutionPolicy:
    """Default external-action gates for the current skeleton."""

    external_send: bool = False
    public_publish: bool = False
    real_quote: bool = False
    payment: bool = False
    order_create: bool = False
    refund: bool = False
    external_execution_allowed: bool = False
    business_external_ready: bool = False


def synthetic_scope() -> ScopeRef:
    """Return a synthetic-only scope for tests and fixtures."""

    return ScopeRef(
        tenant_id="synthetic_tenant",
        project_id="synthetic_project",
        business_line_id="synthetic_business_line",
        correlation_id="synthetic_correlation",
    )


def default_execution_policy() -> ExecutionPolicy:
    """Return the fail-closed external-action policy."""

    return ExecutionPolicy()
