"""Unified videoctl command contracts."""

from __future__ import annotations

from io import StringIO
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from apps.videoctl import _write_aidge_probe_state, main
from core.application.video_orchestrator import ErrorCode, ProviderAdapterError, ProviderExecutionResult


class VideoCtlTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, dict]:
        output = StringIO()
        code = main(list(args), stdout=output)
        return code, json.loads(output.getvalue())

    def test_doctor_and_capabilities_are_executable(self) -> None:
        code, doctor = self.run_cli("doctor")
        self.assertEqual(code, 0)
        self.assertIn("aidge_video_generation", doctor["providers"])
        code, capabilities = self.run_cli("capabilities")
        self.assertEqual(code, 0)
        self.assertIn("product_video", capabilities["capabilities"])

    def test_generate_product_ad_returns_aidge_plan_without_external_call(self) -> None:
        code, result = self.run_cli(
            "generate",
            "--task",
            "product_ad",
            "--image",
            "https://assets.example/product.png",
            "--title",
            "Synthetic product",
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["route"]["primary_adapter"], "aidge_video_generation")
        self.assertEqual(result["execution"], "PLAN_ONLY")

    def test_voice_lip_sync_and_pipeline_commands_are_executable(self) -> None:
        code, voice = self.run_cli("voice", "--language", "ne", "--text", "नमस्कार")
        self.assertEqual(code, 0)
        self.assertEqual(voice["route"]["primary_adapter"], "minimax_speech_2_8_hd")

        code, lip_sync = self.run_cli(
            "lip-sync",
            "--video",
            "asset:synthetic-video",
            "--audio",
            "asset:synthetic-audio",
        )
        self.assertEqual(code, 0)
        self.assertEqual(lip_sync["route"]["primary_adapter"], "alibaba_videoretalk")

        code, pipeline = self.run_cli("pipeline", "--preset", "nepali_talking_video")
        self.assertEqual(code, 0)
        self.assertEqual(pipeline["preset"], "nepali_talking_video")

    def test_execute_requires_explicit_cost_approval(self) -> None:
        code, result = self.run_cli(
            "generate",
            "--task",
            "product_ad",
            "--image",
            "https://assets.example/product.png",
            "--title",
            "Synthetic product",
            "--execute",
        )
        self.assertEqual(code, 2)
        self.assertEqual(result["error"]["code"], "COST_BLOCKED")

    def test_aidge_probe_is_plan_only_by_default(self) -> None:
        code, result = self.run_cli("probe-aidge")
        self.assertEqual(code, 0)
        self.assertEqual(result["execution"], "PLAN_ONLY")
        self.assertEqual(result["request"]["duration"], 5)

    def test_aidge_probe_checkpoints_task_id_before_polling(self) -> None:
        class FakeAidge:
            def doctor(self):
                return SimpleNamespace(available=True, error_code=None, probe_status="PROBE_REQUIRED")

            def build_request(self, **kwargs):
                return {"synthetic": True}

            def submit(self, request):
                return ProviderExecutionResult(
                    "aidge_video_generation",
                    "SUBMITTED",
                    task_id="synthetic-checkpoint-task",
                )

            def wait(self, task_id):
                raise ProviderAdapterError(
                    ErrorCode.PROVIDER_TIMEOUT,
                    "synthetic polling timeout",
                    provider="aidge_video_generation",
                )

        class FakeRuntime:
            aidge = FakeAidge()

        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                with patch("apps.videoctl.VideoRuntimeAdapter", return_value=FakeRuntime()):
                    code, result = self.run_cli(
                        "probe-aidge",
                        "--execute",
                        "--approve-cost",
                        "--max-cost-cny",
                        "7",
                    )
                self.assertEqual(code, 2)
                self.assertEqual(result["error"]["code"], ErrorCode.PROVIDER_TIMEOUT.value)
                state_path = Path("outputs/video_orchestrator/aidge_probe_state.json")
                self.assertTrue(state_path.is_file())
                state = json.loads(state_path.read_text(encoding="utf-8"))
                self.assertEqual(state["task_id"], "synthetic-checkpoint-task")
                self.assertEqual(state["status"], "SUBMITTED")
            finally:
                os.chdir(previous)

    def test_aidge_probe_checkpoint_rejects_symlink_destination(self) -> None:
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                outside = Path("outside.json")
                outside.write_text("preserve-me\n", encoding="utf-8")
                state_path = Path("outputs/video_orchestrator/aidge_probe_state.json")
                state_path.parent.mkdir(parents=True)
                state_path.symlink_to(outside.resolve())
                with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.PERMISSION_DENIED.value):
                    _write_aidge_probe_state(task_id="synthetic-task", status="SUBMITTED")
                self.assertEqual(outside.read_text(encoding="utf-8"), "preserve-me\n")
            finally:
                os.chdir(previous)

    def test_translate_asr_and_final_assembly_commands_are_executable_as_plans(self) -> None:
        code, translated = self.run_cli("translate", "--text", "你好")
        self.assertEqual(code, 0)
        self.assertEqual(translated["route"]["primary_adapter"], "qwen_mt")
        code, asr = self.run_cli("asr", "--source", "https://assets.example/source.wav")
        self.assertEqual(code, 0)
        self.assertEqual(asr["route"]["primary_adapter"], "paraformer_asr")
        code, assembly = self.run_cli(
            "final-assembly",
            "--video",
            "inputs/video_orchestrator/source.mp4",
            "--output",
            "candidate.mp4",
        )
        self.assertEqual(code, 0)
        self.assertEqual(assembly["route"]["primary_adapter"], "ffmpeg_assembly")


if __name__ == "__main__":
    unittest.main()
