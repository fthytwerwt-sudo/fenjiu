"""Typed interfaces for Phase 1 skeleton boundaries."""

from enum import Enum
from typing import Protocol

from core.contracts.errors import BoundaryViolationError
from core.contracts.scope import ExecutionPolicy, ScopeRef


class CapabilityStatus(str, Enum):
    """Capability states allowed before real provider integration."""

    PLANNED_FAKE_ONLY = "planned_fake_only"
    BLOCKED = "blocked"


class PortProbe(Protocol):
    """Minimal fake-first port probe contract."""

    name: str
    status: CapabilityStatus

    def probe(self, scope: ScopeRef) -> CapabilityStatus:
        """Return the current fake-only capability status."""


class ExternalActionGuard:
    """Fail-closed guard shared by future commands."""

    def __init__(self, policy: ExecutionPolicy) -> None:
        self._policy = policy

    def assert_no_external_action(self) -> None:
        if any(
            (
                self._policy.external_send,
                self._policy.public_publish,
                self._policy.real_quote,
                self._policy.payment,
                self._policy.order_create,
                self._policy.refund,
                self._policy.external_execution_allowed,
                self._policy.business_external_ready,
            )
        ):
            raise BoundaryViolationError("external actions are disabled in P01-01")
