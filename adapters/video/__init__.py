"""Synthetic video contracts plus the explicit runtime composition root."""

from adapters.video.contracts import (
    LegacyCapability,
    LegacyProbeState,
    LegacyScriptProbe,
    LegacyVideoAdapterSpec,
    LegacyVideoOperation,
    ProviderRunRef,
    ProviderRunState,
    QualityControlRef,
    QualityControlState,
    VideoArtifactRef,
    VideoManifest,
    VideoPort,
    VideoPortBoundaryError,
    build_legacy_probe_baseline,
)
from adapters.video.fake import FakeVideoProvider
from adapters.video.runtime import VideoRuntimeAdapter

__all__ = [
    "FakeVideoProvider",
    "LegacyCapability",
    "LegacyProbeState",
    "LegacyScriptProbe",
    "LegacyVideoAdapterSpec",
    "LegacyVideoOperation",
    "ProviderRunRef",
    "ProviderRunState",
    "QualityControlRef",
    "QualityControlState",
    "VideoArtifactRef",
    "VideoManifest",
    "VideoPort",
    "VideoPortBoundaryError",
    "VideoRuntimeAdapter",
    "build_legacy_probe_baseline",
]
