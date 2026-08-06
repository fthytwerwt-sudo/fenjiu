"""Fake-only adapter capability metadata."""

from dataclasses import dataclass

from core.application.interfaces import CapabilityStatus


@dataclass(frozen=True)
class AdapterCapability:
    """Declared capability state for a provider-facing package."""

    name: str
    status: CapabilityStatus = CapabilityStatus.PLANNED_FAKE_ONLY


def fake_only_capability(name: str) -> AdapterCapability:
    """Return fake-only capability metadata."""

    return AdapterCapability(name=name)
