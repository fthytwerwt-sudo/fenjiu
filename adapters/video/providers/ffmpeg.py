"""Local FFmpeg/FFprobe final assembly adapter."""

from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess

from core.application.video_orchestrator.contracts import ErrorCode, ProviderAdapterError, ProviderDoctorReport
from adapters.video.providers.common import ProviderExecutionResult
from core.application.video_orchestrator.security import resolve_output_path


class FfmpegAssemblyAdapter:
    provider_id = "ffmpeg_assembly"

    def __init__(self) -> None:
        self.ffmpeg = shutil.which("ffmpeg")
        self.ffprobe = shutil.which("ffprobe")

    def doctor(self) -> ProviderDoctorReport:
        available = bool(self.ffmpeg and self.ffprobe)
        return ProviderDoctorReport(
            provider=self.provider_id,
            available=available,
            credential_present=True,
            sdk_present=available,
            probe_status="CURRENTLY_AVAILABLE" if available else "BLOCKED_BINARY_MISSING",
            error_code=None if available else ErrorCode.PROVIDER_NOT_ENABLED,
        )

    def assemble(
        self,
        *,
        video_path: Path,
        output_path: Path,
        audio_path: Path | None = None,
        subtitle_path: Path | None = None,
    ) -> ProviderExecutionResult:
        if not self.doctor().available:
            raise ProviderAdapterError(ErrorCode.PROVIDER_NOT_ENABLED, "ffmpeg or ffprobe missing", provider=self.provider_id)
        if not video_path.is_file():
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "input video missing", provider=self.provider_id)
        output_path = resolve_output_path(str(output_path), provider=self.provider_id)
        command = [str(self.ffmpeg), "-y", "-v", "error", "-i", str(video_path)]
        if audio_path:
            if not audio_path.is_file():
                raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "input audio missing", provider=self.provider_id)
            command.extend(["-i", str(audio_path)])
        if subtitle_path:
            if not subtitle_path.is_file():
                raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "subtitle file missing", provider=self.provider_id)
            command.extend(["-i", str(subtitle_path)])
        command.extend(["-map", "0:v:0"])
        if audio_path:
            command.extend(["-map", "1:a:0", "-c:a", "aac", "-shortest"])
        else:
            command.extend(["-map", "0:a?", "-c:a", "copy"])
        if subtitle_path:
            subtitle_index = 2 if audio_path else 1
            command.extend(["-map", f"{subtitle_index}:0", "-c:s", "mov_text", "-metadata:s:s:0", "language=nep"])
        command.extend(["-c:v", "copy", str(output_path)])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise ProviderAdapterError(ErrorCode.PROVIDER_FAILED, "ffmpeg assembly failed", provider=self.provider_id, raw_provider_code="FFmpegFailed")
        decode = subprocess.run(
            [str(self.ffmpeg), "-v", "error", "-i", str(output_path), "-f", "null", "-"],
            capture_output=True,
            text=True,
            check=False,
        )
        if decode.returncode != 0 or not output_path.is_file() or output_path.stat().st_size <= 0:
            raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "assembled video failed decode validation", provider=self.provider_id)
        return ProviderExecutionResult(self.provider_id, "TECH_QC_PASSED", output_path=str(output_path))

    def validate_media(self, path: Path) -> dict[str, object]:
        if not self.doctor().available or not path.is_file() or path.stat().st_size <= 0:
            raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "media output missing", provider=self.provider_id)
        probe = subprocess.run(
            [
                str(self.ffprobe),
                "-v",
                "error",
                "-show_entries",
                "format=duration,size",
                "-show_entries",
                "stream=codec_type,codec_name,width,height,r_frame_rate,channels,sample_rate",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode != 0:
            raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "ffprobe validation failed", provider=self.provider_id)
        try:
            payload = json.loads(probe.stdout)
        except json.JSONDecodeError as exc:
            raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "ffprobe returned invalid JSON", provider=self.provider_id) from exc
        decode = subprocess.run(
            [str(self.ffmpeg), "-v", "error", "-i", str(path), "-f", "null", "-"],
            capture_output=True,
            text=True,
            check=False,
        )
        if decode.returncode != 0:
            raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "media decode validation failed", provider=self.provider_id)
        streams = payload.get("streams") if isinstance(payload.get("streams"), list) else []
        video = next((item for item in streams if item.get("codec_type") == "video"), {})
        audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
        return {
            "duration_seconds": float((payload.get("format") or {}).get("duration") or 0),
            "file_size_bytes": int((payload.get("format") or {}).get("size") or path.stat().st_size),
            "video_codec": video.get("codec_name"),
            "width": video.get("width"),
            "height": video.get("height"),
            "fps": video.get("r_frame_rate"),
            "audio_present": bool(audio),
            "audio_codec": audio.get("codec_name"),
            "decodable": True,
        }
