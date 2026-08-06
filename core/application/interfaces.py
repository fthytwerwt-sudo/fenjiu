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
        if self._policy.any_sensitive_action_enabled():
            raise BoundaryViolationError("sensitive actions are disabled by the local control plane")
