"""Provider-neutral contracts for the Video Orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import re
from typing import Any


class TaskType(str, Enum):
    PRODUCT_AD = "product_ad"
    STORY_VIDEO = "story_video"
    FAST_STORY_VIDEO = "fast_story_video"
    SHORT_PRODUCT_SCENE = "short_product_scene"
    NEPALI_VOICE = "nepali_voice"
    TRANSLATE_NEPALI = "translate_nepali"
    SOURCE_ASR = "source_asr"
    LIP_SYNC = "lip_sync"
    FINAL_ASSEMBLY = "final_assembly"


class CapabilityStatus(str, Enum):
    CODE_EXISTS = "CODE_EXISTS"
    CONNECTED = "CONNECTED"
    CONNECTED_NOT_AUTH_VERIFIED = "CONNECTED_NOT_AUTH_VERIFIED"
    AUTH_VERIFIED = "AUTH_VERIFIED"
    PROBE_PASSED = "PROBE_PASSED"
    PREVIOUSLY_TESTED = "PREVIOUSLY_TESTED"
    CURRENTLY_AVAILABLE = "CURRENTLY_AVAILABLE"
    PROBE_REQUIRED = "PROBE_REQUIRED"
    BLOCKED = "BLOCKED"


class ErrorCode(str, Enum):
    AUTH_REQUIRED = "AUTH_REQUIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    PROVIDER_NOT_ENABLED = "PROVIDER_NOT_ENABLED"
    INVALID_INPUT = "INVALID_INPUT"
    UNSUPPORTED_CAPABILITY = "UNSUPPORTED_CAPABILITY"
    RATE_LIMITED = "RATE_LIMITED"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_FAILED = "PROVIDER_FAILED"
    ASSET_ACCESS_FAILED = "ASSET_ACCESS_FAILED"
    OUTPUT_INVALID = "OUTPUT_INVALID"
    COST_BLOCKED = "COST_BLOCKED"


class OrchestratorContractError(ValueError):
    """Raised when a provider-neutral request violates the contract."""


class ProviderAdapterError(RuntimeError):
    """A normalized adapter failure safe for application code."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        provider: str = "unknown",
        raw_provider_code: str | None = None,
    ) -> None:
        super().__init__(f"{code.value}: {message}")
        self.code = code
        self.provider = provider
        self.raw_provider_code = raw_provider_code

    def safe_summary(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "provider": self.provider,
            "raw_provider_code": self.raw_provider_code,
            "message": redact_sensitive_text(str(self).split(": ", 1)[-1])[:300],
        }


def redact_sensitive_text(value: str) -> str:
    text = value
    text = re.sub(r"https?://[^\s]+", "[REDACTED_URL]", text)
    text = re.sub(r"(?i)bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED]", text)
    text = re.sub(r"(?i)\b(?:sk[-_]|akia|ltaI)[A-Za-z0-9._-]+", "[REDACTED_CREDENTIAL]", text)
    text = re.sub(r"(?i)/(?:Users|Volumes)/[^\s]+", "[REDACTED_PATH]", text)
    return text


@dataclass(frozen=True)
class ProviderFailure:
    provider: str
    code: ErrorCode
    message: str
    raw_provider_code: str | None = None


def safe_ref(value: str | None) -> str | None:
    if value is None:
        return None
    digest = sha256(value.encode("utf-8")).hexdigest()
    return f"ref:{digest[:24]}"


@dataclass(frozen=True)
class ProviderExecutionResult:
    provider: str
    status: str
    task_id: str | None = None
    output_url: str | None = None
    output_path: str | None = None
    output_text: str | None = None
    raw_provider_code: str | None = None
    usage: dict[str, Any] | None = None

    def safe_summary(self, *, include_output_text: bool = False) -> dict[str, Any]:
        summary = {
            "provider": self.provider,
            "status": self.status,
            "task_ref": safe_ref(self.task_id),
            "output_ref": safe_ref(self.output_url or self.output_path or self.output_text),
            "raw_provider_code": self.raw_provider_code,
            "usage": self.usage or {},
            "human_review_required": self.status in {"SUCCEEDED", "GENERATED", "TECH_QC_PASSED"},
        }
        if include_output_text and self.output_text is not None:
            summary["output_text"] = self.output_text
        return summary


@dataclass(frozen=True)
class OrchestratorRequest:
    task: TaskType
    language: str = ""
    product_images: tuple[str, ...] = ()
    product_title: str = ""
    prompt: str = ""
    script: str = ""
    source_video: str | None = None
    source_audio: str | None = None
    reference_image: str | None = None
    reference_images: tuple[str, ...] = ()
    reference_videos: tuple[str, ...] = ()
    duration: int | None = None
    ratio: str | None = None
    quality: str | None = None
    speed_priority: bool = False
    execute: bool = False
    cost_approved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "task": self.task.value,
            "language": self.language,
            "product_image_refs": [safe_ref(item) for item in self.product_images],
            "product_title_hash": safe_ref(self.product_title) if self.product_title else None,
            "prompt_hash": safe_ref(self.prompt) if self.prompt else None,
            "script_hash": safe_ref(self.script) if self.script else None,
            "source_video_ref": safe_ref(self.source_video),
            "source_audio_ref": safe_ref(self.source_audio),
            "reference_image_ref": safe_ref(self.reference_image),
            "reference_image_refs": [safe_ref(item) for item in self.reference_images],
            "reference_video_refs": [safe_ref(item) for item in self.reference_videos],
            "duration": self.duration,
            "ratio": self.ratio,
            "quality": self.quality,
            "speed_priority": self.speed_priority,
            "execute": self.execute,
            "cost_approved": self.cost_approved,
            "media_upload_approved": self.metadata.get("media_upload_approved") is True,
            "fallback_approved": self.metadata.get("fallback_approved") is True,
            "approved_providers": sorted(
                str(item) for item in self.metadata.get("approved_providers", [])
            ),
            "max_cost_cny": self.metadata.get("max_cost_cny"),
            "estimated_provider_cost_cny": self.metadata.get("estimated_provider_cost_cny"),
            "fallback_estimated_cost_cny": self.metadata.get("fallback_estimated_cost_cny"),
        }


@dataclass(frozen=True)
class RouteDecision:
    capability_id: str
    primary_adapter: str
    fallback_adapter: str | None
    reason: str
    human_review_required: bool = True

    def safe_summary(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "primary_adapter": self.primary_adapter,
            "fallback_adapter": self.fallback_adapter,
            "reason": self.reason,
            "human_review_required": self.human_review_required,
        }


@dataclass(frozen=True)
class ProviderDoctorReport:
    provider: str
    available: bool
    credential_present: bool
    sdk_present: bool
    probe_status: str
    error_code: ErrorCode | None = None

    def safe_summary(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "available": self.available,
            "credential_present": self.credential_present,
            "sdk_present": self.sdk_present,
            "probe_status": self.probe_status,
            "error_code": self.error_code.value if self.error_code else None,
        }


def map_provider_error(provider: str, raw_code: str, message: str) -> ProviderFailure:
    lowered = raw_code.lower()
    if "accesskey" in lowered or "auth" in lowered or "invalidsignature" in lowered:
        code = ErrorCode.AUTH_REQUIRED
    elif "invalidparameter" in lowered or "invalidinput" in lowered:
        code = ErrorCode.INVALID_INPUT
    elif "forbidden" in lowered or "permission" in lowered or lowered.startswith("ram") or ".ram" in lowered:
        code = ErrorCode.PERMISSION_DENIED
    elif "notopen" in lowered or "productnotopen" in lowered or "notenabled" in lowered:
        code = ErrorCode.PROVIDER_NOT_ENABLED
    elif "invalidurl" in lowered or "asset" in lowered and "access" in lowered:
        code = ErrorCode.ASSET_ACCESS_FAILED
    elif "unsupported" in lowered:
        code = ErrorCode.UNSUPPORTED_CAPABILITY
    elif "thrott" in lowered or "ratelimit" in lowered:
        code = ErrorCode.RATE_LIMITED
    elif "timeout" in lowered:
        code = ErrorCode.PROVIDER_TIMEOUT
    else:
        code = ErrorCode.PROVIDER_FAILED
    return ProviderFailure(provider, code, message[:300], raw_code)
