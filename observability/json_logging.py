"""Correlation-aware JSON logs with conservative metadata redaction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import json
import re
from typing import TextIO

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_SENSITIVE_KEY_TOKENS = {
    "api",
    "authorization",
    "body",
    "content",
    "cookie",
    "credential",
    "file",
    "message",
    "password",
    "path",
    "payload",
    "secret",
    "token",
}
_UNIX_PATH_MARKERS = tuple("/" + root + "/" for root in ("Users", "Volumes", "private", "tmp", "var"))
_WINDOWS_PATH = re.compile(r"[A-Za-z]:[\\/]")
_VALUE_MARKERS = ("bearer ", "cookie=", "authorization:", "sk_", "sk-")
_REDACTED = "[REDACTED]"


def _safe_identifier(value: object) -> str:
    if isinstance(value, str) and _SAFE_IDENTIFIER.fullmatch(value):
        return value
    return "redacted_identifier"


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
    if "\n" in value or "\r" in value or len(value) > 256:
        return True
    return False


def _redact_value(key: str, value: object) -> object:
    if _key_is_sensitive(key):
        return _REDACTED
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _REDACTED if _string_is_sensitive(value) else value
    if isinstance(value, Mapping):
        return {
            str(nested_key): _redact_value(str(nested_key), nested_value)
            for nested_key, nested_value in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact_value(key, item) for item in value]
    return _REDACTED


@dataclass(frozen=True)
class JsonLogEvent:
    """Minimal structured log event linked by a safe correlation identifier."""

    correlation_id: str
    component: str
    event: str
    result: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "correlation_id": _safe_identifier(self.correlation_id),
            "component": _safe_identifier(self.component),
            "event": _safe_identifier(self.event),
            "result": _safe_identifier(self.result),
            "metadata": {
                str(key): _redact_value(str(key), value)
                for key, value in self.metadata.items()
            },
        }


def render_json_log(event: JsonLogEvent) -> str:
    """Render one compact JSON record without raw object representations."""

    return json.dumps(event.as_dict(), ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def write_json_log(stream: TextIO, event: JsonLogEvent) -> None:
    """Write exactly one newline-delimited JSON record."""

    stream.write(render_json_log(event) + "\n")
