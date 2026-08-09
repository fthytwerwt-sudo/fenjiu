"""P07-02 zero-network fake video provider."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from hashlib import sha256

from adapters.video.contracts import (
    ProviderRunRef,
    ProviderRunState,
    QualityControlRef,
    QualityControlState,
    VideoArtifactRef,
    VideoManifest,
    VideoPortBoundaryError,
    _require_identifier,
    _stable_ref,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class FakeVideoProvider:
    """Fake VideoPort implementation that creates only references."""

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or _now_utc
        self._runs: dict[str, VideoManifest] = {}
        self._submission_count = 0
        self._external_call_count = 0

    @property
    def external_call_count(self) -> int:
        return self._external_call_count

    @property
    def submission_count(self) -> int:
        return self._submission_count

    def submit(self, manifest: VideoManifest) -> ProviderRunRef:
        if not isinstance(manifest, VideoManifest):
            raise VideoPortBoundaryError("video_manifest_required")
        provider_task_ref = manifest.provider_task_ref
        if provider_task_ref not in self._runs:
            self._runs[provider_task_ref] = manifest
            self._submission_count += 1
        return ProviderRunRef(
            provider_task_ref=provider_task_ref,
            manifest_id=manifest.manifest_id,
            manifest_version=manifest.manifest_version,
            state=ProviderRunState.SUBMITTED,
            idempotency_key=manifest.idempotency_key,
            external_call_count=0,
            may_auto_retry=False,
            manual_review_required=False,
            checked_at=self._now(),
        )

    def poll(self, provider_task_ref: str) -> ProviderRunRef:
        manifest = self._manifest(provider_task_ref)
        return ProviderRunRef(
            provider_task_ref=provider_task_ref,
            manifest_id=manifest.manifest_id,
            manifest_version=manifest.manifest_version,
            state=ProviderRunState.RUNNING,
            idempotency_key=manifest.idempotency_key,
            external_call_count=0,
            may_auto_retry=False,
            manual_review_required=False,
            checked_at=self._now(),
        )

    def download_artifact_ref(self, provider_task_ref: str) -> VideoArtifactRef:
        manifest = self._manifest(provider_task_ref)
        content_hash = sha256(f"{provider_task_ref}|{manifest.manifest_id}".encode("utf-8")).hexdigest()
        return VideoArtifactRef(
            artifact_ref=_stable_ref("artifact_ref", provider_task_ref, content_hash),
            provider_task_ref=provider_task_ref,
            manifest_id=manifest.manifest_id,
            state=ProviderRunState.DOWNLOADED,
            content_hash=content_hash,
            created_at=self._now(),
        )

    def create_qc_ref(self, artifact_ref: str) -> QualityControlRef:
        _require_identifier(artifact_ref, "artifact_ref_required")
        return QualityControlRef(
            qc_ref=_stable_ref("qc_ref", artifact_ref),
            artifact_ref=artifact_ref,
            state=QualityControlState.MANUAL_REVIEW_REQUIRED,
            quality_approved=False,
            manual_review_required=True,
            checked_at=self._now(),
        )

    def record_provider_uncertainty(
        self,
        manifest: VideoManifest,
        *,
        error_code: str,
    ) -> ProviderRunRef:
        if not isinstance(manifest, VideoManifest):
            raise VideoPortBoundaryError("video_manifest_required")
        _require_identifier(error_code, "error_code_required")
        return ProviderRunRef(
            provider_task_ref=manifest.provider_task_ref,
            manifest_id=manifest.manifest_id,
            manifest_version=manifest.manifest_version,
            state=ProviderRunState.MANUAL_REVIEW_REQUIRED,
            idempotency_key=manifest.idempotency_key,
            external_call_count=0,
            may_auto_retry=False,
            manual_review_required=True,
            checked_at=self._now(),
            error_code=error_code,
        )

    def _manifest(self, provider_task_ref: str) -> VideoManifest:
        _require_identifier(provider_task_ref, "provider_task_ref_required")
        manifest = self._runs.get(provider_task_ref)
        if manifest is None:
            raise VideoPortBoundaryError("provider_task_ref_unknown")
        return manifest
