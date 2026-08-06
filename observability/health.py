"""Non-sensitive liveness and readiness contracts."""

from __future__ import annotations

import re

from core.security import ControlPlaneSettings, default_settings

_SAFE_COMPONENT = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


def _component_name(component: str) -> str:
    if _SAFE_COMPONENT.fullmatch(component):
        return component
    return "unknown"


def liveness_payload(component: str) -> dict[str, object]:
    """Report process health without scope, configuration, path, or secret data."""

    return {
        "component": _component_name(component),
        "check": "liveness",
        "status": "ok",
        "live": True,
        "capability_status": "local_control_plane",
    }


def readiness_payload(
    component: str,
    settings: ControlPlaneSettings | None = None,
) -> dict[str, object]:
    """Report fail-closed readiness using only a stable, non-sensitive reason code."""

    active_settings = settings if settings is not None else default_settings()
    ready = active_settings.is_ready()
    return {
        "component": _component_name(component),
        "check": "readiness",
        "status": "ready" if ready else "not_ready",
        "ready": ready,
        "capability_status": "local_control_plane",
        "reason_code": "ready" if ready else "dependencies_unavailable",
    }
