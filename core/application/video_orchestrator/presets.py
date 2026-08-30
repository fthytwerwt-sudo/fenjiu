"""Safe, provider-neutral pipeline presets."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PresetName(str, Enum):
    NEPALI_PRODUCT_AD = "nepali_product_ad"
    NEPALI_TALKING_VIDEO = "nepali_talking_video"
    STORY_VIDEO = "story_video"


@dataclass(frozen=True)
class PipelineStep:
    capability_id: str
    optional: bool = False


@dataclass(frozen=True)
class PipelinePlan:
    preset: PresetName
    steps: tuple[PipelineStep, ...]
    human_review_required: bool = True

    def safe_summary(self) -> dict[str, object]:
        return {
            "preset": self.preset.value,
            "steps": [
                {"capability_id": step.capability_id, "optional": step.optional}
                for step in self.steps
            ],
            "human_review_required": self.human_review_required,
        }


def build_preset_plan(
    preset: PresetName,
    *,
    language: str = "ne",
    has_talking_person: bool = False,
) -> PipelinePlan:
    if preset is PresetName.NEPALI_PRODUCT_AD:
        steps = [PipelineStep("product_video"), PipelineStep("nepali_tts")]
        if has_talking_person:
            steps.append(PipelineStep("lip_sync"))
        steps.append(PipelineStep("final_assembly"))
        return PipelinePlan(preset, tuple(steps))
    if preset is PresetName.NEPALI_TALKING_VIDEO:
        return PipelinePlan(
            preset,
            (
                PipelineStep("source_asr"),
                PipelineStep("translate_nepali"),
                PipelineStep("nepali_tts"),
                PipelineStep("lip_sync"),
                PipelineStep("final_assembly"),
            ),
        )
    if preset is PresetName.STORY_VIDEO:
        steps = [PipelineStep("story_video")]
        if language.lower() in {"ne", "ne-np", "nepali"}:
            steps.append(PipelineStep("nepali_tts"))
        steps.append(PipelineStep("final_assembly"))
        return PipelinePlan(preset, tuple(steps))
    raise ValueError("preset_unknown")
