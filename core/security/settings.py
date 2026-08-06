"""Typed static settings for the local-only control plane.

This module deliberately has no environment, file, or secret-reference loader.
Runtime configuration inputs cannot enable capabilities in Phase 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ConfigStatus(str, Enum):
    """Safe configuration states without raw error or configuration details."""

    STATIC_DISABLED = "static_disabled"
    UNKNOWN_REJECTED = "unknown_rejected"
    INVALID_REJECTED = "invalid_rejected"


@dataclass(frozen=True)
class ControlPlaneSettings:
    """Typed settings whose capabilities cannot be enabled by constructor input."""

    config_status: ConfigStatus = ConfigStatus.STATIC_DISABLED
    capability_status: str = field(default="local_control_plane", init=False)
    broker_available: bool = field(default=False, init=False)
    provider_available: bool = field(default=False, init=False)
    real_configuration_available: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.config_status, ConfigStatus):
            object.__setattr__(self, "config_status", ConfigStatus.INVALID_REJECTED)

    def is_ready(self) -> bool:
        """Return false until a later task supplies approved dependency contracts."""

        return (
            self.broker_available
            and self.provider_available
            and self.real_configuration_available
        )


def default_settings() -> ControlPlaneSettings:
    """Return static, local-only settings without consulting external input."""

    return ControlPlaneSettings()


def fail_closed_settings(status: object) -> ControlPlaneSettings:
    """Represent unknown or invalid input without reading or retaining its value."""

    if status is ConfigStatus.UNKNOWN_REJECTED:
        safe_status = ConfigStatus.UNKNOWN_REJECTED
    else:
        safe_status = ConfigStatus.INVALID_REJECTED
    return ControlPlaneSettings(config_status=safe_status)
