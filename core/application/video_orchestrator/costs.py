"""Pre-call provider budget validation."""

from __future__ import annotations

from core.application.video_orchestrator.contracts import ErrorCode, OrchestratorRequest, ProviderAdapterError


_LOCAL_ADAPTERS = {"ffmpeg_assembly"}


def estimate_provider_cost(request: OrchestratorRequest, adapter_id: str) -> float | None:
    if adapter_id in _LOCAL_ADAPTERS:
        return 0.0
    supplied_value = request.metadata.get("estimated_provider_cost_cny")
    supplied = (
        float(supplied_value)
        if isinstance(supplied_value, (int, float))
        and not isinstance(supplied_value, bool)
        and supplied_value > 0
        else None
    )
    calculated: float | None = None
    if adapter_id == "aidge_video_generation":
        rate = 2.5 if (request.quality or "720p").lower() == "1080p" else 1.4
        calculated = float(request.duration or 5) * rate
    elif adapter_id == "minimax_speech_2_8_hd":
        calculated = len(request.script) / 10_000 * 3.5
    elif adapter_id == "minimax_speech_2_8_turbo":
        calculated = len(request.script) / 10_000 * 2.0
    elif adapter_id == "alibaba_videoretalk":
        duration = request.metadata.get("duration_seconds")
        if isinstance(duration, (int, float)) and not isinstance(duration, bool) and duration > 0:
            calculated = float(duration) * 0.08
    if calculated is not None and supplied is not None:
        return max(calculated, supplied)
    return calculated if calculated is not None else supplied


def require_cost_budget(request: OrchestratorRequest, adapter_id: str) -> float:
    estimate = estimate_provider_cost(request, adapter_id)
    maximum = request.metadata.get("max_cost_cny")
    if estimate is None:
        raise ProviderAdapterError(
            ErrorCode.COST_BLOCKED,
            "provider cost estimate is required before execution",
            provider=adapter_id,
        )
    if estimate == 0:
        return estimate
    if not isinstance(maximum, (int, float)) or isinstance(maximum, bool) or maximum <= 0:
        raise ProviderAdapterError(
            ErrorCode.COST_BLOCKED,
            "positive maximum cost is required before execution",
            provider=adapter_id,
        )
    if estimate > float(maximum):
        raise ProviderAdapterError(
            ErrorCode.COST_BLOCKED,
            "estimated provider cost exceeds approved maximum",
            provider=adapter_id,
        )
    return estimate
