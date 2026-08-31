"""Private OSS upload plus short-lived signed GET URL bridge."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import importlib.util
from pathlib import Path
import time

from core.application.video_orchestrator.contracts import ErrorCode, ProviderAdapterError, ProviderDoctorReport
from core.application.video_orchestrator.config import VideoRuntimeConfig
from core.application.video_orchestrator.security import endpoint_allowed, validate_local_media


@dataclass(frozen=True)
class BridgedAsset:
    object_key: str
    signed_url: str
    expires_seconds: int

    def safe_summary(self) -> dict[str, object]:
        return {
            "asset_ref": f"asset:{sha256(self.object_key.encode()).hexdigest()[:24]}",
            "signed_url_present": bool(self.signed_url),
            "expires_seconds": self.expires_seconds,
            "public_bucket_required": False,
        }


class OssAssetBridge:
    provider_id = "alibaba_oss_asset_bridge"

    def __init__(self, config: VideoRuntimeConfig) -> None:
        self.config = config

    @classmethod
    def from_environment(cls) -> "OssAssetBridge":
        return cls(VideoRuntimeConfig.from_environment())

    def doctor(self) -> ProviderDoctorReport:
        credential_present = bool(
            self.config.alibaba_access_key_id and self.config.alibaba_access_key_secret
        )
        endpoint_configured = bool(self.config.oss_endpoint)
        bucket_configured = bool(self.config.oss_bucket)
        endpoint_ok = endpoint_allowed(self.config.oss_endpoint, service="oss")
        sdk_present = importlib.util.find_spec("oss2") is not None
        if not credential_present:
            error_code = ErrorCode.AUTH_REQUIRED
            status = "BLOCKED_OSS_CREDENTIALS_ABSENT"
        elif not endpoint_configured or not bucket_configured:
            error_code = ErrorCode.INVALID_INPUT
            status = "BLOCKED_OSS_CONFIG"
        elif not endpoint_ok:
            error_code = ErrorCode.PERMISSION_DENIED
            status = "BLOCKED_OSS_ENDPOINT_NOT_ALLOWED"
        elif not sdk_present:
            error_code = ErrorCode.PROVIDER_NOT_ENABLED
            status = "BLOCKED_OSS_SDK_MISSING"
        else:
            error_code = None
            status = "AVAILABLE"
        available = credential_present and endpoint_configured and bucket_configured and endpoint_ok and sdk_present
        return ProviderDoctorReport(
            provider=self.provider_id,
            available=available,
            credential_present=credential_present,
            sdk_present=sdk_present,
            probe_status=status,
            error_code=error_code,
        )

    def upload(
        self,
        local_path: str,
        *,
        asset_kind: str = "image",
        expires_seconds: int = 3600,
    ) -> BridgedAsset:
        report = self.doctor()
        if not report.available:
            raise ProviderAdapterError(ErrorCode.AUTH_REQUIRED, "private OSS bridge configuration missing", provider=self.provider_id)
        path = validate_local_media(local_path, provider=self.provider_id, asset_kind=asset_kind)
        if not 1800 <= expires_seconds <= 3600:
            raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "signed URL TTL must be 30 to 60 minutes", provider=self.provider_id)
        import oss2

        auth = oss2.Auth(self.config.alibaba_access_key_id, self.config.alibaba_access_key_secret)
        bucket = oss2.Bucket(auth, self.config.oss_endpoint, self.config.oss_bucket)
        digest = sha256(path.read_bytes()).hexdigest()
        prefix = self.config.oss_object_prefix.strip("/")
        object_key = f"{prefix}/aidge/{int(time.time())}-{digest[:20]}{path.suffix.lower()}"
        try:
            bucket.put_object_from_file(object_key, str(path))
            signed_url = bucket.sign_url("GET", object_key, expires_seconds)
        except Exception as exc:
            raise ProviderAdapterError(ErrorCode.ASSET_ACCESS_FAILED, "OSS private asset bridge failed", provider=self.provider_id) from exc
        return BridgedAsset(object_key, signed_url, expires_seconds)

    def cleanup(self, asset: BridgedAsset) -> None:
        report = self.doctor()
        if not report.available:
            return
        import oss2

        auth = oss2.Auth(self.config.alibaba_access_key_id, self.config.alibaba_access_key_secret)
        bucket = oss2.Bucket(auth, self.config.oss_endpoint, self.config.oss_bucket)
        bucket.delete_object(asset.object_key)
