"""Provider-neutral orchestration over business capabilities."""

from __future__ import annotations

from typing import Any

from core.application.video_orchestrator.contracts import (
    ErrorCode,
    OrchestratorRequest,
    ProviderAdapterError,
    ProviderFailure,
    TaskType,
)
from core.application.video_orchestrator.ports import VideoRuntimePort
from core.application.video_orchestrator.costs import estimate_provider_cost, require_cost_budget
from core.application.video_orchestrator.registry import CapabilityRegistry
from core.application.video_orchestrator.router import VideoRouter


class VideoOrchestrator:
    def __init__(
        self,
        runtime: VideoRuntimePort | None = None,
        registry: CapabilityRegistry | None = None,
    ) -> None:
        self.runtime = runtime
        self.registry = registry or CapabilityRegistry.default()
        self.router = VideoRouter(self.registry)

    def doctor(self) -> dict[str, Any]:
        if self.runtime is None:
            return {
                "schema_version": "video_orchestrator.doctor.v1",
                "providers": {},
                "runtime_configured": False,
                "external_calls_made": 0,
            }
        result = dict(self.runtime.doctor())
        result["runtime_configured"] = True
        return result

    def plan(self, request: OrchestratorRequest) -> dict[str, Any]:
        route = self.router.route(request)
        return {
            "request": request.safe_summary(),
            "route": route.safe_summary(),
            "execution": "PLAN_ONLY",
            "estimated_provider_cost_cny": estimate_provider_cost(request, route.primary_adapter),
            "human_review_required": True,
        }

    def execute(self, request: OrchestratorRequest) -> dict[str, Any]:
        if not request.execute:
            return self.plan(request)
        if not request.cost_approved and request.task is not TaskType.FINAL_ASSEMBLY:
            raise ProviderAdapterError(
                ErrorCode.COST_BLOCKED,
                "explicit cost approval is required",
                provider="video_orchestrator",
            )
        if self.runtime is None:
            raise ProviderAdapterError(
                ErrorCode.PROVIDER_NOT_ENABLED,
                "video runtime is not configured",
                provider="video_orchestrator",
            )
        route = self.router.route(request)
        primary_estimate = require_cost_budget(request, route.primary_adapter)
        try:
            result = self.runtime.execute(request, route.primary_adapter)
            return self._execution_summary(
                request,
                route.safe_summary(),
                result.safe_summary(include_output_text=request.metadata.get("return_text") is True),
                fallback_used=False,
            )
        except ProviderAdapterError as exc:
            failure = ProviderFailure(exc.provider, exc.code, str(exc), exc.raw_provider_code)
            if route.fallback_adapter and self.router.may_fallback(failure):
                approved_providers = set(request.metadata.get("approved_providers", []))
                max_cost = request.metadata.get("max_cost_cny")
                fallback_estimate = request.metadata.get("fallback_estimated_cost_cny")
                if (
                    request.metadata.get("fallback_approved") is not True
                    or route.fallback_adapter not in approved_providers
                    or not isinstance(max_cost, (int, float))
                    or isinstance(max_cost, bool)
                    or max_cost <= 0
                    or not isinstance(fallback_estimate, (int, float))
                    or isinstance(fallback_estimate, bool)
                    or fallback_estimate <= 0
                    or primary_estimate + float(fallback_estimate) > float(max_cost)
                ):
                    raise ProviderAdapterError(
                        ErrorCode.COST_BLOCKED,
                        "fallback provider and maximum cost require separate approval",
                        provider="video_orchestrator",
                        raw_provider_code=exc.code.value,
                    ) from exc
                result = self.runtime.execute(request, route.fallback_adapter)
                route_summary = route.safe_summary()
                route_summary["fallback_reason"] = exc.code.value
                return self._execution_summary(
                    request,
                    route_summary,
                    result.safe_summary(include_output_text=request.metadata.get("return_text") is True),
                    fallback_used=True,
                )
            raise

    def _execution_summary(
        self,
        request: OrchestratorRequest,
        route: dict[str, Any],
        result: dict[str, Any],
        *,
        fallback_used: bool,
    ) -> dict[str, Any]:
        return {
            "request": request.safe_summary(),
            "route": route,
            "execution": "SUBMITTED_OR_GENERATED",
            "fallback_used": fallback_used,
            "result": result,
            "next_state": "HUMAN_REVIEW_REQUIRED",
        }
