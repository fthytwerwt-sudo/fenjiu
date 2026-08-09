"""Support adapter shell with no channel SDK or send path."""

from adapters.support.fake import FakeSupportPort, SupportAdapterBoundaryError, SupportInboundEnvelope

__all__ = [
    "FakeSupportPort",
    "SupportAdapterBoundaryError",
    "SupportInboundEnvelope",
]
