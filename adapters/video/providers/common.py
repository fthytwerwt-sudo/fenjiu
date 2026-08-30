"""Common execution results and minimal DashScope HTTP client."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any
import urllib.error
import urllib.request

from core.application.video_orchestrator.contracts import (
    ErrorCode,
    ProviderAdapterError,
    ProviderDoctorReport,
    ProviderExecutionResult,
    map_provider_error,
)
from core.application.video_orchestrator.config import VideoRuntimeConfig
from core.application.video_orchestrator.security import endpoint_allowed, validate_remote_url


class DashScopeHttpClient:
    def __init__(self, config: VideoRuntimeConfig | None = None) -> None:
        self.config = config or VideoRuntimeConfig.from_environment()

    def doctor(self, provider: str) -> ProviderDoctorReport:
        present = bool(self.config.dashscope_api_key)
        endpoint_ok = endpoint_allowed(self.config.dashscope_base_url, service="dashscope")
        return ProviderDoctorReport(
            provider=provider,
            available=present and endpoint_ok,
            credential_present=present,
            sdk_present=True,
            probe_status=("AUTH_CONFIGURED" if present else "AUTH_REQUIRED") if endpoint_ok else "BLOCKED_ENDPOINT_NOT_ALLOWED",
            error_code=(None if present else ErrorCode.AUTH_REQUIRED) if endpoint_ok else ErrorCode.PERMISSION_DENIED,
        )

    def post(self, provider: str, path: str, payload: dict[str, Any], *, asynchronous: bool = False) -> dict[str, Any]:
        if not self.config.dashscope_api_key:
            raise ProviderAdapterError(ErrorCode.AUTH_REQUIRED, "DashScope credential missing", provider=provider)
        if not endpoint_allowed(self.config.dashscope_base_url, service="dashscope"):
            raise ProviderAdapterError(ErrorCode.PERMISSION_DENIED, "DashScope endpoint is not allowlisted", provider=provider)
        headers = {
            "Authorization": f"Bearer {self.config.dashscope_api_key}",
            "Content-Type": "application/json",
        }
        if asynchronous:
            headers["X-DashScope-Async"] = "enable"
        request = urllib.request.Request(
            f"{self.config.dashscope_base_url}{path}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        return self._open_json(provider, request)

    def get(self, provider: str, path: str) -> dict[str, Any]:
        if not self.config.dashscope_api_key:
            raise ProviderAdapterError(ErrorCode.AUTH_REQUIRED, "DashScope credential missing", provider=provider)
        if not endpoint_allowed(self.config.dashscope_base_url, service="dashscope"):
            raise ProviderAdapterError(ErrorCode.PERMISSION_DENIED, "DashScope endpoint is not allowlisted", provider=provider)
        request = urllib.request.Request(
            f"{self.config.dashscope_base_url}{path}",
            headers={"Authorization": f"Bearer {self.config.dashscope_api_key}"},
            method="GET",
        )
        return self._open_json(provider, request)

    def _open_json(self, provider: str, request: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {}
            raw_code = str(payload.get("code") or payload.get("Code") or f"HTTP{exc.code}")
            failure = map_provider_error(provider, raw_code, str(payload.get("message") or payload.get("Message") or "provider request failed"))
            raise ProviderAdapterError(
                failure.code,
                failure.message,
                provider=provider,
                raw_provider_code=raw_code,
            ) from exc
        except urllib.error.URLError as exc:
            raise ProviderAdapterError(
                ErrorCode.PROVIDER_FAILED,
                "provider network request failed",
                provider=provider,
                raw_provider_code="UrlOpenError",
            ) from exc
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ProviderAdapterError(
                ErrorCode.OUTPUT_INVALID,
                "provider returned invalid JSON",
                provider=provider,
                raw_provider_code="InvalidJson",
            ) from exc


def poll_dashscope_task(
    client: DashScopeHttpClient,
    provider: str,
    task_id: str,
    *,
    timeout_seconds: int = 900,
    poll_interval: int = 15,
) -> ProviderExecutionResult:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        data = client.get(provider, f"/tasks/{task_id}")
        output = data.get("output") if isinstance(data.get("output"), dict) else {}
        status = str(output.get("task_status") or "UNKNOWN")
        if status == "SUCCEEDED":
            return ProviderExecutionResult(
                provider=provider,
                status=status,
                task_id=task_id,
                output_url=output.get("video_url") or output.get("audio_url"),
                usage=output.get("usage") if isinstance(output.get("usage"), dict) else {},
            )
        if status in {"FAILED", "CANCELED", "UNKNOWN"}:
            raw_code = str(output.get("code") or status)
            failure = map_provider_error(provider, raw_code, str(output.get("message") or status))
            raise ProviderAdapterError(
                failure.code,
                failure.message,
                provider=provider,
                raw_provider_code=raw_code,
            )
        time.sleep(max(1, poll_interval))
    raise ProviderAdapterError(
        ErrorCode.PROVIDER_TIMEOUT,
        "provider task polling timed out",
        provider=provider,
        raw_provider_code="Timeout",
    )


def download_binary(url: str, destination: Path) -> None:
    validate_remote_url(url, provider="provider_output_download", trusted_output=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=120) as response:
            data = response.read()
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise ProviderAdapterError(ErrorCode.ASSET_ACCESS_FAILED, "output download failed") from exc
    if not data:
        raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "downloaded output is empty")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def download_json(url: str) -> dict[str, Any]:
    validate_remote_url(url, provider="provider_output_download", trusted_output=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=120) as response:
            data = response.read()
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise ProviderAdapterError(ErrorCode.ASSET_ACCESS_FAILED, "JSON output download failed") from exc
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "downloaded JSON output is invalid") from exc
    if not isinstance(payload, dict):
        raise ProviderAdapterError(ErrorCode.OUTPUT_INVALID, "downloaded JSON output must be an object")
    return payload
