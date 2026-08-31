"""Runtime port, configuration, fallback, and Aidge response contracts."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from adapters.video.providers.aidge import AidgeVideoGenerationAdapter
from adapters.video.runtime import VideoRuntimeAdapter
from core.application.video_orchestrator import (
    ErrorCode,
    OrchestratorRequest,
    ProviderAdapterError,
    ProviderExecutionResult,
    TaskType,
    VideoOrchestrator,
)
from core.application.video_orchestrator.config import VideoRuntimeConfig


class _FallbackRuntime:
    def __init__(self, primary_error: ErrorCode | None = None) -> None:
        self.primary_error = primary_error
        self.calls: list[str] = []

    def doctor(self) -> dict:
        return {"schema_version": "test", "providers": {}, "external_calls_made": 0}

    def execute(self, request: OrchestratorRequest, adapter_id: str) -> ProviderExecutionResult:
        self.calls.append(adapter_id)
        if adapter_id == "aidge_video_generation" and self.primary_error:
            raise ProviderAdapterError(self.primary_error, "primary failed", provider=adapter_id)
        return ProviderExecutionResult(adapter_id, "SUBMITTED", task_id="synthetic-task")


class _FakeAidgeClient:
    def video_generation(self, request):
        self.video_request = request.to_map()
        body = SimpleNamespace(
            success=True,
            code="success",
            message="Success",
            data=SimpleNamespace(task_id="synthetic-aidge-task", usage_map={"Duration": 5}),
        )
        return SimpleNamespace(body=body)

    def query_async_task_result(self, request):
        self.query_request = request.to_map()
        result = json.dumps({"Result": {"Status": "completed", "VideoUrl": "https://assets.example/result.mp4"}})
        body = SimpleNamespace(
            success=True,
            code="success",
            message="Success",
            data=SimpleNamespace(
                result=result,
                status="completed",
                task_id="synthetic-aidge-task",
                usage_map={"Duration": 5},
            ),
        )
        return SimpleNamespace(body=body)


class VideoOrchestratorRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        dns = patch(
            "core.application.video_orchestrator.security.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("1.1.1.1", 443))],
        )
        dns.start()
        self.addCleanup(dns.stop)

    def product_request(self) -> OrchestratorRequest:
        return OrchestratorRequest(
            task=TaskType.PRODUCT_AD,
            product_images=("https://assets.example/product.png",),
            product_title="Synthetic product",
            execute=True,
            cost_approved=True,
            metadata={
                "fallback_approved": True,
                "approved_providers": ("wan3_video",),
                "max_cost_cny": 10.0,
                "fallback_estimated_cost_cny": 2.0,
            },
        )

    def test_runtime_config_reads_only_allowlisted_names_and_safe_summary_has_no_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(
                "DASHSCOPE_API_KEY=secret-value\n"
                "UNRELATED_PRIVATE_VALUE=do-not-read\n"
                "AIDGE_REGION_ID=cn-beijing\n",
                encoding="utf-8",
            )
            config = VideoRuntimeConfig.from_environment(env_file=path)
        self.assertEqual(config.dashscope_api_key, "secret-value")
        self.assertEqual(config.aidge_region_id, "cn-beijing")
        rendered = json.dumps(config.safe_summary())
        self.assertNotIn("secret-value", rendered)
        self.assertNotIn("UNRELATED_PRIVATE_VALUE", rendered)

    def test_runtime_config_treats_documented_access_key_placeholders_as_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(
                "DASHSCOPE_API_KEY=LOCAL_ONLY_PLACEHOLDER_NOT_USED\n"
                "ALIBABA_CLOUD_ACCESS_KEY_ID=FILL_ME\n"
                "ALIBABA_CLOUD_ACCESS_KEY_SECRET=FILL_ME\n"
                "ALIBABA_CLOUD_SECURITY_TOKEN=LOCAL_ONLY_PLACEHOLDER_NOT_USED\n"
                "AIDGE_REGION_ID=cn-beijing\n"
                "ALIBABA_OSS_ENDPOINT=https://oss-cn-beijing.aliyuncs.com\n"
                "ALIBABA_OSS_BUCKET=synthetic-bucket\n",
                encoding="utf-8",
            )
            config = VideoRuntimeConfig.from_environment(env_file=path)
        self.assertEqual(config.alibaba_access_key_id, "")
        self.assertEqual(config.alibaba_access_key_secret, "")
        self.assertEqual(config.alibaba_security_token, "")
        self.assertEqual(config.dashscope_api_key, "")
        self.assertFalse(config.safe_summary()["alibaba_access_key_present"])
        self.assertTrue(config.safe_summary()["oss_endpoint_configured"])
        self.assertTrue(config.safe_summary()["oss_bucket_configured"])
        self.assertFalse(config.safe_summary()["oss_configured"])

    def test_orchestrator_falls_back_only_for_allowed_primary_failure(self) -> None:
        runtime = _FallbackRuntime(ErrorCode.PROVIDER_NOT_ENABLED)
        result = VideoOrchestrator(runtime=runtime).execute(self.product_request())
        self.assertTrue(result["fallback_used"])
        self.assertEqual(runtime.calls, ["aidge_video_generation", "wan3_video"])

    def test_orchestrator_does_not_fallback_for_rate_limit(self) -> None:
        runtime = _FallbackRuntime(ErrorCode.RATE_LIMITED)
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.RATE_LIMITED.value):
            VideoOrchestrator(runtime=runtime).execute(self.product_request())
        self.assertEqual(runtime.calls, ["aidge_video_generation"])

    def test_orchestrator_blocks_fallback_without_separate_cost_approval(self) -> None:
        runtime = _FallbackRuntime(ErrorCode.PROVIDER_NOT_ENABLED)
        request = OrchestratorRequest(
            task=TaskType.PRODUCT_AD,
            product_images=("https://assets.example/product.png",),
            product_title="Synthetic product",
            execute=True,
            cost_approved=True,
            metadata={"max_cost_cny": 7.0},
        )
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.COST_BLOCKED.value):
            VideoOrchestrator(runtime=runtime).execute(request)
        self.assertEqual(runtime.calls, ["aidge_video_generation"])

    def test_orchestrator_blocks_known_primary_cost_above_maximum_before_call(self) -> None:
        runtime = _FallbackRuntime()
        request = self.product_request()
        request.metadata["max_cost_cny"] = 6.0
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.COST_BLOCKED.value):
            VideoOrchestrator(runtime=runtime).execute(request)
        self.assertEqual(runtime.calls, [])

    def test_orchestrator_blocks_unknown_cost_before_call(self) -> None:
        runtime = _FallbackRuntime()
        request = OrchestratorRequest(
            task=TaskType.STORY_VIDEO,
            prompt="Synthetic story",
            execute=True,
            cost_approved=True,
            metadata={"max_cost_cny": 5.0},
        )
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.COST_BLOCKED.value):
            VideoOrchestrator(runtime=runtime).execute(request)
        self.assertEqual(runtime.calls, [])

    def test_orchestrator_uses_more_conservative_explicit_estimate(self) -> None:
        runtime = _FallbackRuntime()
        request = OrchestratorRequest(
            task=TaskType.NEPALI_VOICE,
            language="ne",
            script="नमस्कार",
            execute=True,
            cost_approved=True,
            metadata={
                "estimated_provider_cost_cny": 1.0,
                "max_cost_cny": 0.5,
            },
        )
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.COST_BLOCKED.value):
            VideoOrchestrator(runtime=runtime).execute(request)
        self.assertEqual(runtime.calls, [])

    def test_aidge_sdk_client_contract_submit_and_poll(self) -> None:
        fake = _FakeAidgeClient()
        config = VideoRuntimeConfig(
            alibaba_access_key_id="probe-only",
            alibaba_access_key_secret="probe-only",
            aidge_region_id="cn-beijing",
        )
        adapter = AidgeVideoGenerationAdapter(config, client=fake)
        request = adapter.build_request(
            images=("https://assets.example/product.png",),
            title="Synthetic product",
            duration=5,
            ratio="9:16",
            quality="720p",
        )
        submitted = adapter.submit(request)
        completed = adapter.poll(submitted.task_id or "")
        self.assertEqual(submitted.status, "SUBMITTED")
        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.output_url, "https://assets.example/result.mp4")
        rendered = json.dumps(completed.safe_summary())
        self.assertNotIn("assets.example", rendered)

    def test_videoretalk_runtime_bridges_local_video_and_voice_output(self) -> None:
        class FakeAsset:
            def __init__(self, url):
                self.signed_url = url

        class FakeBridge:
            def __init__(self):
                self.uploads = []
                self.cleanups = []

            def upload(self, path, *, asset_kind="image"):
                self.uploads.append((path, asset_kind))
                return FakeAsset(f"https://assets.example/{asset_kind}")

            def cleanup(self, asset):
                self.cleanups.append(asset.signed_url)

        class FakeVideoRetalk:
            def build_request(self, video_url, audio_url, *, reference_image_url=None):
                return {"video": video_url, "audio": audio_url}

            def submit(self, payload):
                return ProviderExecutionResult("alibaba_videoretalk", "SUBMITTED", task_id="task")

            def poll(self, task_id):
                return ProviderExecutionResult("alibaba_videoretalk", "SUCCEEDED", task_id=task_id)

        runtime = VideoRuntimeAdapter(VideoRuntimeConfig())
        bridge = FakeBridge()
        runtime.oss = bridge
        runtime.videoretalk = FakeVideoRetalk()
        request = OrchestratorRequest(
            task=TaskType.LIP_SYNC,
            source_video="outputs/video_orchestrator/source.mp4",
            source_audio="outputs/video_orchestrator/nepali.wav",
            execute=True,
            cost_approved=True,
            metadata={"media_upload_approved": True},
        )
        result = runtime.execute(request, "alibaba_videoretalk")
        self.assertEqual(result.status, "SUCCEEDED")
        self.assertEqual(
            bridge.uploads,
            [
                ("outputs/video_orchestrator/source.mp4", "video"),
                ("outputs/video_orchestrator/nepali.wav", "audio"),
            ],
        )
        self.assertEqual(len(bridge.cleanups), 2)

    def test_wan_fallback_bridges_local_product_image_with_explicit_approval(self) -> None:
        class FakeAsset:
            signed_url = "https://assets.example/product.png"

        class FakeBridge:
            def __init__(self):
                self.uploads = []
                self.cleanups = 0

            def upload(self, path, *, asset_kind="image"):
                self.uploads.append((path, asset_kind))
                return FakeAsset()

            def cleanup(self, asset):
                self.cleanups += 1

        class FakeWan:
            def __init__(self):
                self.media = None

            def build_request(self, *, prompt, media, duration, resolution, ratio):
                self.media = media
                return {"synthetic": True}

            def submit(self, payload):
                return ProviderExecutionResult("wan3_video", "SUBMITTED", task_id="task")

            def poll(self, task_id):
                return ProviderExecutionResult("wan3_video", "SUCCEEDED", task_id=task_id)

        runtime = VideoRuntimeAdapter(VideoRuntimeConfig())
        bridge = FakeBridge()
        wan = FakeWan()
        runtime.oss = bridge
        runtime.wan = wan
        result = runtime.execute(
            OrchestratorRequest(
                task=TaskType.PRODUCT_AD,
                product_images=("inputs/video_orchestrator/product.png",),
                product_title="Synthetic product",
                metadata={"media_upload_approved": True},
            ),
            "wan3_video",
        )
        self.assertEqual(result.status, "SUCCEEDED")
        self.assertEqual(bridge.uploads, [("inputs/video_orchestrator/product.png", "image")])
        self.assertEqual(wan.media, ({"type": "reference_image", "url": FakeAsset.signed_url},))
        self.assertEqual(bridge.cleanups, 1)


if __name__ == "__main__":
    unittest.main()
