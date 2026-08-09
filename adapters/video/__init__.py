"""Fake-only video adapter contracts with no provider SDK or media rendering."""

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
    "build_legacy_probe_baseline",
]
