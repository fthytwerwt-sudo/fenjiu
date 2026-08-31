"""Runtime configuration loaded without exposing credential values."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable

from core.application.video_orchestrator.security import endpoint_allowed


_ALLOWED_ENV_NAMES = (
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_BASE_URL",
    "ALIBABA_CLOUD_ACCESS_KEY_ID",
    "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
    "ALIBABA_CLOUD_SECURITY_TOKEN",
    "AIDGE_REGION_ID",
    "AIDGE_ENDPOINT",
    "ALIBABA_OSS_ENDPOINT",
    "ALIBABA_OSS_BUCKET",
    "ALIBABA_OSS_OBJECT_PREFIX",
)
_CREDENTIAL_PLACEHOLDERS = {
    "FILL_ME",
    "LOCAL_ONLY_PLACEHOLDER",
    "LOCAL_ONLY_PLACEHOLDER_NOT_USED",
}


def _credential_value(values: dict[str, str], name: str) -> str:
    value = values.get(name, "").strip()
    return "" if value.upper() in _CREDENTIAL_PLACEHOLDERS else value


def load_allowlisted_env_file(path: Path, names: Iterable[str] = _ALLOWED_ENV_NAMES) -> dict[str, str]:
    allowed = set(names)
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("export "):
            stripped = stripped[7:].lstrip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        name = name.strip()
        if name not in allowed:
            continue
        result[name] = value.strip().strip('"').strip("'")
    return result


@dataclass(frozen=True)
class VideoRuntimeConfig:
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    alibaba_access_key_id: str = ""
    alibaba_access_key_secret: str = ""
    alibaba_security_token: str = ""
    aidge_region_id: str = "cn-beijing"
    aidge_endpoint: str = ""
    oss_endpoint: str = ""
    oss_bucket: str = ""
    oss_object_prefix: str = "video-orchestrator"

    @classmethod
    def from_environment(cls, *, env_file: Path | None = None) -> "VideoRuntimeConfig":
        values = dict(load_allowlisted_env_file(env_file or Path.cwd() / ".env"))
        values.update({name: value for name in _ALLOWED_ENV_NAMES if (value := os.environ.get(name))})
        return cls(
            dashscope_api_key=_credential_value(values, "DASHSCOPE_API_KEY"),
            dashscope_base_url=values.get(
                "DASHSCOPE_BASE_URL",
                "https://dashscope.aliyuncs.com/api/v1",
            ).rstrip("/"),
            alibaba_access_key_id=_credential_value(values, "ALIBABA_CLOUD_ACCESS_KEY_ID"),
            alibaba_access_key_secret=_credential_value(values, "ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
            alibaba_security_token=_credential_value(values, "ALIBABA_CLOUD_SECURITY_TOKEN"),
            aidge_region_id=values.get("AIDGE_REGION_ID", "cn-beijing"),
            aidge_endpoint=values.get("AIDGE_ENDPOINT", ""),
            oss_endpoint=values.get("ALIBABA_OSS_ENDPOINT", ""),
            oss_bucket=values.get("ALIBABA_OSS_BUCKET", ""),
            oss_object_prefix=values.get("ALIBABA_OSS_OBJECT_PREFIX", "video-orchestrator"),
        )

    def safe_summary(self) -> dict[str, object]:
        return {
            "dashscope_credential_present": bool(self.dashscope_api_key),
            "alibaba_access_key_present": bool(
                self.alibaba_access_key_id and self.alibaba_access_key_secret
            ),
            "alibaba_security_token_present": bool(self.alibaba_security_token),
            "aidge_region_id": self.aidge_region_id,
            "aidge_endpoint_configured": bool(self.aidge_endpoint),
            "dashscope_endpoint_allowed": endpoint_allowed(self.dashscope_base_url, service="dashscope"),
            "aidge_endpoint_allowed": endpoint_allowed(self.aidge_endpoint, service="aidge"),
            "oss_endpoint_allowed": endpoint_allowed(self.oss_endpoint, service="oss"),
            "oss_endpoint_configured": bool(self.oss_endpoint),
            "oss_bucket_configured": bool(self.oss_bucket),
            "oss_configured": bool(
                self.oss_endpoint
                and self.oss_bucket
                and self.alibaba_access_key_id
                and self.alibaba_access_key_secret
            ),
        }
