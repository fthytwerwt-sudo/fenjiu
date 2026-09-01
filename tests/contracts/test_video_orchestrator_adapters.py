"""Provider request builders and local adapter contracts."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from adapters.video.providers import (
    AidgeVideoGenerationAdapter,
    FfmpegAssemblyAdapter,
    HappyHorseVideoAdapter,
    MiniMaxSpeechAdapter,
    OssAssetBridge,
    ParaformerAsrAdapter,
    QwenMtAdapter,
    VideoRetalkAdapter,
    Wan3VideoAdapter,
)
from core.application.video_orchestrator import ErrorCode, ProviderAdapterError
from core.application.video_orchestrator.config import VideoRuntimeConfig
from adapters.video.providers import common as provider_common


class VideoOrchestratorAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        dns = patch(
            "core.application.video_orchestrator.security.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("1.1.1.1", 443))],
        )
        dns.start()
        self.addCleanup(dns.stop)

    def test_aidge_request_matches_official_video_generation_shape(self) -> None:
        adapter = AidgeVideoGenerationAdapter()
        request = adapter.build_request(
            images=("https://assets.example/product.png",),
            title="Synthetic product",
            duration=5,
            ratio="9:16",
            quality="720p",
        )
        self.assertEqual(request["Input"]["Images"], ["https://assets.example/product.png"])
        self.assertEqual(request["Input"]["Title"], "Synthetic product")
        self.assertEqual(request["Output"], {"Duration": 5, "Ratio": "9:16", "Quality": "720p"})

    def test_aidge_rejects_invalid_image_count_and_output_options(self) -> None:
        adapter = AidgeVideoGenerationAdapter()
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.INVALID_INPUT.value):
            adapter.build_request(images=(), title="Synthetic", duration=5, ratio="9:16", quality="720p")
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.INVALID_INPUT.value):
            adapter.build_request(
                images=tuple(f"https://assets.example/{i}.png" for i in range(7)),
                title="Synthetic",
                duration=5,
                ratio="16:9",
                quality="4k",
            )

    def test_aidge_doctor_reports_missing_credentials_without_reading_values(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            report = AidgeVideoGenerationAdapter(VideoRuntimeConfig()).doctor()
        self.assertFalse(report.credential_present)
        self.assertEqual(report.error_code, ErrorCode.AUTH_REQUIRED)
        self.assertNotIn("access_key", str(report.safe_summary()).lower())

    def test_oss_bridge_requires_private_config_and_never_returns_url_in_summary(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            bridge = OssAssetBridge(VideoRuntimeConfig())
        self.assertFalse(bridge.doctor().credential_present)
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.AUTH_REQUIRED.value):
            bridge.upload("asset:synthetic")

    def test_oss_doctor_distinguishes_waiting_credentials_from_missing_config(self) -> None:
        bridge = OssAssetBridge(
            VideoRuntimeConfig(
                oss_endpoint="https://oss-cn-beijing.aliyuncs.com",
                oss_bucket="synthetic-bucket",
            )
        )
        report = bridge.doctor()
        self.assertFalse(report.available)
        self.assertEqual(report.probe_status, "BLOCKED_OSS_CREDENTIALS_ABSENT")
        self.assertEqual(report.error_code, ErrorCode.AUTH_REQUIRED)

    def test_wan_and_happyhorse_model_selection(self) -> None:
        self.assertEqual(Wan3VideoAdapter(prime=False).model_id, "wan3.0-video")
        self.assertEqual(Wan3VideoAdapter(prime=True).model_id, "wan3.0-video-prime")
        self.assertEqual(HappyHorseVideoAdapter(mode="t2v").model_id, "happyhorse-1.1-t2v")
        self.assertEqual(HappyHorseVideoAdapter(mode="i2v").model_id, "happyhorse-1.1-i2v")
        self.assertEqual(HappyHorseVideoAdapter(mode="r2v").model_id, "happyhorse-1.1-r2v")
        self.assertEqual(HappyHorseVideoAdapter(mode="video_edit").model_id, "happyhorse-1.0-video-edit")

    def test_wan_request_explicitly_disables_provider_watermark_and_audio(self) -> None:
        payload = Wan3VideoAdapter().build_request(
            prompt="Synthetic reference recreation",
            media=({"type": "reference_video", "url": "https://assets.example/reference.mp4"},),
            duration=4,
            resolution="720P",
            ratio="9:16",
            audio=False,
            prompt_extend=False,
        )
        self.assertIs(payload["parameters"]["watermark"], False)
        self.assertIs(payload["parameters"]["audio"], False)
        self.assertIs(payload["parameters"]["prompt_extend"], False)

    def test_happyhorse_r2v_accepts_reference_images_and_rejects_reference_video(self) -> None:
        adapter = HappyHorseVideoAdapter(mode="r2v")
        payload = adapter.build_request(
            prompt="Synthetic image reference",
            media=({"type": "reference_image", "url": "https://assets.example/reference.jpg"},),
            duration=4,
            resolution="720P",
            ratio="9:16",
        )
        self.assertEqual(payload["model"], "happyhorse-1.1-r2v")
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.INVALID_INPUT.value):
            adapter.build_request(
                prompt="Synthetic video reference",
                media=({"type": "reference_video", "url": "https://assets.example/reference.mp4"},),
                duration=4,
                resolution="720P",
                ratio="9:16",
            )

    def test_minimax_nepali_request_uses_auto_language_boost(self) -> None:
        payload = MiniMaxSpeechAdapter().build_request("नमस्कार", language="ne")
        self.assertEqual(payload["model"], "MiniMax/speech-2.8-hd")
        self.assertEqual(payload["input"]["language_boost"], "auto")
        turbo = MiniMaxSpeechAdapter(turbo=True).build_request("नमस्कार", language="ne")
        self.assertEqual(turbo["model"], "MiniMax/speech-2.8-turbo")

    def test_qwen_mt_paraformer_and_videoretalk_request_contracts(self) -> None:
        translation = QwenMtAdapter().build_request("你好", source_language="zh", target_language="ne")
        self.assertEqual(translation["translation_options"]["target_lang"], "Nepali")
        asr = ParaformerAsrAdapter().build_request("https://assets.example/source.wav")
        self.assertEqual(asr["model"], "paraformer-v1")
        lip_sync = VideoRetalkAdapter().build_request(
            "https://assets.example/source.mp4",
            "https://assets.example/nepali.wav",
            reference_image_url="https://assets.example/face.jpg",
        )
        self.assertEqual(lip_sync["model"], "videoretalk")
        self.assertIn("ref_image_url", lip_sync["input"])

    def test_paraformer_wait_returns_normalized_transcript(self) -> None:
        class FakeClient:
            def get(self, provider, path):
                return {
                    "output": {
                        "task_status": "SUCCEEDED",
                        "results": [
                            {
                                "subtask_status": "SUCCEEDED",
                                "transcription_url": "https://result.oss-cn-beijing.aliyuncs.com/transcript.json",
                            }
                        ],
                        "task_metrics": {"SUCCEEDED": 1},
                    }
                }

        adapter = ParaformerAsrAdapter(
            transcript_fetcher=lambda url: {
                "transcripts": [
                    {
                        "text": "你好，世界。",
                        "sentences": [
                            {"begin_time": 120, "end_time": 980, "text": "你好，"},
                            {"begin_time": 1000, "end_time": 1800, "text": "世界。"},
                        ],
                    }
                ]
            }
        )
        adapter.client = FakeClient()
        result = adapter.wait("synthetic-task", timeout_seconds=1, poll_interval=1)
        self.assertEqual(result.status, "GENERATED")
        self.assertEqual(result.output_text, "你好，世界。")
        self.assertEqual(
            result.usage["transcript_segments"],
            [
                {"start_ms": 120, "end_ms": 980, "text": "你好，"},
                {"start_ms": 1000, "end_ms": 1800, "text": "世界。"},
            ],
        )

    def test_output_download_upgrades_trusted_alibaba_http_url_to_https(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return b"synthetic-video"

        captured = {}

        class FakeOpener:
            def open(self, request, timeout):
                captured["url"] = request.full_url
                return FakeResponse()

        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                destination = Path("video.mp4")
                with patch.object(
                    provider_common.urllib.request,
                    "build_opener",
                    return_value=FakeOpener(),
                ):
                    try:
                        provider_common.download_binary(
                            "http://result.oss-cn-beijing.aliyuncs.com/video.mp4",
                            destination,
                        )
                    except ProviderAdapterError as exc:
                        self.fail(f"trusted provider output should normalize safely: {exc.code.value}")
                self.assertEqual(captured["url"], "https://result.oss-cn-beijing.aliyuncs.com/video.mp4")
                self.assertEqual(destination.read_bytes(), b"synthetic-video")
            finally:
                os.chdir(previous)

    def test_output_download_does_not_upgrade_untrusted_or_userinfo_url(self) -> None:
        for value in (
            "http://untrusted.example/video.mp4",
            "https://user:password@result.oss-cn-beijing.aliyuncs.com/video.mp4",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ProviderAdapterError):
                    provider_common.download_binary(value, Path("unused.mp4"))

    def test_output_download_revalidates_redirect_target(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return b"synthetic-video"

        class FakeOpener:
            def open(self, request, timeout):
                return FakeResponse()

        captured = {}

        def fake_build_opener(handler):
            captured["handler"] = handler
            return FakeOpener()

        with patch.object(provider_common.urllib.request, "build_opener", side_effect=fake_build_opener):
            with patch.object(provider_common.urllib.request, "urlopen", return_value=FakeResponse()):
                provider_common.download_binary(
                    "https://result.oss-cn-beijing.aliyuncs.com/video.mp4",
                    Path("redirect-test.mp4"),
                )
        self.assertIn("handler", captured)
        with self.assertRaises(ProviderAdapterError):
            captured["handler"].redirect_request(
                SimpleNamespace(full_url="https://result.oss-cn-beijing.aliyuncs.com/video.mp4"),
                None,
                302,
                "Found",
                {},
                "https://untrusted.example/video.mp4",
            )

    def test_ffmpeg_doctor_reports_installed_binary(self) -> None:
        report = FfmpegAssemblyAdapter().doctor()
        self.assertTrue(report.available)


if __name__ == "__main__":
    unittest.main()
