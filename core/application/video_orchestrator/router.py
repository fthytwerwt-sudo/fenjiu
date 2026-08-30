"""Task classifier and provider routing rules."""

from __future__ import annotations

from core.application.video_orchestrator.contracts import (
    ErrorCode,
    OrchestratorContractError,
    OrchestratorRequest,
    ProviderFailure,
    RouteDecision,
    TaskType,
)
from core.application.video_orchestrator.registry import CapabilityRegistry


class VideoRouter:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry

    def route(self, request: OrchestratorRequest) -> RouteDecision:
        if request.task is TaskType.PRODUCT_AD:
            if not 1 <= len(request.product_images) <= 6 or not request.product_title:
                raise OrchestratorContractError("product_ad_requires_1_to_6_images_and_title")
            return self._from_capability("product_video", "product_ad_with_product_images")
        if request.task in {TaskType.STORY_VIDEO, TaskType.FAST_STORY_VIDEO}:
            if not request.prompt:
                raise OrchestratorContractError("story_video_prompt_required")
            capability = (
                "fast_story_video"
                if request.speed_priority or request.task is TaskType.FAST_STORY_VIDEO
                else "story_video"
            )
            return self._from_capability(capability, "story_video_route")
        if request.task is TaskType.SHORT_PRODUCT_SCENE:
            if not request.prompt:
                raise OrchestratorContractError("short_scene_prompt_required")
            record = self.registry.get("short_reference_video")
            if request.reference_videos:
                adapter = "happyhorse_1_1_r2v"
            elif request.reference_images:
                adapter = "happyhorse_1_1_i2v"
            else:
                adapter = "happyhorse_1_1_t2v"
            return RouteDecision(record.capability_id, adapter, record.fallback, "short_reference_input_shape")
        if request.task is TaskType.NEPALI_VOICE:
            if request.language.lower() not in {"ne", "ne-np", "nepali"} or not request.script:
                raise OrchestratorContractError("nepali_voice_requires_ne_language_and_script")
            return self._from_capability("nepali_tts", "primary_nepali_tts")
        if request.task is TaskType.TRANSLATE_NEPALI:
            if request.language.lower() not in {"ne", "ne-np", "nepali"} or not request.script:
                raise OrchestratorContractError("translate_nepali_requires_ne_language_and_script")
            return self._from_capability("translate_nepali", "zh_to_ne_translation")
        if request.task is TaskType.SOURCE_ASR:
            if not request.source_audio and not request.source_video:
                raise OrchestratorContractError("asr_source_required")
            return self._from_capability("source_asr", "source_transcription")
        if request.task is TaskType.LIP_SYNC:
            if not request.source_video or not request.source_audio:
                raise OrchestratorContractError("lip_sync_video_and_audio_required")
            return self._from_capability("lip_sync", "existing_video_new_audio")
        if request.task is TaskType.FINAL_ASSEMBLY:
            return self._from_capability("final_assembly", "local_final_assembly")
        raise OrchestratorContractError("task_type_unknown")

    def _from_capability(self, capability_id: str, reason: str) -> RouteDecision:
        record = self.registry.get(capability_id)
        return RouteDecision(
            capability_id=record.capability_id,
            primary_adapter=record.primary_adapter,
            fallback_adapter=record.fallback,
            reason=reason,
        )

    def may_fallback(self, failure: ProviderFailure) -> bool:
        return failure.code in {
            ErrorCode.PROVIDER_NOT_ENABLED,
            ErrorCode.PERMISSION_DENIED,
            ErrorCode.UNSUPPORTED_CAPABILITY,
        }
