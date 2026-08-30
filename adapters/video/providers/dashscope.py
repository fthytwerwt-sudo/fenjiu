"""Current DashScope/Model Studio provider adapters."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

from core.application.video_orchestrator.contracts import ErrorCode, ProviderAdapterError, ProviderDoctorReport
from core.application.video_orchestrator.config import VideoRuntimeConfig
from core.application.video_orchestrator.security import validate_remote_url
from adapters.video.providers.common import (
    DashScopeHttpClient,
    ProviderExecutionResult,
    download_binary,
    download_json,
    poll_dashscope_task,
)


class _DashScopeAdapter:
    provider_id = "dashscope"

    def __init__(self, config: VideoRuntimeConfig | None = None) -> None:
        self.config = config or VideoRuntimeConfig.from_environment()
        self.client = DashScopeHttpClient(self.config)

    def doctor(self) -> ProviderDoctorReport:
        return self.client.doctor(self.provider_id)


class Wan3VideoAdapter(_DashScopeAdapter):
    provider_id = "wan3_video"
    submit_path = "/services/aigc/video-generation/video-synthesis"

    def __init__(self, *, prime: bool = False, config: VideoRuntimeConfig | None = None) -> None:
        super().__init__(config)
        self.prime = prime
        self.model_id = "wan3.0-video-prime" if prime else "wan3.0-video"
        if prime:
            self.provider_id = "wan3_video_prime"

    def build_request(
        self,
        *,
        prompt: str,
        media: tuple[dict[str, str], ...] = (),
        duration: int = 5,
        resolution: str = "720P",
        ratio: str = "9:16",
        audio: bool = True,
        prompt_extend: bool = True,
    ) -> dict[str, Any]:
        if not prompt and not media:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "Wan3 requires prompt or media", provider=self.provider_id)
        if duration not in range(2, 31) or resolution not in {"480P", "720P", "1080P"}:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "Wan3 output options invalid", provider=self.provider_id)
        if ratio not in {"adaptive", "16:9", "4:3", "1:1", "3:4", "9:16"}:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "Wan3 ratio invalid", provider=self.provider_id)
        allowed_media = {"first_frame", "last_frame", "reference_image", "reference_video", "reference_audio", "file", "link"}
        for item in media:
            if item.get("type") not in allowed_media or not item.get("url"):
                raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "Wan3 media item invalid", provider=self.provider_id)
            validate_remote_url(item["url"], provider=self.provider_id)
        input_map: dict[str, Any] = {"prompt": prompt}
        if media:
            input_map["media"] = [dict(item) for item in media]
        return {
            "model": self.model_id,
            "input": input_map,
            "parameters": {
                "resolution": resolution,
                "ratio": ratio,
                "duration": duration,
                "audio": audio,
                "prompt_extend": prompt_extend,
            },
        }

    def submit(self, payload: dict[str, Any]) -> ProviderExecutionResult:
        data = self.client.post(self.provider_id, self.submit_path, payload, asynchronous=True)
        output = data.get("output") if isinstance(data.get("output"), dict) else {}
        task_id = output.get("task_id")
        if not task_id:
            raise ProviderAdapterError(ErrorCode.PROVIDER_FAILED, "Wan3 did not return a task ID", provider=self.provider_id)
        return ProviderExecutionResult(self.provider_id, str(output.get("task_status") or "SUBMITTED"), task_id=task_id)

    def poll(self, task_id: str, *, timeout_seconds: int = 900) -> ProviderExecutionResult:
        return poll_dashscope_task(self.client, self.provider_id, task_id, timeout_seconds=timeout_seconds)


class HappyHorseVideoAdapter(Wan3VideoAdapter):
    _MODELS = {
        "t2v": "happyhorse-1.1-t2v",
        "i2v": "happyhorse-1.1-i2v",
        "r2v": "happyhorse-1.1-r2v",
        "video_edit": "happyhorse-1.0-video-edit",
    }

    def __init__(self, *, mode: str, config: VideoRuntimeConfig | None = None) -> None:
        if mode not in self._MODELS:
            raise ProviderAdapterError(ErrorCode.UNSUPPORTED_CAPABILITY, "HappyHorse mode unsupported", provider="happyhorse")
        super().__init__(prime=False, config=config)
        self.mode = mode
        self.model_id = self._MODELS[mode]
        self.provider_id = f"happyhorse_{mode}"

    def build_request(
        self,
        *,
        prompt: str,
        media: tuple[dict[str, str], ...] = (),
        duration: int = 5,
        resolution: str = "720P",
        ratio: str = "9:16",
        audio: bool = True,
        prompt_extend: bool = True,
    ) -> dict[str, Any]:
        if duration not in range(3, 16):
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "HappyHorse duration must be 3 to 15 seconds", provider=self.provider_id)
        payload = super().build_request(
            prompt=prompt,
            media=media,
            duration=duration,
            resolution=resolution,
            ratio=ratio,
            audio=audio,
            prompt_extend=prompt_extend,
        )
        payload["model"] = self.model_id
        if self.mode == "i2v" and not any(item.get("type") in {"first_frame", "reference_image"} for item in media):
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "HappyHorse i2v requires an image", provider=self.provider_id)
        if self.mode in {"r2v", "video_edit"} and not any(item.get("type") == "reference_video" for item in media):
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "HappyHorse reference/video-edit requires video input", provider=self.provider_id)
        return payload


class MiniMaxSpeechAdapter(_DashScopeAdapter):
    provider_id = "minimax_speech_2_8_hd"
    model_id = "MiniMax/speech-2.8-hd"
    submit_path = "/services/aigc/multimodal-generation/generation"

    def __init__(self, config: VideoRuntimeConfig | None = None, *, turbo: bool = False) -> None:
        super().__init__(config)
        if turbo:
            self.provider_id = "minimax_speech_2_8_turbo"
            self.model_id = "MiniMax/speech-2.8-turbo"

    def build_request(
        self,
        text: str,
        *,
        language: str,
        voice_id: str = "male-qn-qingse",
        speed: float = 1.0,
    ) -> dict[str, Any]:
        if not text or not 0.5 <= speed <= 2.0:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "MiniMax speech input invalid", provider=self.provider_id)
        language_boost = "auto" if language.lower() in {"ne", "ne-np", "nepali"} else language
        return {
            "model": self.model_id,
            "input": {
                "text": text,
                "voice_setting": {
                    "voice_id": voice_id,
                    "speed": speed,
                    "vol": 1,
                    "pitch": 0,
                    "emotion": "calm",
                },
                "audio_setting": {
                    "sample_rate": 32000,
                    "bitrate": 128000,
                    "format": "mp3",
                    "channel": 1,
                },
                "language_boost": language_boost,
                "output_format": "hex",
                "subtitle_enable": False,
                "aigc_watermark": False,
            },
        }

    def synthesize(self, payload: dict[str, Any], output_path: Path) -> ProviderExecutionResult:
        data = self.client.post(self.provider_id, self.submit_path, payload)
        output = data.get("output") if isinstance(data.get("output"), dict) else {}
        base = output.get("base_resp") if isinstance(output.get("base_resp"), dict) else {}
        inner = output.get("data") if isinstance(output.get("data"), dict) else {}
        audio_hex = inner.get("audio") if isinstance(inner.get("audio"), str) else ""
        if base.get("status_code") not in (0, None) or not audio_hex:
            raw_code = str(base.get("status_code") or "MiniMaxAudioMissing")
            raise ProviderAdapterError(ErrorCode.PROVIDER_FAILED, "MiniMax returned no audio", provider=self.provider_id, raw_provider_code=raw_code)
        try:
            audio = bytes.fromhex(audio_hex)
        except ValueError as exc:
            raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "MiniMax audio hex invalid", provider=self.provider_id) from exc
        if not audio:
            raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "MiniMax audio empty", provider=self.provider_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio)
        return ProviderExecutionResult(self.provider_id, "GENERATED", output_path=str(output_path))


class QwenMtAdapter(_DashScopeAdapter):
    provider_id = "qwen_mt"
    model_id = "qwen-mt-flash"
    submit_path = "/services/aigc/text-generation/generation"

    def build_request(self, text: str, *, source_language: str, target_language: str) -> dict[str, Any]:
        if not text:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "translation text required", provider=self.provider_id)
        target = "Nepali" if target_language.lower() in {"ne", "nepali", "ne-np"} else target_language
        source = "Chinese" if source_language.lower() in {"zh", "chinese"} else source_language
        return {
            "model": self.model_id,
            "messages": [{"role": "user", "content": text}],
            "translation_options": {"source_lang": source, "target_lang": target},
        }

    def translate(self, request: dict[str, Any]) -> str:
        payload = {
            "model": request["model"],
            "input": {"messages": request["messages"]},
            "parameters": {"translation_options": request["translation_options"], "result_format": "message"},
        }
        data = self.client.post(self.provider_id, self.submit_path, payload)
        choices = ((data.get("output") or {}).get("choices") or [])
        if not choices:
            raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "Qwen-MT returned no translation", provider=self.provider_id)
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str) or not text.strip():
            raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "Qwen-MT translation empty", provider=self.provider_id)
        return text


class ParaformerAsrAdapter(_DashScopeAdapter):
    provider_id = "paraformer_asr"
    model_id = "paraformer-v1"
    submit_path = "/services/audio/asr/transcription"

    def __init__(
        self,
        config: VideoRuntimeConfig | None = None,
        *,
        transcript_fetcher=download_json,
    ) -> None:
        super().__init__(config)
        self.transcript_fetcher = transcript_fetcher

    def build_request(self, source_url: str) -> dict[str, Any]:
        if not source_url.startswith(("http://", "https://", "oss://")):
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "ASR source must be a reachable URL", provider=self.provider_id)
        if source_url.startswith(("http://", "https://")):
            validate_remote_url(source_url, provider=self.provider_id)
        return {"model": self.model_id, "input": {"file_urls": [source_url]}, "parameters": {}}

    def submit(self, payload: dict[str, Any]) -> ProviderExecutionResult:
        data = self.client.post(self.provider_id, self.submit_path, payload, asynchronous=True)
        output = data.get("output") if isinstance(data.get("output"), dict) else {}
        task_id = output.get("task_id")
        if not task_id:
            raise ProviderAdapterError(ErrorCode.PROVIDER_FAILED, "Paraformer returned no task ID", provider=self.provider_id)
        return ProviderExecutionResult(self.provider_id, str(output.get("task_status") or "SUBMITTED"), task_id=task_id)

    def wait(
        self,
        task_id: str,
        *,
        timeout_seconds: int = 900,
        poll_interval: int = 5,
    ) -> ProviderExecutionResult:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            data = self.client.get(self.provider_id, f"/tasks/{task_id}")
            output = data.get("output") if isinstance(data.get("output"), dict) else {}
            status = str(output.get("task_status") or "UNKNOWN")
            if status == "SUCCEEDED":
                results = output.get("results") if isinstance(output.get("results"), list) else []
                transcript_url = next(
                    (
                        item.get("transcription_url")
                        for item in results
                        if isinstance(item, dict)
                        and item.get("subtask_status") == "SUCCEEDED"
                        and isinstance(item.get("transcription_url"), str)
                    ),
                    None,
                )
                if not transcript_url:
                    raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "ASR completed without transcript URL", provider=self.provider_id)
                transcript_payload = self.transcript_fetcher(transcript_url)
                transcript = _collect_transcript_text(transcript_payload)
                if not transcript:
                    raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "ASR transcript is empty", provider=self.provider_id)
                return ProviderExecutionResult(
                    self.provider_id,
                    "GENERATED",
                    task_id=task_id,
                    output_text=transcript,
                    usage=output.get("task_metrics") if isinstance(output.get("task_metrics"), dict) else {},
                )
            if status in {"FAILED", "CANCELED", "UNKNOWN"}:
                raw_code = str(output.get("code") or status)
                raise ProviderAdapterError(ErrorCode.PROVIDER_FAILED, "ASR task failed", provider=self.provider_id, raw_provider_code=raw_code)
            time.sleep(max(1, poll_interval))
        raise ProviderAdapterError(ErrorCode.PROVIDER_TIMEOUT, "ASR task polling timed out", provider=self.provider_id, raw_provider_code="Timeout")


def _collect_transcript_text(value: Any) -> str:
    texts: list[str] = []
    if isinstance(value, dict):
        transcripts = value.get("transcripts")
        if isinstance(transcripts, list):
            for item in transcripts:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    texts.append(item["text"].strip())
        if not texts:
            for item in value.values():
                nested = _collect_transcript_text(item)
                if nested:
                    texts.append(nested)
    elif isinstance(value, list):
        for item in value:
            nested = _collect_transcript_text(item)
            if nested:
                texts.append(nested)
    return "\n".join(text for text in texts if text)


class VideoRetalkAdapter(_DashScopeAdapter):
    provider_id = "alibaba_videoretalk"
    model_id = "videoretalk"
    submit_path = "/services/aigc/image2video/video-synthesis/"

    def build_request(
        self,
        video_url: str,
        audio_url: str,
        *,
        reference_image_url: str | None = None,
        video_extension: bool = False,
    ) -> dict[str, Any]:
        if not video_url.startswith(("http://", "https://")) or not audio_url.startswith(("http://", "https://")):
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "VideoRetalk requires reachable video and audio URLs", provider=self.provider_id)
        validate_remote_url(video_url, provider=self.provider_id)
        validate_remote_url(audio_url, provider=self.provider_id)
        if reference_image_url:
            validate_remote_url(reference_image_url, provider=self.provider_id)
        input_map: dict[str, Any] = {"video_url": video_url, "audio_url": audio_url}
        if reference_image_url:
            input_map["ref_image_url"] = reference_image_url
        return {
            "model": self.model_id,
            "input": input_map,
            "parameters": {"video_extension": video_extension},
        }

    def submit(self, payload: dict[str, Any]) -> ProviderExecutionResult:
        data = self.client.post(self.provider_id, self.submit_path, payload, asynchronous=True)
        output = data.get("output") if isinstance(data.get("output"), dict) else {}
        task_id = output.get("task_id")
        if not task_id:
            raise ProviderAdapterError(ErrorCode.PROVIDER_FAILED, "VideoRetalk returned no task ID", provider=self.provider_id)
        return ProviderExecutionResult(self.provider_id, str(output.get("task_status") or "SUBMITTED"), task_id=task_id)

    def poll(self, task_id: str, *, timeout_seconds: int = 900) -> ProviderExecutionResult:
        return poll_dashscope_task(self.client, self.provider_id, task_id, timeout_seconds=timeout_seconds)
