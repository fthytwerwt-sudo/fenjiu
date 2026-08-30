"""Preset planning contracts for the Video Orchestrator."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from core.application.video_orchestrator import PresetName, ProviderAdapterError, TaskType, build_preset_plan
from workflows.video_pipeline import VideoPipelineRunner


class VideoOrchestratorPresetTests(unittest.TestCase):
    def test_nepali_product_ad_uses_aidge_then_minimax_and_ffmpeg(self) -> None:
        plan = build_preset_plan(PresetName.NEPALI_PRODUCT_AD, has_talking_person=False)
        self.assertEqual(
            [step.capability_id for step in plan.steps],
            ["product_video", "nepali_tts", "final_assembly"],
        )

    def test_nepali_product_ad_adds_lip_sync_only_for_talking_person(self) -> None:
        plan = build_preset_plan(PresetName.NEPALI_PRODUCT_AD, has_talking_person=True)
        self.assertIn("lip_sync", [step.capability_id for step in plan.steps])

    def test_nepali_talking_video_has_full_localization_chain(self) -> None:
        plan = build_preset_plan(PresetName.NEPALI_TALKING_VIDEO)
        self.assertEqual(
            [step.capability_id for step in plan.steps],
            ["source_asr", "translate_nepali", "nepali_tts", "lip_sync", "final_assembly"],
        )

    def test_story_video_uses_wan_and_optional_nepali_voice(self) -> None:
        plan = build_preset_plan(PresetName.STORY_VIDEO, language="ne")
        self.assertEqual(
            [step.capability_id for step in plan.steps],
            ["story_video", "nepali_tts", "final_assembly"],
        )

    def test_nepali_talking_pipeline_executes_all_steps_with_synthetic_runtime(self) -> None:
        class FakeOrchestrator:
            def __init__(self):
                self.tasks = []

            def execute(self, request):
                self.tasks.append(request.task)
                if request.task is TaskType.SOURCE_ASR:
                    return {"result": {"output_text": "你好"}}
                if request.task is TaskType.TRANSLATE_NEPALI:
                    return {"result": {"output_text": "नमस्कार"}}
                output = request.metadata.get("output_path")
                if output:
                    path = Path(output)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b"synthetic")
                return {"result": {"status": "TECH_QC_PASSED"}}

        class SyntheticRunner(VideoPipelineRunner):
            @staticmethod
            def _duration(path):
                return 1.0

        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                fake = FakeOrchestrator()
                result = SyntheticRunner(fake).run(
                    PresetName.NEPALI_TALKING_VIDEO,
                    execute=True,
                    cost_approved=True,
                    media_upload_approved=True,
                    source_video="inputs/video_orchestrator/source.mp4",
                    max_cost_cny=2.0,
                    step_costs={
                        "source_asr": 0.5,
                        "translate_nepali": 0.5,
                        "nepali_tts": 0.5,
                        "lip_sync": 0.5,
                    },
                )
                self.assertEqual(
                    fake.tasks,
                    [
                        TaskType.SOURCE_ASR,
                        TaskType.TRANSLATE_NEPALI,
                        TaskType.NEPALI_VOICE,
                        TaskType.LIP_SYNC,
                        TaskType.FINAL_ASSEMBLY,
                    ],
                )
                self.assertEqual(result["next_state"], "HUMAN_REVIEW_REQUIRED")
                self.assertTrue((Path(tmp) / result["final_output"]).is_file())
            finally:
                os.chdir(previous)

    def test_pipeline_blocks_aggregate_cost_before_any_provider_call(self) -> None:
        class FakeOrchestrator:
            def __init__(self):
                self.calls = 0

            def execute(self, request):
                self.calls += 1
                return {}

        fake = FakeOrchestrator()
        with self.assertRaisesRegex(ProviderAdapterError, "COST_BLOCKED"):
            VideoPipelineRunner(fake).run(
                PresetName.NEPALI_TALKING_VIDEO,
                execute=True,
                cost_approved=True,
                media_upload_approved=True,
                source_video="inputs/video_orchestrator/source.mp4",
                max_cost_cny=1.0,
                step_costs={
                    "source_asr": 0.5,
                    "translate_nepali": 0.5,
                    "nepali_tts": 0.5,
                    "lip_sync": 0.5,
                },
            )
        self.assertEqual(fake.calls, 0)


if __name__ == "__main__":
    unittest.main()
