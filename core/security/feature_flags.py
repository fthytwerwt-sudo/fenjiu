"""Feature-flag port with immutable fail-closed Phase 1 behavior."""

from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable

from core.contracts import default_execution_policy


class FeatureFlagName(str, Enum):
    """Sensitive capabilities defined by the control-plane contract."""

    EXTERNAL_SEND = "external_send_enabled"
    CONTENT_PUBLISH = "content_publish_enabled"
    PRICE_QUOTE = "price_quote_enabled"
    REFUND = "refund_enabled"
    ORDER = "order_enabled"
    PAYMENT = "payment_enabled"
    INVENTORY_WRITE = "inventory_write_enabled"
    REAL_CRAWL = "real_crawl_enabled"
    REAL_VIDEO_PROVIDER = "real_video_provider_enabled"
    EXTERNAL_EXECUTION_ALLOWED = "external_execution_allowed"
    BUSINESS_EXTERNAL_READY = "business_external_ready"


_POLICY_ATTRIBUTE = {
    FeatureFlagName.EXTERNAL_SEND: "external_send",
    FeatureFlagName.CONTENT_PUBLISH: "public_publish",
    FeatureFlagName.PRICE_QUOTE: "real_quote",
    FeatureFlagName.REFUND: "refund",
    FeatureFlagName.ORDER: "order_create",
    FeatureFlagName.PAYMENT: "payment",
    FeatureFlagName.INVENTORY_WRITE: "inventory_writeback",
    FeatureFlagName.REAL_CRAWL: "real_crawl",
    FeatureFlagName.REAL_VIDEO_PROVIDER: "real_video",
    FeatureFlagName.EXTERNAL_EXECUTION_ALLOWED: "external_execution_allowed",
    FeatureFlagName.BUSINESS_EXTERNAL_READY: "business_external_ready",
}


@runtime_checkable
class FeatureFlagPort(Protocol):
    """Read-only port used by application policy checks."""

    def is_enabled(self, flag: FeatureFlagName | str) -> bool:
        """Return false for disabled, unknown, or invalid flags."""


class FailClosedFeatureFlags:
    """Static flag service with no override or configuration input surface."""

    __slots__ = ()

    def is_enabled(self, flag: FeatureFlagName | str) -> bool:
        try:
            normalized = flag if isinstance(flag, FeatureFlagName) else FeatureFlagName(flag)
        except (TypeError, ValueError):
            return False
        policy = default_execution_policy()
        return getattr(policy, _POLICY_ATTRIBUTE[normalized], False) is True

    def snapshot(self) -> dict[str, bool]:
        """Return a safe public table containing only disabled states."""

        return {flag.value: self.is_enabled(flag) for flag in FeatureFlagName}
