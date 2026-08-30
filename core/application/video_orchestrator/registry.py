"""Machine-readable capability registry."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from core.application.video_orchestrator.contracts import CapabilityStatus, OrchestratorContractError


_REQUIRED_FIELDS = {
    "capability_id",
    "provider",
    "model_or_api",
    "status",
    "input_types",
    "output_types",
    "supported_duration",
    "supported_resolution",
    "supports_audio",
    "supports_reference",
    "supports_nepali",
    "cost_status",
    "credential_status",
    "current_probe_status",
    "primary_adapter",
    "fallback",
}


@dataclass(frozen=True)
class CapabilityRecord:
    capability_id: str
    provider: str
    model_or_api: str
    status: CapabilityStatus
    input_types: tuple[str, ...]
    output_types: tuple[str, ...]
    supported_duration: tuple[int, int] | None
    supported_resolution: tuple[str, ...]
    supports_audio: bool
    supports_reference: bool
    supports_nepali: bool
    cost_status: str
    credential_status: str
    current_probe_status: str
    primary_adapter: str
    fallback: str | None

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "CapabilityRecord":
        missing = sorted(_REQUIRED_FIELDS.difference(item))
        if missing:
            raise OrchestratorContractError(f"capability_fields_missing:{','.join(missing)}")
        duration = item["supported_duration"]
        if duration is not None:
            if not isinstance(duration, list) or len(duration) != 2:
                raise OrchestratorContractError("capability_duration_invalid")
            duration_value = (int(duration[0]), int(duration[1]))
        else:
            duration_value = None
        return cls(
            capability_id=str(item["capability_id"]),
            provider=str(item["provider"]),
            model_or_api=str(item["model_or_api"]),
            status=CapabilityStatus(str(item["status"])),
            input_types=tuple(str(value) for value in item["input_types"]),
            output_types=tuple(str(value) for value in item["output_types"]),
            supported_duration=duration_value,
            supported_resolution=tuple(str(value) for value in item["supported_resolution"]),
            supports_audio=bool(item["supports_audio"]),
            supports_reference=bool(item["supports_reference"]),
            supports_nepali=bool(item["supports_nepali"]),
            cost_status=str(item["cost_status"]),
            credential_status=str(item["credential_status"]),
            current_probe_status=str(item["current_probe_status"]),
            primary_adapter=str(item["primary_adapter"]),
            fallback=str(item["fallback"]) if item["fallback"] else None,
        )

    def safe_summary(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model_or_api": self.model_or_api,
            "status": self.status.value,
            "input_types": list(self.input_types),
            "output_types": list(self.output_types),
            "supported_duration": list(self.supported_duration) if self.supported_duration else None,
            "supported_resolution": list(self.supported_resolution),
            "supports_audio": self.supports_audio,
            "supports_reference": self.supports_reference,
            "supports_nepali": self.supports_nepali,
            "cost_status": self.cost_status,
            "credential_status": self.credential_status,
            "current_probe_status": self.current_probe_status,
            "primary_adapter": self.primary_adapter,
            "fallback": self.fallback,
        }


class CapabilityRegistry:
    def __init__(self, records: tuple[CapabilityRecord, ...]) -> None:
        by_id = {record.capability_id: record for record in records}
        if len(by_id) != len(records):
            raise OrchestratorContractError("duplicate_capability_id")
        self._records = by_id

    @classmethod
    def default(cls) -> "CapabilityRegistry":
        path = Path(__file__).with_name("capabilities.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != "video_orchestrator.capabilities.v1":
            raise OrchestratorContractError("capability_schema_invalid")
        return cls(tuple(CapabilityRecord.from_dict(item) for item in payload["capabilities"]))

    def capability_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._records))

    def get(self, capability_id: str) -> CapabilityRecord:
        try:
            return self._records[capability_id]
        except KeyError as exc:
            raise OrchestratorContractError("capability_unknown") from exc

    def safe_summary(self) -> dict[str, Any]:
        return {key: self._records[key].safe_summary() for key in sorted(self._records)}
