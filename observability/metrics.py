"""P04-03 local metrics contracts with conservative label redaction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
import json
import re

from core.application.retry import QueueDeliveryState, RetryDecision


_LABEL_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_LABEL_VALUE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SENSITIVE_KEY_TOKENS = {
    "api",
    "authorization",
    "body",
    "content",
    "cookie",
    "credential",
    "dsn",
    "endpoint",
    "file",
    "message",
    "password",
    "path",
    "payload",
    "secret",
    "token",
    "uri",
    "url",
}
_UNIX_PATH_MARKERS = tuple("/" + root + "/" for root in ("Users", "Volumes", "private", "tmp", "var"))
_WINDOWS_PATH = re.compile(r"[A-Za-z]:[\\/]")
_VALUE_MARKERS = ("bearer ", "cookie=", "authorization:", "sk_", "sk-")


class MetricName(str, Enum):
    AUDIT_EVENT_TOTAL = "audit_event_total"
    RETRY_DECISION_TOTAL = "retry_decision_total"
    DEAD_LETTER_TOTAL = "dead_letter_total"
    MANUAL_QUEUE_DEPTH = "manual_queue_depth"


def _key_is_sensitive(key: str) -> bool:
    tokens = {token for token in re.split(r"[^a-z0-9]+", key.lower()) if token}
    return bool(tokens & _SENSITIVE_KEY_TOKENS)


def _string_is_sensitive(value: str) -> bool:
    lowered = value.lower()
    if any(marker in value for marker in _UNIX_PATH_MARKERS):
        return True
    if _WINDOWS_PATH.search(value):
        return True
    if any(marker in lowered for marker in _VALUE_MARKERS):
        return True
    return _LABEL_VALUE.fullmatch(value) is None


def _safe_label_name(key: object) -> str:
    if not isinstance(key, str) or _LABEL_NAME.fullmatch(key) is None or _key_is_sensitive(key):
        return "redacted_label"
    return key


def _safe_label_value(value: object) -> object:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return "redacted_identifier" if _string_is_sensitive(value) else value
    return "redacted_identifier"


def _safe_labels(labels: Mapping[str, object] | None) -> dict[str, object]:
    if labels is None:
        return {}
    result: dict[str, object] = {}
    for key, value in labels.items():
        result[_safe_label_name(key)] = _safe_label_value(value)
    return result


@dataclass(frozen=True)
class MetricSample:
    name: MetricName
    value: int
    labels: Mapping[str, object]

    def safe_summary(self) -> dict[str, object]:
        return {
            "name": self.name.value,
            "value": self.value,
            "labels": dict(self.labels),
        }


class LocalMetricsRegistry:
    """Append-only local metric observations; no thresholds or external sink."""

    def __init__(self) -> None:
        self._samples: tuple[MetricSample, ...] = ()

    @property
    def samples(self) -> tuple[MetricSample, ...]:
        return self._samples

    def increment(
        self,
        name: MetricName,
        *,
        value: int = 1,
        labels: Mapping[str, object] | None = None,
    ) -> MetricSample:
        if not isinstance(name, MetricName):
            raise ValueError("metric_name_required")
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("metric_value_required")
        sample = MetricSample(name=name, value=value, labels=_safe_labels(labels))
        self._samples = (*self._samples, sample)
        return sample


def render_metrics_snapshot(registry: LocalMetricsRegistry) -> str:
    if not isinstance(registry, LocalMetricsRegistry):
        raise ValueError("metrics_registry_required")
    return json.dumps(
        [sample.safe_summary() for sample in registry.samples],
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def record_retry_metrics(registry: LocalMetricsRegistry, decision: RetryDecision) -> None:
    if not isinstance(decision, RetryDecision):
        raise ValueError("retry_decision_required")
    labels = {
        "correlation_id": decision.correlation_id,
        "retry_class": decision.retry_class.value,
        "delivery_state": decision.delivery_state.value,
        "effect": decision.effect.value,
        "error_code": decision.error_code,
        "manual_required": decision.manual_required,
    }
    registry.increment(MetricName.RETRY_DECISION_TOTAL, labels=labels)
    if decision.delivery_state is QueueDeliveryState.DEAD_LETTERED:
        registry.increment(MetricName.DEAD_LETTER_TOTAL, labels=labels)
    if decision.manual_required:
        registry.increment(MetricName.MANUAL_QUEUE_DEPTH, labels=labels)
