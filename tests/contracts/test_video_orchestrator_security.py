"""Negative security contracts for media, endpoints, URLs, and output paths."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from adapters.video.providers.common import DashScopeHttpClient
from core.application.video_orchestrator import ErrorCode, ProviderAdapterError
from core.application.video_orchestrator.config import VideoRuntimeConfig
from core.application.video_orchestrator.security import (
    endpoint_allowed,
    resolve_output_path,
    validate_local_media,
    validate_local_product_image,
    validate_remote_url,
)


class VideoOrchestratorSecurityTests(unittest.TestCase):
    @staticmethod
    def public_dns(*args, **kwargs):
        return [(2, 1, 6, "", ("1.1.1.1", 443))]

    def test_provider_urls_require_https_and_reject_private_hosts(self) -> None:
        for value in (
            "http://assets.example/item.png",
            "https://localhost/item.png",
            "https://127.0.0.1/item.png",
            "https://169.254.169.254/latest/meta-data",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ProviderAdapterError):
                    validate_remote_url(value, provider="test")
        self.assertEqual(
            validate_remote_url(
                "https://assets.example/item.png",
                provider="test",
                resolver=self.public_dns,
            ),
            "https://assets.example/item.png",
        )

    def test_provider_urls_reject_dns_answers_that_resolve_private(self) -> None:
        private_dns = lambda *args, **kwargs: [(2, 1, 6, "", ("10.2.3.4", 443))]
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.PERMISSION_DENIED.value):
            validate_remote_url(
                "https://public-looking.example/item.png",
                provider="test",
                resolver=private_dns,
            )

    def test_only_trusted_alibaba_hosts_accept_codex_benchmark_proxy_dns(self) -> None:
        proxy_dns = lambda *args, **kwargs: [(2, 1, 6, "", ("198.18.8.234", 443))]
        trusted = "https://help-static-aliyun-doc.aliyuncs.com/sample.png"
        self.assertEqual(
            validate_remote_url(trusted, provider="test", resolver=proxy_dns),
            trusted,
        )
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.PERMISSION_DENIED.value):
            validate_remote_url(
                "https://untrusted.example/sample.png",
                provider="test",
                resolver=proxy_dns,
            )
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.PERMISSION_DENIED.value):
            validate_remote_url(
                "https://unknown-service.aliyuncs.com/sample.png",
                provider="test",
                resolver=proxy_dns,
            )

    def test_provider_urls_reject_public_literal_ip_hosts(self) -> None:
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.PERMISSION_DENIED.value):
            validate_remote_url("https://1.1.1.1/sample.png", provider="test")

    def test_provider_output_download_hosts_are_allowlisted(self) -> None:
        with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.ASSET_ACCESS_FAILED.value):
            validate_remote_url(
                "https://evil.example/result.mp4",
                provider="download",
                trusted_output=True,
            )
        self.assertEqual(
            validate_remote_url(
                "https://result.oss-cn-beijing.aliyuncs.com/result.mp4",
                provider="download",
                trusted_output=True,
                resolver=self.public_dns,
            ),
            "https://result.oss-cn-beijing.aliyuncs.com/result.mp4",
        )

    def test_endpoint_overrides_accept_only_alibaba_https_hosts(self) -> None:
        self.assertTrue(endpoint_allowed("https://dashscope.aliyuncs.com/api/v1", service="dashscope"))
        self.assertTrue(endpoint_allowed("https://workspace.cn-beijing.maas.aliyuncs.com/api/v1", service="dashscope"))
        self.assertFalse(endpoint_allowed("https://evil.example/api/v1", service="dashscope"))
        self.assertFalse(endpoint_allowed("http://aidge.cn-beijing.aliyuncs.com", service="aidge"))

        client = DashScopeHttpClient(
            VideoRuntimeConfig(
                dashscope_api_key="probe-only",
                dashscope_base_url="https://evil.example/api/v1",
            )
        )
        self.assertEqual(client.doctor("dashscope").error_code, ErrorCode.PERMISSION_DENIED)

    def test_local_product_images_are_confined_and_signature_checked(self) -> None:
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                allowed = Path("inputs/video_orchestrator/item.png")
                allowed.parent.mkdir(parents=True)
                allowed.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
                self.assertEqual(validate_local_product_image(str(allowed), provider="test"), allowed.resolve())

                outside = Path("outside.png")
                outside.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
                with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.PERMISSION_DENIED.value):
                    validate_local_product_image(str(outside), provider="test")

                fake = Path("inputs/video_orchestrator/not-image.png")
                fake.write_text("not an image", encoding="utf-8")
                with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.INVALID_INPUT.value):
                    validate_local_product_image(str(fake), provider="test")
            finally:
                os.chdir(previous)

    def test_local_bridge_accepts_claimed_audio_video_and_bmp_formats(self) -> None:
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                root = Path("inputs/video_orchestrator")
                root.mkdir(parents=True)
                samples = {
                    "audio.m4a": ("audio", b"\x00\x00\x00\x18ftypM4A "),
                    "audio.flac": ("audio", b"fLaC" + b"0" * 12),
                    "audio.ogg": ("audio", b"OggS" + b"0" * 12),
                    "audio.opus": ("audio", b"OggS" + b"0" * 12),
                    "video.webm": ("video", b"\x1aE\xdf\xa3" + b"0" * 12),
                    "face.bmp": ("image", b"BM" + b"0" * 14),
                }
                for name, (kind, payload) in samples.items():
                    with self.subTest(name=name):
                        path = root / name
                        path.write_bytes(payload)
                        self.assertEqual(
                            validate_local_media(str(path), provider="test", asset_kind=kind),
                            path.resolve(),
                        )
            finally:
                os.chdir(previous)

    def test_output_paths_are_confined_to_orchestrator_outputs(self) -> None:
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                allowed = resolve_output_path("candidate.mp4", provider="test")
                self.assertEqual(allowed, (Path(tmp) / "outputs/video_orchestrator/candidate.mp4").resolve())
                with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.PERMISSION_DENIED.value):
                    resolve_output_path("../outside.mp4", provider="test")
                with self.assertRaisesRegex(ProviderAdapterError, ErrorCode.INVALID_INPUT.value):
                    resolve_output_path("candidate.sh", provider="test")
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
