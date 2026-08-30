"""Thin preset runner over the Video Orchestrator application service."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Any
from uuid import uuid4

from core.application.video_orchestrator import (
    ErrorCode,
    OrchestratorRequest,
    PresetName,
    ProviderAdapterError,
    TaskType,
    VideoOrchestrator,
    build_preset_plan,
)
from core.application.video_orchestrator.contracts import safe_ref
from core.application.video_orchestrator.security import resolve_output_path


class VideoPipelineRunner:
    def __init__(self, orchestrator: VideoOrchestrator) -> None:
        self.orchestrator = orchestrator

    def run(
        self,
        preset: PresetName,
        *,
        execute: bool,
        cost_approved: bool,
        media_upload_approved: bool,
        product_images: tuple[str, ...] = (),
        product_title: str = "",
        prompt: str = "",
        script: str = "",
        source_video: str | None = None,
        reference_image: str | None = None,
        language: str = "ne",
        has_talking_person: bool = False,
        fallback_approved: bool = False,
        approved_providers: tuple[str, ...] = (),
        max_cost_cny: float | None = None,
        step_costs: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        plan = build_preset_plan(
            preset,
            language=language,
            has_talking_person=has_talking_person,
        )
        if not execute:
            return plan.safe_summary()
        if not cost_approved:
            raise ProviderAdapterError(ErrorCode.COST_BLOCKED, "pipeline cost approval required", provider="video_pipeline")
        normalized_costs = self._preflight_costs(
            plan,
            preset=preset,
            script=script,
            fallback_approved=fallback_approved,
            approved_providers=approved_providers,
            max_cost_cny=max_cost_cny,
            step_costs=step_costs or {},
        )
        run_label = f"{preset.value}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
        common = {
            "fallback_approved": fallback_approved,
            "approved_providers": approved_providers,
            "media_upload_approved": media_upload_approved,
            "step_costs": normalized_costs,
        }
        if preset is PresetName.NEPALI_TALKING_VIDEO:
            return self._run_nepali_talking(
                run_label,
                source_video=source_video,
                reference_image=reference_image,
                common=common,
            )
        if preset is PresetName.NEPALI_PRODUCT_AD:
            return self._run_nepali_product_ad(
                run_label,
                product_images=product_images,
                product_title=product_title,
                script=script,
                has_talking_person=has_talking_person,
                common=common,
            )
        if preset is PresetName.STORY_VIDEO:
            return self._run_story(
                run_label,
                prompt=prompt,
                script=script,
                language=language,
                common=common,
            )
        raise ProviderAdapterError(ErrorCode.UNSUPPORTED_CAPABILITY, "pipeline preset unsupported", provider="video_pipeline")

    def _run_nepali_talking(
        self,
        run_label: str,
        *,
        source_video: str | None,
        reference_image: str | None,
        common: dict[str, Any],
    ) -> dict[str, Any]:
        if not source_video:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "nepali_talking_video requires source video", provider="video_pipeline")
        asr = self.orchestrator.execute(
            OrchestratorRequest(
                task=TaskType.SOURCE_ASR,
                source_video=source_video,
                execute=True,
                cost_approved=True,
                metadata={**self._step_metadata(common, "source_asr"), "return_text": True},
            )
        )
        source_text = self._required_output_text(asr, "ASR")
        translation = self.orchestrator.execute(
            OrchestratorRequest(
                task=TaskType.TRANSLATE_NEPALI,
                language="ne",
                script=source_text,
                execute=True,
                cost_approved=True,
                metadata={
                    **self._step_metadata(common, "translate_nepali"),
                    "return_text": True,
                    "source_language": "zh",
                },
            )
        )
        nepali_text = self._required_output_text(translation, "translation")
        audio = resolve_output_path(f"{run_label}/nepali_voice.mp3", provider="video_pipeline")
        self.orchestrator.execute(
            OrchestratorRequest(
                task=TaskType.NEPALI_VOICE,
                language="ne",
                script=nepali_text,
                execute=True,
                cost_approved=True,
                metadata={**self._step_metadata(common, "nepali_tts"), "output_path": str(audio)},
            )
        )
        lip_synced = resolve_output_path(f"{run_label}/lip_synced.mp4", provider="video_pipeline")
        self.orchestrator.execute(
            OrchestratorRequest(
                task=TaskType.LIP_SYNC,
                source_video=source_video,
                source_audio=str(audio),
                reference_image=reference_image,
                execute=True,
                cost_approved=True,
                metadata={**self._step_metadata(common, "lip_sync"), "output_path": str(lip_synced)},
            )
        )
        return self._subtitle_and_assemble(run_label, lip_synced, nepali_text)

    def _run_nepali_product_ad(
        self,
        run_label: str,
        *,
        product_images: tuple[str, ...],
        product_title: str,
        script: str,
        has_talking_person: bool,
        common: dict[str, Any],
    ) -> dict[str, Any]:
        if not product_images or not product_title or not script:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "nepali_product_ad requires images, title, and Nepali script", provider="video_pipeline")
        base_video = resolve_output_path(f"{run_label}/product_video.mp4", provider="video_pipeline")
        self.orchestrator.execute(
            OrchestratorRequest(
                task=TaskType.PRODUCT_AD,
                product_images=product_images,
                product_title=product_title,
                execute=True,
                cost_approved=True,
                duration=5,
                ratio="9:16",
                quality="720p",
                metadata={
                    **self._step_metadata(common, "product_video", fallback_capability="wan3_video"),
                    "output_path": str(base_video),
                },
            )
        )
        audio = resolve_output_path(f"{run_label}/nepali_voice.mp3", provider="video_pipeline")
        self.orchestrator.execute(
            OrchestratorRequest(
                task=TaskType.NEPALI_VOICE,
                language="ne",
                script=script,
                execute=True,
                cost_approved=True,
                metadata={**self._step_metadata(common, "nepali_tts"), "output_path": str(audio)},
            )
        )
        video_for_assembly = base_video
        if has_talking_person:
            lip_synced = resolve_output_path(f"{run_label}/lip_synced.mp4", provider="video_pipeline")
            self.orchestrator.execute(
                OrchestratorRequest(
                    task=TaskType.LIP_SYNC,
                    source_video=str(base_video),
                    source_audio=str(audio),
                    execute=True,
                    cost_approved=True,
                    metadata={**self._step_metadata(common, "lip_sync"), "output_path": str(lip_synced)},
                )
            )
            video_for_assembly = lip_synced
        return self._subtitle_and_assemble(run_label, video_for_assembly, script, audio_path=audio)

    def _run_story(
        self,
        run_label: str,
        *,
        prompt: str,
        script: str,
        language: str,
        common: dict[str, Any],
    ) -> dict[str, Any]:
        if not prompt:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "story_video requires prompt", provider="video_pipeline")
        story_video = resolve_output_path(f"{run_label}/story_video.mp4", provider="video_pipeline")
        self.orchestrator.execute(
            OrchestratorRequest(
                task=TaskType.STORY_VIDEO,
                prompt=prompt,
                execute=True,
                cost_approved=True,
                metadata={**self._step_metadata(common, "story_video"), "output_path": str(story_video)},
            )
        )
        if language.lower() not in {"ne", "nepali", "ne-np"} or not script:
            return {
                "preset": PresetName.STORY_VIDEO.value,
                "final_output": self._relative_output(story_video),
                "next_state": "HUMAN_REVIEW_REQUIRED",
            }
        audio = resolve_output_path(f"{run_label}/nepali_voice.mp3", provider="video_pipeline")
        self.orchestrator.execute(
            OrchestratorRequest(
                task=TaskType.NEPALI_VOICE,
                language="ne",
                script=script,
                execute=True,
                cost_approved=True,
                metadata={**self._step_metadata(common, "nepali_tts"), "output_path": str(audio)},
            )
        )
        return self._subtitle_and_assemble(run_label, story_video, script, audio_path=audio)

    def _subtitle_and_assemble(
        self,
        run_label: str,
        video_path: Path,
        subtitle_text: str,
        *,
        audio_path: Path | None = None,
    ) -> dict[str, Any]:
        duration = self._duration(video_path)
        subtitle = resolve_output_path(f"{run_label}/subtitles_ne.srt", provider="video_pipeline")
        subtitle.parent.mkdir(parents=True, exist_ok=True)
        subtitle.write_text(
            "1\n00:00:00,000 --> " + self._srt_time(duration) + "\n" + subtitle_text.strip() + "\n",
            encoding="utf-8",
        )
        final = resolve_output_path(f"{run_label}/final.mp4", provider="video_pipeline")
        self.orchestrator.execute(
            OrchestratorRequest(
                task=TaskType.FINAL_ASSEMBLY,
                source_video=str(video_path),
                source_audio=str(audio_path) if audio_path else None,
                execute=True,
                cost_approved=True,
                metadata={"output_path": str(final), "subtitle_path": str(subtitle)},
            )
        )
        return {
            "preset": run_label.split("-", 1)[0],
            "final_output": self._relative_output(final),
            "subtitle_output": self._relative_output(subtitle),
            "output_ref": safe_ref(str(final)),
            "next_state": "HUMAN_REVIEW_REQUIRED",
        }

    @staticmethod
    def _required_output_text(result: dict[str, Any], step: str) -> str:
        text = ((result.get("result") or {}).get("output_text"))
        if not isinstance(text, str) or not text.strip():
            raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, f"{step} produced no text", provider="video_pipeline")
        return text

    @staticmethod
    def _preflight_costs(
        plan,
        *,
        preset: PresetName,
        script: str,
        fallback_approved: bool,
        approved_providers: tuple[str, ...],
        max_cost_cny: float | None,
        step_costs: dict[str, float],
    ) -> dict[str, float]:
        if not isinstance(max_cost_cny, (int, float)) or isinstance(max_cost_cny, bool) or max_cost_cny <= 0:
            raise ProviderAdapterError(
                ErrorCode.COST_BLOCKED,
                "positive pipeline maximum cost is required before execution",
                provider="video_pipeline",
            )
        required = {
            step.capability_id
            for step in plan.steps
            if step.capability_id != "final_assembly"
        }
        if preset is PresetName.STORY_VIDEO and not script:
            required.discard("nepali_tts")
        if fallback_approved and "wan3_video" in approved_providers:
            required.add("wan3_video")
        normalized: dict[str, float] = {}
        for capability in sorted(required):
            amount = step_costs.get(capability)
            if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
                raise ProviderAdapterError(
                    ErrorCode.COST_BLOCKED,
                    f"positive cost estimate required for pipeline capability {capability}",
                    provider="video_pipeline",
                )
            normalized[capability] = float(amount)
        if sum(normalized.values()) > float(max_cost_cny):
            raise ProviderAdapterError(
                ErrorCode.COST_BLOCKED,
                "pipeline estimated cost exceeds approved maximum",
                provider="video_pipeline",
            )
        return normalized

    @staticmethod
    def _step_metadata(
        common: dict[str, Any],
        capability: str,
        *,
        fallback_capability: str | None = None,
    ) -> dict[str, Any]:
        step_costs = common["step_costs"]
        estimate = step_costs[capability]
        fallback_estimate = step_costs.get(fallback_capability) if fallback_capability else None
        maximum = estimate + (fallback_estimate or 0.0)
        return {
            "fallback_approved": common["fallback_approved"],
            "approved_providers": common["approved_providers"],
            "media_upload_approved": common["media_upload_approved"],
            "estimated_provider_cost_cny": estimate,
            "fallback_estimated_cost_cny": fallback_estimate,
            "max_cost_cny": maximum,
        }

    @staticmethod
    def _duration(path: Path) -> float:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "pipeline video duration probe failed", provider="video_pipeline")
        return max(0.1, float(result.stdout.strip()))

    @staticmethod
    def _srt_time(seconds: float) -> str:
        milliseconds = int(round(seconds * 1000))
        hours, milliseconds = divmod(milliseconds, 3_600_000)
        minutes, milliseconds = divmod(milliseconds, 60_000)
        whole_seconds, milliseconds = divmod(milliseconds, 1000)
        return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"

    @staticmethod
    def _relative_output(path: Path) -> str:
        try:
            return str(path.relative_to(Path.cwd()))
        except ValueError:
            return f"output:{path.name}"
