"""Runtime port kept separate from the P07 synthetic-only VideoPort."""

from __future__ import annotations

from typing import Any, Protocol

from core.application.video_orchestrator.contracts import OrchestratorRequest, ProviderExecutionResult


class VideoRuntimePort(Protocol):
    def doctor(self) -> dict[str, Any]:
        ...

    def execute(self, request: OrchestratorRequest, adapter_id: str) -> ProviderExecutionResult:
        ...
