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
    inventory_writeback: bool = False
    real_crawl: bool = False
    real_video: bool = False
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        if self.any_sensitive_action_enabled():
            raise ValueError("sensitive action flags must remain disabled")

    def any_sensitive_action_enabled(self) -> bool:
        """Return true if any action that can cross the local boundary is on."""

        return any(
            (
                self.external_send,
                self.public_publish,
                self.real_quote,
                self.payment,
                self.order_create,
                self.refund,
                self.inventory_writeback,
                self.real_crawl,
                self.real_video,
                self.external_execution_allowed,
                self.business_external_ready,
            )
        )


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
