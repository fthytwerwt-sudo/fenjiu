"""Video Orchestrator registry, routing, and error contracts."""

from __future__ import annotations

import json
import unittest

from core.application.video_orchestrator import (
    CapabilityRegistry,
    ErrorCode,
    OrchestratorRequest,
    ProviderFailure,
    TaskType,
    VideoRouter,
    map_provider_error,
)
from core.application.video_orchestrator.contracts import redact_sensitive_text


class VideoOrchestratorCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = CapabilityRegistry.default()
        self.router = VideoRouter(self.registry)

    def test_default_registry_has_required_business_capabilities(self) -> None:
        required = {
            "product_video",
            "story_video",
            "fast_story_video",
            "short_reference_video",
            "nepali_tts",
            "translate_nepali",
            "source_asr",
            "lip_sync",
            "final_assembly",
        }
        self.assertTrue(required.issubset(set(self.registry.capability_ids())))
        rendered = json.dumps(self.registry.safe_summary(), ensure_ascii=False)
        self.assertNotIn("api_key", rendered.lower())
        self.assertNotIn("/" + "Volumes/", rendered)

    def test_product_ad_routes_to_aidge_with_wan_fallback(self) -> None:
        request = OrchestratorRequest(
            task=TaskType.PRODUCT_AD,
            product_images=("https://assets.example/item.png",),
            product_title="Synthetic product",
        )
        decision = self.router.route(request)
        self.assertEqual(decision.primary_adapter, "aidge_video_generation")
        self.assertEqual(decision.fallback_adapter, "wan3_video")

    def test_story_video_speed_priority_routes_to_prime(self) -> None:
        request = OrchestratorRequest(
            task=TaskType.STORY_VIDEO,
            prompt="A synthetic cinematic product story",
            speed_priority=True,
        )
        self.assertEqual(self.router.route(request).primary_adapter, "wan3_video_prime")

    def test_short_reference_routes_by_input_shape(self) -> None:
        image_request = OrchestratorRequest(
            task=TaskType.SHORT_PRODUCT_SCENE,
            reference_images=("asset:synthetic-image",),
            prompt="Synthetic scene",
        )
        video_request = OrchestratorRequest(
            task=TaskType.SHORT_PRODUCT_SCENE,
            reference_videos=("asset:synthetic-video",),
            prompt="Synthetic scene",
        )
        self.assertEqual(self.router.route(image_request).primary_adapter, "happyhorse_1_1_i2v")
        self.assertEqual(self.router.route(video_request).primary_adapter, "happyhorse_1_1_r2v")

    def test_nepali_voice_routes_to_minimax_hd(self) -> None:
        request = OrchestratorRequest(
            task=TaskType.NEPALI_VOICE,
            language="ne",
            script="नमस्कार",
        )
        self.assertEqual(self.router.route(request).primary_adapter, "minimax_speech_2_8_hd")

    def test_translate_nepali_rejects_non_nepali_target(self) -> None:
        request = OrchestratorRequest(
            task=TaskType.TRANSLATE_NEPALI,
            language="en",
            script="你好",
        )
        with self.assertRaisesRegex(ValueError, "translate_nepali_requires_ne_language"):
            self.router.route(request)

    def test_existing_video_and_audio_routes_to_videoretalk(self) -> None:
        request = OrchestratorRequest(
            task=TaskType.LIP_SYNC,
            source_video="asset:synthetic-video",
            source_audio="asset:synthetic-audio",
        )
        self.assertEqual(self.router.route(request).primary_adapter, "alibaba_videoretalk")

    def test_request_safe_summary_hashes_local_paths_and_urls(self) -> None:
        request = OrchestratorRequest(
            task=TaskType.LIP_SYNC,
            source_video="/tmp/private/source.mp4",
            source_audio="https://signed.example/audio.wav?secret=value",
        )
        rendered = json.dumps(request.safe_summary(), sort_keys=True)
        self.assertNotIn("/tmp/private", rendered)
        self.assertNotIn("signed.example", rendered)
        self.assertNotIn("secret=value", rendered)

    def test_provider_errors_map_to_unified_contract(self) -> None:
        cases = {
            "InvalidAccessKeyId.NotFound": ErrorCode.AUTH_REQUIRED,
            "Forbidden.RAM": ErrorCode.PERMISSION_DENIED,
            "ProductNotOpen": ErrorCode.PROVIDER_NOT_ENABLED,
            "InvalidParameter": ErrorCode.INVALID_INPUT,
            "Throttling": ErrorCode.RATE_LIMITED,
            "Timeout": ErrorCode.PROVIDER_TIMEOUT,
            "InvalidURL": ErrorCode.ASSET_ACCESS_FAILED,
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                failure = map_provider_error("provider", raw, "safe message")
                self.assertEqual(failure.code, expected)
                self.assertEqual(failure.raw_provider_code, raw)

    def test_fallback_only_for_allowed_failure_classes(self) -> None:
        allowed = ProviderFailure("aidge", ErrorCode.PROVIDER_NOT_ENABLED, "blocked")
        denied = ProviderFailure("aidge", ErrorCode.RATE_LIMITED, "retry later")
        self.assertTrue(self.router.may_fallback(allowed))
        self.assertFalse(self.router.may_fallback(denied))

    def test_safe_error_redaction_removes_urls_credentials_and_local_paths(self) -> None:
        local_path = "/" + "Volumes/private/file.png"
        rendered = redact_sensitive_text(
            f"failed https://signed.example/a?token=1 Bearer secret {local_path}"
        )
        self.assertNotIn("signed.example", rendered)
        self.assertNotIn("Bearer secret", rendered)
        self.assertNotIn("/" + "Volumes/private", rendered)


if __name__ == "__main__":
    unittest.main()
