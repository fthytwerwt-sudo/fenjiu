"""Alibaba Cloud Aidge VideoGeneration adapter using the official V2 SDK."""

from __future__ import annotations

import importlib.util
import json
import time
from typing import Any

from core.application.video_orchestrator.contracts import ErrorCode, ProviderAdapterError, ProviderDoctorReport
from core.application.video_orchestrator.config import VideoRuntimeConfig
from core.application.video_orchestrator.security import endpoint_allowed, validate_remote_url
from adapters.video.providers.common import ProviderExecutionResult


class AidgeVideoGenerationAdapter:
    provider_id = "aidge_video_generation"
    sdk_package = "alibabacloud_aidge20260428"
    api_version = "2026-04-28"
    action = "VideoGeneration"

    def __init__(self, config: VideoRuntimeConfig | None = None, *, client: Any = None) -> None:
        self.config = config or VideoRuntimeConfig.from_environment()
        self._client = client

    def build_request(
        self,
        *,
        images: tuple[str, ...],
        title: str,
        duration: int,
        ratio: str,
        quality: str,
        asset_bindings: tuple[dict[str, Any], ...] = (),
    ) -> dict[str, Any]:
        if not 1 <= len(images) <= 6:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "Aidge requires 1 to 6 image URLs", provider=self.provider_id)
        if not title or len(title) > 60:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "Aidge title must contain 1 to 60 characters", provider=self.provider_id)
        if duration not in range(5, 16) or ratio != "9:16" or quality not in {"720p", "1080p"}:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "Aidge output options are invalid", provider=self.provider_id)
        if any(not image.startswith(("http://", "https://")) for image in images):
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "Aidge images must be accessible URLs", provider=self.provider_id)
        for image in images:
            validate_remote_url(image, provider=self.provider_id)
        input_map: dict[str, Any] = {"Images": list(images), "Title": title}
        if asset_bindings:
            input_map["AssetBindings"] = [dict(item) for item in asset_bindings]
        return {
            "Input": input_map,
            "Output": {"Duration": duration, "Ratio": ratio, "Quality": quality},
        }

    def doctor(self) -> ProviderDoctorReport:
        credential_present = bool(
            self.config.alibaba_access_key_id and self.config.alibaba_access_key_secret
        )
        sdk_present = importlib.util.find_spec(self.sdk_package) is not None
        endpoint_ok = endpoint_allowed(self.config.aidge_endpoint, service="aidge")
        if not credential_present:
            error_code = ErrorCode.AUTH_REQUIRED
            status = "BLOCKED_AIDGE_CREDENTIALS_ABSENT"
        elif not endpoint_ok:
            error_code = ErrorCode.PERMISSION_DENIED
            status = "BLOCKED_AIDGE_ENDPOINT_NOT_ALLOWED"
        elif not sdk_present:
            error_code = ErrorCode.PROVIDER_NOT_ENABLED
            status = "BLOCKED_AIDGE_SDK_MISSING"
        else:
            error_code = None
            status = "PROBE_REQUIRED"
        return ProviderDoctorReport(
            provider=self.provider_id,
            available=credential_present and sdk_present and endpoint_ok,
            credential_present=credential_present,
            sdk_present=sdk_present,
            probe_status=status,
            error_code=error_code,
        )

    def _sdk_client(self) -> Any:
        if self._client is not None:
            if not self.config.alibaba_access_key_id or not self.config.alibaba_access_key_secret:
                raise ProviderAdapterError(ErrorCode.AUTH_REQUIRED, "Aidge AccessKey credentials missing", provider=self.provider_id)
            return self._client
        report = self.doctor()
        if not report.credential_present:
            raise ProviderAdapterError(ErrorCode.AUTH_REQUIRED, "Aidge AccessKey credentials missing", provider=self.provider_id)
        if not report.sdk_present:
            raise ProviderAdapterError(ErrorCode.PROVIDER_NOT_ENABLED, "Aidge official SDK is not installed", provider=self.provider_id)
        from alibabacloud_aidge20260428.client import Client
        from alibabacloud_tea_openapi.models import Config

        config = Config(
            access_key_id=self.config.alibaba_access_key_id,
            access_key_secret=self.config.alibaba_access_key_secret,
            security_token=self.config.alibaba_security_token or None,
            region_id=self.config.aidge_region_id,
        )
        if self.config.aidge_endpoint:
            config.endpoint = self.config.aidge_endpoint
        self._client = Client(config)
        return self._client

    def submit(self, request_map: dict[str, Any]) -> ProviderExecutionResult:
        client = self._sdk_client()
        if importlib.util.find_spec(self.sdk_package) is None:
            sdk_request = _MappingRequest(request_map)
        else:
            from alibabacloud_aidge20260428 import models

            input_map = request_map["Input"]
            output_map = request_map["Output"]
            bindings = [
                models.VideoGenerationRequestInputAssetBindings(
                    asset_index=item.get("AssetIndex"),
                    description=item.get("Description"),
                    slot=item.get("Slot"),
                )
                for item in input_map.get("AssetBindings", [])
            ]
            sdk_request = models.VideoGenerationRequest(
                input=models.VideoGenerationRequestInput(
                    images=input_map["Images"],
                    title=input_map["Title"],
                    asset_bindings=bindings or None,
                ),
                output=models.VideoGenerationRequestOutput(
                    duration=output_map["Duration"],
                    ratio=output_map["Ratio"],
                    quality=output_map["Quality"],
                ),
            )
        try:
            response = client.video_generation(sdk_request)
        except Exception as exc:
            raw = getattr(exc, "code", None) or exc.__class__.__name__
            text = str(exc).lower()
            if "forbidden" in text or "permission" in text:
                code = ErrorCode.PERMISSION_DENIED
            elif "not open" in text or "notenabled" in text:
                code = ErrorCode.PROVIDER_NOT_ENABLED
            else:
                code = ErrorCode.PROVIDER_FAILED
            raise ProviderAdapterError(code, "Aidge VideoGeneration request failed", provider=self.provider_id, raw_provider_code=str(raw)) from exc
        body = response.body
        if not body or body.success is not True or not body.data or not body.data.task_id:
            raw_code = str(getattr(body, "code", None) or "AidgeSubmitFailed")
            raise ProviderAdapterError(ErrorCode.PROVIDER_FAILED, "Aidge did not accept the task", provider=self.provider_id, raw_provider_code=raw_code)
        return ProviderExecutionResult(
            provider=self.provider_id,
            status="SUBMITTED",
            task_id=body.data.task_id,
            usage=dict(body.data.usage_map or {}),
        )

    def poll(self, task_id: str) -> ProviderExecutionResult:
        client = self._sdk_client()
        try:
            if importlib.util.find_spec(self.sdk_package) is None:
                query_request = _MappingRequest({"TaskId": task_id})
            else:
                from alibabacloud_aidge20260428 import models

                query_request = models.QueryAsyncTaskResultRequest(task_id=task_id)
            response = client.query_async_task_result(query_request)
        except Exception as exc:
            raise ProviderAdapterError(
                ErrorCode.PROVIDER_FAILED,
                "Aidge task query failed",
                provider=self.provider_id,
                raw_provider_code=str(getattr(exc, "code", None) or exc.__class__.__name__),
            ) from exc
        body = response.body
        if not body or body.success is not True or not body.data:
            raise ProviderAdapterError(ErrorCode.PROVIDER_FAILED, "Aidge task query returned no data", provider=self.provider_id)
        result_url = None
        if body.data.result:
            try:
                payload = json.loads(body.data.result)
            except json.JSONDecodeError:
                payload = {"result": body.data.result}
            result_url = _find_video_url(payload)
        return ProviderExecutionResult(
            provider=self.provider_id,
            status=str(body.data.status or "UNKNOWN"),
            task_id=task_id,
            output_url=result_url,
            usage=dict(body.data.usage_map or {}),
        )

    def wait(
        self,
        task_id: str,
        *,
        timeout_seconds: int = 900,
        poll_interval: int = 15,
    ) -> ProviderExecutionResult:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            result = self.poll(task_id)
            normalized = result.status.lower()
            if normalized in {"completed", "succeeded", "success"}:
                if not result.output_url:
                    raise ProviderAdapterError(
                        ErrorCode.OUTPUT_INVALID,
                        "Aidge completed without a video URL",
                        provider=self.provider_id,
                        raw_provider_code="AidgeVideoUrlMissing",
                    )
                return result
            if normalized in {"failed", "canceled", "cancelled"}:
                raise ProviderAdapterError(
                    ErrorCode.PROVIDER_FAILED,
                    "Aidge task failed",
                    provider=self.provider_id,
                    raw_provider_code=result.raw_provider_code or result.status,
                )
            time.sleep(max(1, poll_interval))
        raise ProviderAdapterError(
            ErrorCode.PROVIDER_TIMEOUT,
            "Aidge task polling timed out",
            provider=self.provider_id,
            raw_provider_code="Timeout",
        )


def _find_video_url(value: Any) -> str | None:
    if isinstance(value, str):
        return value if value.startswith(("http://", "https://")) and ".mp4" in value else None
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in {"videourl", "video_url", "url"} and isinstance(item, str) and item.startswith(("http://", "https://")):
                return item
            found = _find_video_url(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = _find_video_url(item)
            if found:
                return found
    return None


class _MappingRequest:
    """Test seam used only with an explicitly injected fake SDK client."""

    def __init__(self, value: dict[str, Any]) -> None:
        self._value = value

    def to_map(self) -> dict[str, Any]:
        return dict(self._value)
