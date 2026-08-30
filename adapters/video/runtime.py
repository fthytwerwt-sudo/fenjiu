"""Composition root for real video provider adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
from adapters.video.providers.common import download_binary
from core.application.video_orchestrator.config import VideoRuntimeConfig
from core.application.video_orchestrator.contracts import (
    ErrorCode,
    OrchestratorRequest,
    ProviderAdapterError,
    ProviderExecutionResult,
)
from core.application.video_orchestrator.security import resolve_output_path


class VideoRuntimeAdapter:
    def __init__(self, config: VideoRuntimeConfig | None = None) -> None:
        self.config = config or VideoRuntimeConfig.from_environment()
        self.aidge = AidgeVideoGenerationAdapter(self.config)
        self.oss = OssAssetBridge(self.config)
        self.wan = Wan3VideoAdapter(config=self.config)
        self.wan_prime = Wan3VideoAdapter(prime=True, config=self.config)
        self.minimax = MiniMaxSpeechAdapter(self.config)
        self.minimax_turbo = MiniMaxSpeechAdapter(self.config, turbo=True)
        self.qwen_mt = QwenMtAdapter(self.config)
        self.paraformer = ParaformerAsrAdapter(self.config)
        self.videoretalk = VideoRetalkAdapter(self.config)
        self.ffmpeg = FfmpegAssemblyAdapter()

    def doctor(self) -> dict[str, Any]:
        adapters = {
            "aidge_video_generation": self.aidge,
            "alibaba_oss_asset_bridge": self.oss,
            "wan3_video": self.wan,
            "wan3_video_prime": self.wan_prime,
            "happyhorse_1_1_t2v": HappyHorseVideoAdapter(mode="t2v", config=self.config),
            "happyhorse_1_1_i2v": HappyHorseVideoAdapter(mode="i2v", config=self.config),
            "happyhorse_1_1_r2v": HappyHorseVideoAdapter(mode="r2v", config=self.config),
            "happyhorse_1_0_video_edit": HappyHorseVideoAdapter(mode="video_edit", config=self.config),
            "minimax_speech_2_8_hd": self.minimax,
            "minimax_speech_2_8_turbo": self.minimax_turbo,
            "qwen_mt": self.qwen_mt,
            "paraformer_asr": self.paraformer,
            "alibaba_videoretalk": self.videoretalk,
            "ffmpeg_assembly": self.ffmpeg,
        }
        states = {
            "aidge_video_generation": None,
            "alibaba_oss_asset_bridge": None,
            "wan3_video": "PROBE_REQUIRED",
            "wan3_video_prime": "PROBE_REQUIRED",
            "happyhorse_1_1_t2v": "PREVIOUSLY_TESTED",
            "happyhorse_1_1_i2v": "PREVIOUSLY_TESTED",
            "happyhorse_1_1_r2v": "PREVIOUSLY_TESTED",
            "happyhorse_1_0_video_edit": "PREVIOUSLY_TESTED",
            "minimax_speech_2_8_hd": "PROBE_PASSED",
            "minimax_speech_2_8_turbo": "PROBE_REQUIRED",
            "qwen_mt": "PROBE_REQUIRED",
            "paraformer_asr": "PREVIOUSLY_TESTED",
            "alibaba_videoretalk": "PREVIOUSLY_TESTED",
            "ffmpeg_assembly": "CURRENTLY_AVAILABLE",
        }
        provider_summaries = {}
        for key, adapter in sorted(adapters.items()):
            summary = adapter.doctor().safe_summary()
            summary["status"] = states[key] or summary["probe_status"]
            provider_summaries[key] = summary
        return {
            "schema_version": "video_orchestrator.doctor.v1",
            "providers": provider_summaries,
            "configuration": self.config.safe_summary(),
            "external_calls_made": 0,
        }

    def execute(self, request: OrchestratorRequest, adapter_id: str) -> ProviderExecutionResult:
        if adapter_id == "aidge_video_generation":
            doctor = self.aidge.doctor()
            if not doctor.available:
                raise ProviderAdapterError(
                    doctor.error_code or ErrorCode.PROVIDER_NOT_ENABLED,
                    doctor.probe_status,
                    provider=adapter_id,
                )
            bridged_assets = []
            try:
                images = []
                for item in request.product_images:
                    if item.startswith(("http://", "https://")):
                        images.append(item)
                    else:
                        if request.metadata.get("media_upload_approved") is not True:
                            raise ProviderAdapterError(
                                ErrorCode.PERMISSION_DENIED,
                                "explicit local media upload approval is required",
                                provider="aidge_video_generation",
                            )
                        bridged = self.oss.upload(item)
                        bridged_assets.append(bridged)
                        images.append(bridged.signed_url)
                submitted = self.aidge.submit(
                    self.aidge.build_request(
                        images=tuple(images),
                        title=request.product_title,
                        duration=request.duration or 5,
                        ratio=request.ratio or "9:16",
                        quality=request.quality or "720p",
                    )
                )
                return self._materialize(self.aidge.wait(submitted.task_id or ""), request)
            finally:
                for asset in bridged_assets:
                    self.oss.cleanup(asset)
        if adapter_id in {"wan3_video", "wan3_video_prime"}:
            adapter = self.wan_prime if adapter_id.endswith("prime") else self.wan
            media, bridged_assets = self._bridge_reference_media(request, provider=adapter_id)
            try:
                submitted = adapter.submit(
                    adapter.build_request(
                        prompt=request.prompt or request.product_title,
                        media=media,
                        duration=request.duration or 5,
                        resolution=(request.quality or "720p").upper(),
                        ratio=request.ratio or "9:16",
                    )
                )
                return self._materialize(adapter.poll(submitted.task_id or ""), request)
            finally:
                for asset in bridged_assets:
                    self.oss.cleanup(asset)
        if adapter_id.startswith("happyhorse_"):
            mode = adapter_id.removeprefix("happyhorse_1_1_")
            if adapter_id == "happyhorse_1_0_video_edit":
                mode = "video_edit"
            adapter = HappyHorseVideoAdapter(mode=mode, config=self.config)
            media, bridged_assets = self._bridge_reference_media(request, provider=adapter_id)
            try:
                submitted = adapter.submit(
                    adapter.build_request(
                        prompt=request.prompt,
                        media=media,
                        duration=request.duration or 5,
                        resolution=(request.quality or "720p").upper(),
                        ratio=request.ratio or "9:16",
                    )
                )
                return self._materialize(adapter.poll(submitted.task_id or ""), request)
            finally:
                for asset in bridged_assets:
                    self.oss.cleanup(asset)
        if adapter_id == "minimax_speech_2_8_hd":
            output_value = request.metadata.get("output_path")
            if not isinstance(output_value, str) or not output_value:
                raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "voice output path required", provider=adapter_id)
            return self.minimax.synthesize(
                self.minimax.build_request(request.script, language=request.language),
                resolve_output_path(output_value, provider=adapter_id),
            )
        if adapter_id == "minimax_speech_2_8_turbo":
            output_value = request.metadata.get("output_path")
            if not isinstance(output_value, str) or not output_value:
                raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "voice output path required", provider=adapter_id)
            return self.minimax_turbo.synthesize(
                self.minimax_turbo.build_request(request.script, language=request.language),
                resolve_output_path(output_value, provider=adapter_id),
            )
        if adapter_id == "qwen_mt":
            translated = self.qwen_mt.translate(
                self.qwen_mt.build_request(
                    request.script,
                    source_language=str(request.metadata.get("source_language") or "zh"),
                    target_language=request.language or "ne",
                )
            )
            return ProviderExecutionResult(adapter_id, "GENERATED", output_text=translated)
        if adapter_id == "paraformer_asr":
            source = request.source_audio or request.source_video or ""
            bridged_asset = None
            try:
                if not source.startswith(("https://", "oss://")):
                    if request.metadata.get("media_upload_approved") is not True:
                        raise ProviderAdapterError(
                            ErrorCode.PERMISSION_DENIED,
                            "explicit local media upload approval is required",
                            provider=adapter_id,
                        )
                    kind = "audio" if Path(source).suffix.lower() in {
                        ".wav",
                        ".mp3",
                        ".aac",
                        ".m4a",
                        ".flac",
                        ".ogg",
                        ".opus",
                    } else "video"
                    bridged_asset = self.oss.upload(source, asset_kind=kind)
                    source = bridged_asset.signed_url
                submitted = self.paraformer.submit(self.paraformer.build_request(source))
                return self.paraformer.wait(submitted.task_id or "")
            finally:
                if bridged_asset is not None:
                    self.oss.cleanup(bridged_asset)
        if adapter_id == "alibaba_videoretalk":
            bridged_assets = []
            try:
                video_value = request.source_video or ""
                audio_value = request.source_audio or ""
                reference_value = request.reference_image
                local_transfer_required = any(
                    value and not value.startswith(("http://", "https://"))
                    for value in (video_value, audio_value, reference_value)
                )
                if local_transfer_required and request.metadata.get("media_upload_approved") is not True:
                    raise ProviderAdapterError(
                        ErrorCode.PERMISSION_DENIED,
                        "explicit local media upload approval is required",
                        provider=adapter_id,
                    )
                if not video_value.startswith(("http://", "https://")):
                    asset = self.oss.upload(video_value, asset_kind="video")
                    bridged_assets.append(asset)
                    video_value = asset.signed_url
                if not audio_value.startswith(("http://", "https://")):
                    asset = self.oss.upload(audio_value, asset_kind="audio")
                    bridged_assets.append(asset)
                    audio_value = asset.signed_url
                if reference_value and not reference_value.startswith(("http://", "https://")):
                    asset = self.oss.upload(reference_value, asset_kind="image")
                    bridged_assets.append(asset)
                    reference_value = asset.signed_url
                submitted = self.videoretalk.submit(
                    self.videoretalk.build_request(
                        video_value,
                        audio_value,
                        reference_image_url=reference_value,
                    )
                )
                return self._materialize(self.videoretalk.poll(submitted.task_id or ""), request)
            finally:
                for asset in bridged_assets:
                    self.oss.cleanup(asset)
        if adapter_id == "ffmpeg_assembly":
            output_value = request.metadata.get("output_path")
            if not isinstance(output_value, str) or not output_value or not request.source_video:
                raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "assembly input and output paths required", provider=adapter_id)
            return self.ffmpeg.assemble(
                video_path=Path(request.source_video),
                audio_path=Path(request.source_audio) if request.source_audio else None,
                subtitle_path=Path(request.metadata["subtitle_path"]) if request.metadata.get("subtitle_path") else None,
                output_path=Path(output_value),
            )
        raise ProviderAdapterError(ErrorCode.UNSUPPORTED_CAPABILITY, "execution adapter not wired", provider=adapter_id)

    def _bridge_reference_media(
        self,
        request: OrchestratorRequest,
        *,
        provider: str,
    ) -> tuple[tuple[dict[str, str], ...], list[Any]]:
        inputs = (
            [("reference_image", value, "image") for value in request.product_images]
            + [("reference_image", value, "image") for value in request.reference_images]
            + [("reference_video", value, "video") for value in request.reference_videos]
        )
        media: list[dict[str, str]] = []
        bridged_assets: list[Any] = []
        try:
            for media_type, value, asset_kind in inputs:
                if value.startswith(("http://", "https://")):
                    url = value
                else:
                    if request.metadata.get("media_upload_approved") is not True:
                        raise ProviderAdapterError(
                            ErrorCode.PERMISSION_DENIED,
                            "explicit local media upload approval is required",
                            provider=provider,
                        )
                    asset = self.oss.upload(value, asset_kind=asset_kind)
                    bridged_assets.append(asset)
                    url = asset.signed_url
                media.append({"type": media_type, "url": url})
        except Exception:
            for asset in bridged_assets:
                self.oss.cleanup(asset)
            raise
        return tuple(media), bridged_assets

    def _materialize(
        self,
        result: ProviderExecutionResult,
        request: OrchestratorRequest,
    ) -> ProviderExecutionResult:
        output_value = request.metadata.get("output_path")
        if not output_value or not result.output_url:
            return result
        output = resolve_output_path(str(output_value), provider=result.provider)
        download_binary(result.output_url, output)
        media_qc = self.ffmpeg.validate_media(output)
        usage = dict(result.usage or {})
        usage["technical_qc"] = media_qc
        return ProviderExecutionResult(
            provider=result.provider,
            status="TECH_QC_PASSED",
            task_id=result.task_id,
            output_url=result.output_url,
            output_path=str(output),
            raw_provider_code=result.raw_provider_code,
            usage=usage,
        )
