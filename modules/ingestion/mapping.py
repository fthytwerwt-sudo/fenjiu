"""Value-free P03-02 mapping, normalization, quality, and replay contracts.

This module consumes only P03-01 synthetic staging records.  It never reads a
file, keeps a raw value, persists a fact, approves data, or enables an external
action.  "Normalization" intentionally produces a deterministic fingerprint
from an existing content hash and explicit control metadata; real-value parsing
belongs to a separately approved future adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Callable, Dict, Mapping, Optional, Tuple
from uuid import UUID, NAMESPACE_URL, uuid5

from core.contracts import DataState, ScopeRef
from modules.ingestion.contracts import (
    ExtractionResultRecord,
    FieldLocator,
    IngestionBoundaryError,
    IngestionJobRecord,
    IngestionWorkflowState,
    PrivateStorageLocator,
    SourceDisposition,
    SourceFileRecord,
    SourceKind,
    StagingCandidateRecord,
    _require_aware_time,
    _require_hash,
    _require_identifier,
    _reject_sensitive_text,
)


_ALLOWED_TRANSFORMS = frozenset(
    {
        "unicode_nfkc",
        "trim",
        "casefold",
        "decimal_canonical",
        "unit_check",
        "currency_check",
        "date_check",
        "language_check",
    }
)
_ATTRIBUTE_NAMES = frozenset({"unit", "currency", "date", "language"})


class MappingBoundaryError(IngestionBoundaryError):
    """Stable, value-free P03-02 boundary error."""


class AttributeStatus(str, Enum):
    """Whether a required normalization attribute is known without storing it."""

    KNOWN = "known"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class MappingRunState(str, Enum):
    MAPPED = "mapped"
    BLOCKED_MANUAL = "blocked_manual"


class QualityCode(str, Enum):
    PROFILE_MISSING = "profile_missing"
    SOURCE_SIGNATURE_MISMATCH = "source_signature_mismatch"
    CROSS_SCOPE = "cross_scope_forbidden"
    LINEAGE_INVALID = "lineage_invalid"
    UNMAPPED_SOURCE_FIELD = "unmapped_source_field"
    MISSING_REQUIRED = "required_missing"
    UNKNOWN_UNIT = "unknown_unit"
    UNKNOWN_CURRENCY = "unknown_currency"
    UNKNOWN_DATE = "unknown_date"
    UNKNOWN_LANGUAGE = "unknown_language"
    MAPPING_CONFLICT = "mapping_conflict"
    DUPLICATE_CANDIDATE = "duplicate_candidate"
    EXPIRED_OR_STALE = "expired_or_stale"
    FRESHNESS_TIME_INVALID = "freshness_time_invalid"


def _digest(*parts: object) -> str:
    material = "\x1f".join(str(part) for part in parts)
    return sha256(material.encode("utf-8")).hexdigest()


def _require_mapping_identifier(value: object, code: str) -> str:
    try:
        result = _require_identifier(value, code)
        _reject_sensitive_text(result)
    except IngestionBoundaryError as exc:
        raise MappingBoundaryError(code) from exc
    return result


def _require_mapping_hash(value: object, code: str) -> str:
    try:
        return _require_hash(value, code)
    except IngestionBoundaryError as exc:
        raise MappingBoundaryError(code) from exc


def _require_scope_mapping(value: object, code: str) -> ScopeRef:
    if not isinstance(value, ScopeRef):
        raise MappingBoundaryError(code)
    try:
        _reject_sensitive_text(value.correlation_id)
    except IngestionBoundaryError as exc:
        raise MappingBoundaryError(code) from exc
    return value


def _parse_scope(value: object) -> ScopeRef:
    if not isinstance(value, Mapping) or set(value) != {
        "tenant_id",
        "project_id",
        "business_line_id",
        "correlation_id",
    }:
        raise MappingBoundaryError("mapping_profile_schema_invalid")
    if any(not isinstance(value[key], str) for key in value):
        raise MappingBoundaryError("mapping_profile_schema_invalid")
    try:
        return ScopeRef(
            tenant_id=UUID(str(value["tenant_id"])),
            project_id=UUID(str(value["project_id"])),
            business_line_id=UUID(str(value["business_line_id"])),
            correlation_id=str(value["correlation_id"]),
        )
    except (TypeError, ValueError, IngestionBoundaryError) as exc:
        raise MappingBoundaryError("mapping_profile_schema_invalid") from exc


@dataclass(frozen=True)
class NormalizationDescriptor:
    """Value-free statuses used by deterministic synthetic normalizers."""

    unit: AttributeStatus = AttributeStatus.KNOWN
    currency: AttributeStatus = AttributeStatus.KNOWN
    date: AttributeStatus = AttributeStatus.KNOWN
    language: AttributeStatus = AttributeStatus.KNOWN

    def __post_init__(self) -> None:
        if any(
            not isinstance(item, AttributeStatus)
            for item in (self.unit, self.currency, self.date, self.language)
        ):
            raise MappingBoundaryError("normalization_descriptor_invalid")

    def status_for(self, attribute: str) -> AttributeStatus:
        if attribute not in _ATTRIBUTE_NAMES:
            raise MappingBoundaryError("normalization_attribute_invalid")
        return getattr(self, attribute)

    def fingerprint_part(self) -> str:
        return ":".join(
            (
                self.unit.value,
                self.currency.value,
                self.date.value,
                self.language.value,
            )
        )


@dataclass(frozen=True)
class TargetContract:
    """Frozen synthetic target field allowlist; not a business-data schema."""

    contract_id: str
    version: str
    fields: Tuple[str, ...]

    def __post_init__(self) -> None:
        _require_mapping_identifier(self.contract_id, "target_contract_invalid")
        _require_mapping_identifier(self.version, "target_contract_invalid")
        if not isinstance(self.fields, tuple) or not self.fields:
            raise MappingBoundaryError("target_contract_invalid")
        validated = tuple(
            _require_mapping_identifier(field, "target_contract_invalid")
            for field in self.fields
        )
        if len(set(validated)) != len(validated):
            raise MappingBoundaryError("target_contract_invalid")

    def to_mapping(self) -> dict[str, object]:
        return {
            "id": self.contract_id,
            "version": self.version,
            "fields": list(self.fields),
        }


@dataclass(frozen=True)
class MappingRule:
    """One explicit source-field to target-field configuration rule."""

    rule_id: str
    source_field: str
    target_field: str
    transforms: Tuple[str, ...]
    required: bool
    required_attributes: Tuple[str, ...]
    freshness_seconds: Optional[int]

    def __post_init__(self) -> None:
        _require_mapping_identifier(self.rule_id, "mapping_rule_invalid")
        _require_mapping_identifier(self.source_field, "mapping_rule_invalid")
        _require_mapping_identifier(self.target_field, "mapping_rule_invalid")
        if not isinstance(self.transforms, tuple) or not self.transforms:
            raise MappingBoundaryError("mapping_rule_invalid")
        if any(not isinstance(item, str) or item not in _ALLOWED_TRANSFORMS for item in self.transforms):
            raise MappingBoundaryError("mapping_rule_invalid")
        if len(set(self.transforms)) != len(self.transforms):
            raise MappingBoundaryError("mapping_rule_invalid")
        if not isinstance(self.required, bool):
            raise MappingBoundaryError("mapping_rule_invalid")
        if not isinstance(self.required_attributes, tuple):
            raise MappingBoundaryError("mapping_rule_invalid")
        if (
            any(item not in _ATTRIBUTE_NAMES for item in self.required_attributes)
            or len(set(self.required_attributes)) != len(self.required_attributes)
        ):
            raise MappingBoundaryError("mapping_rule_invalid")
        if self.freshness_seconds is not None and (
            not isinstance(self.freshness_seconds, int)
            or isinstance(self.freshness_seconds, bool)
            or self.freshness_seconds < 1
        ):
            raise MappingBoundaryError("mapping_rule_invalid")

    def to_mapping(self) -> dict[str, object]:
        return {
            "id": self.rule_id,
            "source_field": self.source_field,
            "target_field": self.target_field,
            "transforms": list(self.transforms),
            "required": self.required,
            "required_attributes": list(self.required_attributes),
            "freshness_seconds": self.freshness_seconds,
        }


@dataclass(frozen=True)
class MappingProfile:
    """Strict, versioned, scope-bound mapping profile parsed from JSON-style data."""

    profile_id: str
    version: str
    scope: ScopeRef
    source_signature: str
    target_contract: TargetContract
    rules: Tuple[MappingRule, ...]

    def __post_init__(self) -> None:
        _require_mapping_identifier(self.profile_id, "mapping_profile_invalid")
        _require_mapping_identifier(self.version, "mapping_profile_invalid")
        _require_scope_mapping(self.scope, "mapping_profile_invalid")
        _require_mapping_hash(self.source_signature, "mapping_profile_invalid")
        if not isinstance(self.target_contract, TargetContract):
            raise MappingBoundaryError("target_contract_invalid")
        if not isinstance(self.rules, tuple) or not self.rules:
            raise MappingBoundaryError("mapping_profile_invalid")
        if any(not isinstance(rule, MappingRule) for rule in self.rules):
            raise MappingBoundaryError("mapping_profile_invalid")
        if len({rule.rule_id for rule in self.rules}) != len(self.rules):
            raise MappingBoundaryError("mapping_profile_invalid")
        if len({rule.source_field for rule in self.rules}) != len(self.rules):
            raise MappingBoundaryError("mapping_profile_invalid")
        if any(rule.target_field not in self.target_contract.fields for rule in self.rules):
            raise MappingBoundaryError("target_contract_invalid")

    @property
    def synthetic_storage_locator(self) -> PrivateStorageLocator:
        return PrivateStorageLocator.parse("private/synthetic/mapping_input.csv")

    @property
    def synthetic_source_kind(self) -> SourceKind:
        return SourceKind.CSV

    @property
    def synthetic_source_disposition(self) -> SourceDisposition:
        return SourceDisposition.REGISTERED

    @property
    def fingerprint(self) -> str:
        return _digest(
            self.profile_id,
            self.version,
            self.scope.tenant_id,
            self.scope.project_id,
            self.scope.business_line_id,
            self.scope.correlation_id,
            self.source_signature,
            self.target_contract.contract_id,
            self.target_contract.version,
            *self.target_contract.fields,
            *(item for rule in self.rules for item in self._rule_fingerprint_parts(rule)),
        )

    @staticmethod
    def _rule_fingerprint_parts(rule: MappingRule) -> tuple[object, ...]:
        return (
            rule.rule_id,
            rule.source_field,
            rule.target_field,
            *rule.transforms,
            rule.required,
            *rule.required_attributes,
            rule.freshness_seconds,
        )

    @classmethod
    def from_mapping(cls, value: object) -> "MappingProfile":
        expected_keys = {
            "profile_id",
            "version",
            "scope",
            "source_signature",
            "target_contract",
            "rules",
        }
        if not isinstance(value, Mapping) or set(value) != expected_keys:
            raise MappingBoundaryError("mapping_profile_schema_invalid")
        target_payload = value["target_contract"]
        if (
            not isinstance(target_payload, Mapping)
            or set(target_payload) != {"id", "version", "fields"}
            or not isinstance(target_payload["fields"], list)
        ):
            raise MappingBoundaryError("mapping_profile_schema_invalid")
        rules_payload = value["rules"]
        if not isinstance(rules_payload, list) or not rules_payload:
            raise MappingBoundaryError("mapping_profile_schema_invalid")
        try:
            contract = TargetContract(
                contract_id=target_payload["id"],
                version=target_payload["version"],
                fields=tuple(target_payload["fields"]),
            )
            rules = tuple(cls._rule_from_mapping(item) for item in rules_payload)
            return cls(
                profile_id=value["profile_id"],
                version=value["version"],
                scope=_parse_scope(value["scope"]),
                source_signature=value["source_signature"],
                target_contract=contract,
                rules=rules,
            )
        except (KeyError, TypeError, MappingBoundaryError, IngestionBoundaryError) as exc:
            raise MappingBoundaryError("mapping_profile_schema_invalid") from exc

    @staticmethod
    def _rule_from_mapping(value: object) -> MappingRule:
        expected_keys = {
            "id",
            "source_field",
            "target_field",
            "transforms",
            "required",
            "required_attributes",
            "freshness_seconds",
        }
        if not isinstance(value, Mapping) or set(value) != expected_keys:
            raise MappingBoundaryError("mapping_profile_schema_invalid")
        if not isinstance(value["transforms"], list) or not isinstance(
            value["required_attributes"], list
        ):
            raise MappingBoundaryError("mapping_profile_schema_invalid")
        try:
            return MappingRule(
                rule_id=value["id"],
                source_field=value["source_field"],
                target_field=value["target_field"],
                transforms=tuple(value["transforms"]),
                required=value["required"],
                required_attributes=tuple(value["required_attributes"]),
                freshness_seconds=value["freshness_seconds"],
            )
        except (TypeError, MappingBoundaryError) as exc:
            raise MappingBoundaryError("mapping_profile_schema_invalid") from exc

    def to_mapping(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "scope": {
                "tenant_id": str(self.scope.tenant_id),
                "project_id": str(self.scope.project_id),
                "business_line_id": str(self.scope.business_line_id),
                "correlation_id": self.scope.correlation_id,
            },
            "source_signature": self.source_signature,
            "target_contract": self.target_contract.to_mapping(),
            "rules": [rule.to_mapping() for rule in self.rules],
        }


@dataclass(frozen=True)
class MappingEvidence:
    """One P03-01 record chain plus value-free normalization control metadata."""

    source_file: object
    ingestion_job: object
    extraction_result: object
    staging_candidate: object
    descriptor: object
    observed_at: object

    def validate(self, scope: ScopeRef) -> None:
        if not all(
            isinstance(item, expected)
            for item, expected in (
                (self.source_file, SourceFileRecord),
                (self.ingestion_job, IngestionJobRecord),
                (self.extraction_result, ExtractionResultRecord),
                (self.staging_candidate, StagingCandidateRecord),
                (self.descriptor, NormalizationDescriptor),
            )
        ):
            raise MappingBoundaryError("lineage_invalid")
        try:
            _require_aware_time(self.observed_at, "lineage_invalid")
        except IngestionBoundaryError as exc:
            raise MappingBoundaryError("lineage_invalid") from exc
        if (
            self.source_file.disposition is not SourceDisposition.REGISTERED
            or self.ingestion_job.workflow_state is not IngestionWorkflowState.STAGED
            or self.staging_candidate.workflow_state is not IngestionWorkflowState.STAGED
        ):
            raise MappingBoundaryError("lineage_invalid")
        records = (
            self.source_file,
            self.ingestion_job,
            self.extraction_result,
            self.staging_candidate,
        )
        if any(record.scope != scope for record in records):
            raise MappingBoundaryError("cross_scope_forbidden")
        if (
            self.ingestion_job.source_file_id != self.source_file.id
            or self.extraction_result.source_file_id != self.source_file.id
            or self.extraction_result.ingestion_job_id != self.ingestion_job.id
            or self.staging_candidate.source_file_id != self.source_file.id
            or self.staging_candidate.ingestion_job_id != self.ingestion_job.id
            or self.staging_candidate.extraction_result_id != self.extraction_result.id
            or self.staging_candidate.field_name != self.extraction_result.field_name
            or self.staging_candidate.content_hash != self.extraction_result.content_hash
            or self.staging_candidate.locator != self.extraction_result.locator
            or self.source_file.source_kind is None
        ):
            raise MappingBoundaryError("lineage_invalid")
        try:
            self.extraction_result.locator.validate_for(self.source_file.source_kind)
        except IngestionBoundaryError as exc:
            raise MappingBoundaryError("lineage_invalid") from exc

    def lineage(self) -> "MappingEvidenceLineage":
        if not isinstance(self.source_file, SourceFileRecord) or not isinstance(
            self.ingestion_job, IngestionJobRecord
        ) or not isinstance(self.extraction_result, ExtractionResultRecord) or not isinstance(
            self.staging_candidate, StagingCandidateRecord
        ):
            raise MappingBoundaryError("lineage_invalid")
        return MappingEvidenceLineage(
            source_file_id=self.source_file.id,
            ingestion_job_id=self.ingestion_job.id,
            extraction_result_id=self.extraction_result.id,
            staging_candidate_id=self.staging_candidate.id,
            locator=self.extraction_result.locator,
        )


@dataclass(frozen=True)
class MappingBatch:
    """A caller-provided synthetic batch; no file or content access surface."""

    scope: ScopeRef
    source_signature: str
    evidence: Tuple[MappingEvidence, ...]

    def __post_init__(self) -> None:
        _require_scope_mapping(self.scope, "mapping_batch_invalid")
        _require_mapping_hash(self.source_signature, "mapping_batch_invalid")
        if not isinstance(self.evidence, tuple) or any(
            not isinstance(item, MappingEvidence) for item in self.evidence
        ):
            raise MappingBoundaryError("mapping_batch_invalid")

    @property
    def fingerprint(self) -> str:
        parts: list[object] = [
            self.scope.tenant_id,
            self.scope.project_id,
            self.scope.business_line_id,
            self.scope.correlation_id,
            self.source_signature,
        ]
        for item in sorted(self.evidence, key=self._evidence_sort_key):
            parts.extend(self._evidence_fingerprint_parts(item))
        return _digest(*parts)

    @staticmethod
    def _evidence_sort_key(item: MappingEvidence) -> str:
        if isinstance(item.staging_candidate, StagingCandidateRecord):
            return item.staging_candidate.id.hex
        return repr(type(item.staging_candidate))

    @staticmethod
    def _evidence_fingerprint_parts(item: MappingEvidence) -> tuple[object, ...]:
        if not isinstance(item.source_file, SourceFileRecord) or not isinstance(
            item.ingestion_job, IngestionJobRecord
        ) or not isinstance(item.extraction_result, ExtractionResultRecord) or not isinstance(
            item.staging_candidate, StagingCandidateRecord
        ) or not isinstance(item.descriptor, NormalizationDescriptor):
            return ("invalid_evidence",)
        return (
            item.source_file.id,
            item.ingestion_job.id,
            item.extraction_result.id,
            item.staging_candidate.id,
            item.extraction_result.content_hash,
            item.descriptor.fingerprint_part(),
            item.observed_at,
        )


@dataclass(frozen=True)
class MappingEvidenceLineage:
    """Safe source and locator reference exposed by a mapping report."""

    source_file_id: UUID
    ingestion_job_id: UUID
    extraction_result_id: UUID
    staging_candidate_id: UUID
    locator: FieldLocator


@dataclass(frozen=True)
class MappedCandidate:
    """A synthetic candidate retaining immutable input and rule/profile lineage."""

    id: UUID
    scope: ScopeRef
    source_file_id: UUID
    ingestion_job_id: UUID
    extraction_result_id: UUID
    staging_candidate_id: UUID
    locator: FieldLocator
    source_content_hash: str
    normalized_value_hash: str
    target_field: str
    profile_id: str
    profile_version: str
    rule_id: str
    descriptor: NormalizationDescriptor
    observed_at: datetime
    state: MappingRunState
    data_state: DataState = DataState.FIXTURE
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _require_scope_mapping(self.scope, "mapped_candidate_invalid")
        for value in (
            self.source_file_id,
            self.ingestion_job_id,
            self.extraction_result_id,
            self.staging_candidate_id,
        ):
            if not isinstance(value, UUID) or value.int == 0:
                raise MappingBoundaryError("mapped_candidate_invalid")
        if not isinstance(self.locator, FieldLocator) or not self.locator.has_traceable_location:
            raise MappingBoundaryError("mapped_candidate_invalid")
        _require_mapping_hash(self.source_content_hash, "mapped_candidate_invalid")
        _require_mapping_hash(self.normalized_value_hash, "mapped_candidate_invalid")
        for value in (self.target_field, self.profile_id, self.profile_version, self.rule_id):
            _require_mapping_identifier(value, "mapped_candidate_invalid")
        if not isinstance(self.descriptor, NormalizationDescriptor):
            raise MappingBoundaryError("mapped_candidate_invalid")
        try:
            _require_aware_time(self.observed_at, "mapped_candidate_invalid")
        except IngestionBoundaryError as exc:
            raise MappingBoundaryError("mapped_candidate_invalid") from exc
        if not isinstance(self.state, MappingRunState):
            raise MappingBoundaryError("mapped_candidate_invalid")
        if (
            self.data_state is not DataState.FIXTURE
            or self.is_synthetic is not True
            or self.external_execution_allowed is not False
            or self.business_external_ready is not False
        ):
            raise MappingBoundaryError("synthetic_mapping_required")

    @property
    def fingerprint(self) -> str:
        return _digest(
            self.id,
            self.source_file_id,
            self.ingestion_job_id,
            self.extraction_result_id,
            self.staging_candidate_id,
            self.target_field,
            self.normalized_value_hash,
            self.profile_id,
            self.profile_version,
            self.rule_id,
            self.state.value,
        )

    @property
    def semantic_key(self) -> str:
        return _digest(
            self.source_file_id,
            self.ingestion_job_id,
            self.extraction_result_id,
            self.staging_candidate_id,
            self.target_field,
        )


@dataclass(frozen=True)
class QualityFinding:
    """Stable, value-free quality finding; references only candidate IDs."""

    code: QualityCode
    scope: ScopeRef
    profile_id: Optional[str]
    profile_version: Optional[str]
    target_field: Optional[str]
    rule_id: Optional[str]
    candidate_ids: Tuple[UUID, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.code, QualityCode):
            raise MappingBoundaryError("quality_finding_invalid")
        _require_scope_mapping(self.scope, "quality_finding_invalid")
        for value in (self.profile_id, self.profile_version, self.target_field, self.rule_id):
            if value is not None:
                _require_mapping_identifier(value, "quality_finding_invalid")
        if not isinstance(self.candidate_ids, tuple) or any(
            not isinstance(item, UUID) or item.int == 0 for item in self.candidate_ids
        ):
            raise MappingBoundaryError("quality_finding_invalid")
        if len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise MappingBoundaryError("quality_finding_invalid")

    def sort_key(self) -> tuple[object, ...]:
        return (
            self.code.value,
            self.target_field or "",
            self.rule_id or "",
            tuple(item.hex for item in self.candidate_ids),
        )


@dataclass(frozen=True)
class MappingReport:
    """Immutable replay output containing only lineage IDs, hashes, and codes."""

    state: MappingRunState
    scope: ScopeRef
    profile_id: Optional[str]
    profile_version: Optional[str]
    profile_fingerprint: Optional[str]
    input_fingerprint: str
    input_evidence_ids: Tuple[MappingEvidenceLineage, ...]
    candidates: Tuple[MappedCandidate, ...]
    findings: Tuple[QualityFinding, ...]
    run_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, MappingRunState):
            raise MappingBoundaryError("mapping_report_invalid")
        _require_scope_mapping(self.scope, "mapping_report_invalid")
        profile_identity = (
            self.profile_id,
            self.profile_version,
            self.profile_fingerprint,
        )
        if any(value is None for value in profile_identity) and any(
            value is not None for value in profile_identity
        ):
            raise MappingBoundaryError("mapping_report_invalid")
        for value in (self.profile_id, self.profile_version):
            if value is not None:
                _require_mapping_identifier(value, "mapping_report_invalid")
        if self.profile_fingerprint is not None:
            _require_mapping_hash(self.profile_fingerprint, "mapping_report_invalid")
        _require_mapping_hash(self.input_fingerprint, "mapping_report_invalid")
        _require_mapping_hash(self.run_fingerprint, "mapping_report_invalid")
        if any(not isinstance(item, MappingEvidenceLineage) for item in self.input_evidence_ids):
            raise MappingBoundaryError("mapping_report_invalid")
        if any(not isinstance(item, MappedCandidate) for item in self.candidates):
            raise MappingBoundaryError("mapping_report_invalid")
        if any(not isinstance(item, QualityFinding) for item in self.findings):
            raise MappingBoundaryError("mapping_report_invalid")
        if tuple(sorted(self.findings, key=lambda item: item.sort_key())) != self.findings:
            raise MappingBoundaryError("mapping_report_invalid")

    def safe_summary(self) -> dict[str, object]:
        counts: Dict[str, int] = {}
        for finding in self.findings:
            counts[finding.code.value] = counts.get(finding.code.value, 0) + 1
        return {
            "state": self.state.value,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "input_count": len(self.input_evidence_ids),
            "candidate_count": len(self.candidates),
            "finding_counts": dict(sorted(counts.items())),
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


@dataclass(frozen=True)
class ProfileReplayDiff:
    """Append-only evidence that a changed profile was replayed rather than overwritten."""

    profile_id: str
    previous_version: str
    current_version: str
    previous_run_fingerprint: str
    current_run_fingerprint: str
    added_candidate_fingerprints: Tuple[str, ...]
    removed_candidate_fingerprints: Tuple[str, ...]
    changed_candidate_keys: Tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (self.profile_id, self.previous_version, self.current_version):
            _require_mapping_identifier(value, "profile_replay_diff_invalid")
        _require_mapping_hash(self.previous_run_fingerprint, "profile_replay_diff_invalid")
        _require_mapping_hash(self.current_run_fingerprint, "profile_replay_diff_invalid")
        for collection in (
            self.added_candidate_fingerprints,
            self.removed_candidate_fingerprints,
            self.changed_candidate_keys,
        ):
            if not isinstance(collection, tuple):
                raise MappingBoundaryError("profile_replay_diff_invalid")
            for value in collection:
                _require_mapping_hash(value, "profile_replay_diff_invalid")

    @property
    def changed_or_added_or_removed(self) -> bool:
        return bool(
            self.added_candidate_fingerprints
            or self.removed_candidate_fingerprints
            or self.changed_candidate_keys
        )


class SyntheticMappingEngine:
    """Pure, deterministic config mapping and quality engine with no write surface."""

    def __init__(self, now: Optional[Callable[[], datetime]] = None) -> None:
        self._now = now or (lambda: datetime.now(timezone.utc))

    def map(self, profile: Optional[MappingProfile], batch: MappingBatch) -> MappingReport:
        if not isinstance(batch, MappingBatch):
            raise MappingBoundaryError("mapping_batch_invalid")
        if profile is None:
            return self._blocked_report(batch, None, QualityCode.PROFILE_MISSING)
        if not isinstance(profile, MappingProfile):
            raise MappingBoundaryError("mapping_profile_invalid")
        if profile.scope != batch.scope:
            return self._blocked_report(batch, profile, QualityCode.CROSS_SCOPE)
        if profile.source_signature != batch.source_signature:
            return self._blocked_report(batch, profile, QualityCode.SOURCE_SIGNATURE_MISMATCH)

        valid_evidence: list[MappingEvidence] = []
        lineages: list[MappingEvidenceLineage] = []
        findings: list[QualityFinding] = []
        for evidence in sorted(batch.evidence, key=MappingBatch._evidence_sort_key):
            try:
                evidence.validate(batch.scope)
                valid_evidence.append(evidence)
                lineages.append(evidence.lineage())
            except MappingBoundaryError as exc:
                code = (
                    QualityCode.CROSS_SCOPE
                    if exc.code == "cross_scope_forbidden"
                    else QualityCode.LINEAGE_INVALID
                )
                findings.append(self._finding(profile, batch.scope, code))

        if findings:
            return self._report(
                batch=batch,
                profile=profile,
                lineages=tuple(lineages),
                candidates=(),
                findings=tuple(findings),
            )

        rules_by_source = {rule.source_field: rule for rule in profile.rules}
        candidates: list[MappedCandidate] = []
        now = self._checked_now()
        for evidence in valid_evidence:
            result = evidence.extraction_result
            if not isinstance(result, ExtractionResultRecord):
                return self._blocked_report(batch, profile, QualityCode.LINEAGE_INVALID)
            rule = rules_by_source.get(result.field_name)
            if rule is None:
                findings.append(
                    self._finding(
                        profile,
                        batch.scope,
                        QualityCode.UNMAPPED_SOURCE_FIELD,
                    )
                )
                continue
            candidates.append(self._candidate(profile, rule, evidence))

        findings.extend(self._quality_findings(profile, tuple(candidates), now))
        return self._report(
            batch=batch,
            profile=profile,
            lineages=tuple(lineages),
            candidates=tuple(sorted(candidates, key=lambda item: item.id.hex)),
            findings=tuple(findings),
        )

    def _checked_now(self) -> datetime:
        value = self._now()
        try:
            _require_aware_time(value, "mapping_clock_invalid")
        except IngestionBoundaryError as exc:
            raise MappingBoundaryError("mapping_clock_invalid") from exc
        return value

    def _candidate(
        self,
        profile: MappingProfile,
        rule: MappingRule,
        evidence: MappingEvidence,
    ) -> MappedCandidate:
        if not isinstance(evidence.extraction_result, ExtractionResultRecord) or not isinstance(
            evidence.staging_candidate, StagingCandidateRecord
        ) or not isinstance(evidence.source_file, SourceFileRecord) or not isinstance(
            evidence.ingestion_job, IngestionJobRecord
        ) or not isinstance(evidence.descriptor, NormalizationDescriptor) or not isinstance(
            evidence.observed_at, datetime
        ):
            raise MappingBoundaryError("lineage_invalid")
        source_hash = evidence.extraction_result.content_hash
        normalized_hash = _digest(source_hash, *rule.transforms, evidence.descriptor.fingerprint_part())
        unknown_required = any(
            evidence.descriptor.status_for(attribute) is AttributeStatus.UNKNOWN
            for attribute in rule.required_attributes
        )
        state = MappingRunState.BLOCKED_MANUAL if unknown_required else MappingRunState.MAPPED
        identifier = uuid5(
            NAMESPACE_URL,
            "|".join(
                (
                    profile.profile_id,
                    profile.version,
                    str(evidence.staging_candidate.id),
                    rule.rule_id,
                    rule.target_field,
                    normalized_hash,
                )
            ),
        )
        return MappedCandidate(
            id=identifier,
            scope=evidence.source_file.scope,
            source_file_id=evidence.source_file.id,
            ingestion_job_id=evidence.ingestion_job.id,
            extraction_result_id=evidence.extraction_result.id,
            staging_candidate_id=evidence.staging_candidate.id,
            locator=evidence.extraction_result.locator,
            source_content_hash=source_hash,
            normalized_value_hash=normalized_hash,
            target_field=rule.target_field,
            profile_id=profile.profile_id,
            profile_version=profile.version,
            rule_id=rule.rule_id,
            descriptor=evidence.descriptor,
            observed_at=evidence.observed_at,
            state=state,
        )

    def _quality_findings(
        self,
        profile: MappingProfile,
        candidates: Tuple[MappedCandidate, ...],
        now: datetime,
    ) -> list[QualityFinding]:
        findings: list[QualityFinding] = []
        candidates_by_target: Dict[str, list[MappedCandidate]] = {}
        for candidate in candidates:
            candidates_by_target.setdefault(candidate.target_field, []).append(candidate)
            rule = next(rule for rule in profile.rules if rule.rule_id == candidate.rule_id)
            for attribute, code in (
                ("unit", QualityCode.UNKNOWN_UNIT),
                ("currency", QualityCode.UNKNOWN_CURRENCY),
                ("date", QualityCode.UNKNOWN_DATE),
                ("language", QualityCode.UNKNOWN_LANGUAGE),
            ):
                if (
                    attribute in rule.required_attributes
                    and candidate.descriptor.status_for(attribute) is AttributeStatus.UNKNOWN
                ):
                    findings.append(
                        self._finding(
                            profile,
                            candidate.scope,
                            code,
                            target_field=candidate.target_field,
                            rule_id=rule.rule_id,
                            candidate_ids=(candidate.id,),
                        )
                    )
            if rule.freshness_seconds is not None:
                age_seconds = (now - candidate.observed_at).total_seconds()
                code = (
                    QualityCode.FRESHNESS_TIME_INVALID
                    if age_seconds < 0
                    else QualityCode.EXPIRED_OR_STALE
                )
                if age_seconds < 0 or age_seconds > rule.freshness_seconds:
                    findings.append(
                        self._finding(
                            profile,
                            candidate.scope,
                            code,
                            target_field=candidate.target_field,
                            rule_id=rule.rule_id,
                            candidate_ids=(candidate.id,),
                        )
                    )

        for target in {rule.target_field for rule in profile.rules if rule.required}:
            if target not in candidates_by_target:
                findings.append(
                    self._finding(
                        profile,
                        profile.scope,
                        QualityCode.MISSING_REQUIRED,
                        target_field=target,
                    )
                )

        for target, grouped in candidates_by_target.items():
            if len(grouped) < 2:
                continue
            all_ids = tuple(sorted((item.id for item in grouped), key=lambda item: item.hex))
            normalized_groups: Dict[str, list[MappedCandidate]] = {}
            for candidate in grouped:
                normalized_groups.setdefault(candidate.normalized_value_hash, []).append(candidate)
            for duplicates in normalized_groups.values():
                if len(duplicates) > 1:
                    findings.append(
                        self._finding(
                            profile,
                            profile.scope,
                            QualityCode.DUPLICATE_CANDIDATE,
                            target_field=target,
                            candidate_ids=tuple(
                                sorted((item.id for item in duplicates), key=lambda item: item.hex)
                            ),
                        )
                    )
            if len(normalized_groups) > 1:
                findings.append(
                    self._finding(
                        profile,
                        profile.scope,
                        QualityCode.MAPPING_CONFLICT,
                        target_field=target,
                        candidate_ids=all_ids,
                    )
                )
        return findings

    @staticmethod
    def _finding(
        profile: Optional[MappingProfile],
        scope: ScopeRef,
        code: QualityCode,
        *,
        target_field: Optional[str] = None,
        rule_id: Optional[str] = None,
        candidate_ids: Tuple[UUID, ...] = (),
    ) -> QualityFinding:
        return QualityFinding(
            code=code,
            scope=scope,
            profile_id=profile.profile_id if profile else None,
            profile_version=profile.version if profile else None,
            target_field=target_field,
            rule_id=rule_id,
            candidate_ids=candidate_ids,
        )

    def _blocked_report(
        self,
        batch: MappingBatch,
        profile: Optional[MappingProfile],
        code: QualityCode,
    ) -> MappingReport:
        return self._report(
            batch=batch,
            profile=profile,
            lineages=(),
            candidates=(),
            findings=(self._finding(profile, batch.scope, code),),
        )

    @staticmethod
    def _report(
        *,
        batch: MappingBatch,
        profile: Optional[MappingProfile],
        lineages: Tuple[MappingEvidenceLineage, ...],
        candidates: Tuple[MappedCandidate, ...],
        findings: Tuple[QualityFinding, ...],
    ) -> MappingReport:
        ordered_findings = tuple(sorted(findings, key=lambda item: item.sort_key()))
        state = MappingRunState.BLOCKED_MANUAL if ordered_findings else MappingRunState.MAPPED
        run_fingerprint = _digest(
            batch.fingerprint,
            profile.fingerprint if profile else "profile_missing",
            *(candidate.fingerprint for candidate in candidates),
            *(
                item.code.value
                + ":"
                + (item.target_field or "")
                + ":"
                + ",".join(identifier.hex for identifier in item.candidate_ids)
                for item in ordered_findings
            ),
        )
        return MappingReport(
            state=state,
            scope=batch.scope,
            profile_id=profile.profile_id if profile else None,
            profile_version=profile.version if profile else None,
            profile_fingerprint=profile.fingerprint if profile else None,
            input_fingerprint=batch.fingerprint,
            input_evidence_ids=lineages,
            candidates=candidates,
            findings=ordered_findings,
            run_fingerprint=run_fingerprint,
        )


def diff_replays(previous: MappingReport, current: MappingReport) -> ProfileReplayDiff:
    """Compare two immutable replay reports without exposing values or locators."""

    if not isinstance(previous, MappingReport) or not isinstance(current, MappingReport):
        raise MappingBoundaryError("profile_replay_diff_invalid")
    if (
        previous.scope != current.scope
        or previous.profile_id is None
        or current.profile_id is None
        or previous.profile_id != current.profile_id
        or previous.profile_version is None
        or current.profile_version is None
        or previous.profile_version == current.profile_version
    ):
        raise MappingBoundaryError("profile_replay_diff_invalid")
    prior_by_key = {candidate.semantic_key: candidate for candidate in previous.candidates}
    current_by_key = {candidate.semantic_key: candidate for candidate in current.candidates}
    added = tuple(
        sorted(
            candidate.fingerprint
            for key, candidate in current_by_key.items()
            if key not in prior_by_key
        )
    )
    removed = tuple(
        sorted(
            candidate.fingerprint
            for key, candidate in prior_by_key.items()
            if key not in current_by_key
        )
    )
    changed = tuple(
        sorted(
            key
            for key in prior_by_key.keys() & current_by_key.keys()
            if prior_by_key[key].fingerprint != current_by_key[key].fingerprint
        )
    )
    return ProfileReplayDiff(
        profile_id=previous.profile_id,
        previous_version=previous.profile_version,
        current_version=current.profile_version,
        previous_run_fingerprint=previous.run_fingerprint,
        current_run_fingerprint=current.run_fingerprint,
        added_candidate_fingerprints=added,
        removed_candidate_fingerprints=removed,
        changed_candidate_keys=changed,
    )


class MappingProfileRegistry:
    """Append-only profile registry that refuses unproved version changes."""

    def __init__(self) -> None:
        self._profiles: Dict[tuple[ScopeRef, str, str], MappingProfile] = {}
        self._diffs: Dict[tuple[ScopeRef, str, str], ProfileReplayDiff] = {}

    def register(self, profile: MappingProfile) -> MappingProfile:
        if not isinstance(profile, MappingProfile):
            raise MappingBoundaryError("mapping_profile_invalid")
        key = (profile.scope, profile.profile_id, profile.version)
        current = self._profiles.get(key)
        if current is not None:
            if current.fingerprint != profile.fingerprint:
                raise MappingBoundaryError("mapping_profile_version_conflict")
            return current
        if any(
            scope == profile.scope and profile_id == profile.profile_id
            for scope, profile_id, _version in self._profiles
        ):
            raise MappingBoundaryError("profile_change_replay_required")
        self._profiles[key] = profile
        return profile

    def register_profile_change(
        self,
        profile: MappingProfile,
        previous: MappingReport,
        current: MappingReport,
        proof: ProfileReplayDiff,
    ) -> MappingProfile:
        if not isinstance(profile, MappingProfile) or not isinstance(proof, ProfileReplayDiff):
            raise MappingBoundaryError("profile_replay_diff_invalid")
        prior_key = (previous.scope, profile.profile_id, proof.previous_version)
        current_key = (profile.scope, profile.profile_id, profile.version)
        prior_profile = self._profiles.get(prior_key)
        if (
            prior_profile is None
            or proof.profile_id != profile.profile_id
            or proof.current_version != profile.version
            or previous.profile_id != profile.profile_id
            or previous.profile_version != proof.previous_version
            or current.profile_id != profile.profile_id
            or current.profile_version != profile.version
            or proof.previous_run_fingerprint != previous.run_fingerprint
            or proof.current_run_fingerprint != current.run_fingerprint
        ):
            raise MappingBoundaryError("profile_replay_diff_invalid")
        if (
            previous.scope != prior_profile.scope
            or current.scope != profile.scope
            or previous.profile_fingerprint != prior_profile.fingerprint
            or current.profile_fingerprint != profile.fingerprint
        ):
            raise MappingBoundaryError("profile_report_provenance_mismatch")
        expected = diff_replays(previous, current)
        if expected != proof:
            raise MappingBoundaryError("profile_replay_diff_invalid")
        existing = self._profiles.get(current_key)
        if existing is not None and existing.fingerprint != profile.fingerprint:
            raise MappingBoundaryError("mapping_profile_version_conflict")
        existing_proof = self._diffs.get(current_key)
        if existing_proof is not None and existing_proof != proof:
            raise MappingBoundaryError("profile_replay_diff_invalid")
        self._profiles[current_key] = existing or profile
        self._diffs[current_key] = existing_proof or proof
        return self._profiles[current_key]


__all__ = [
    "AttributeStatus",
    "MappingBatch",
    "MappingBoundaryError",
    "MappingEvidence",
    "MappingEvidenceLineage",
    "MappedCandidate",
    "MappingProfile",
    "MappingProfileRegistry",
    "MappingReport",
    "MappingRule",
    "MappingRunState",
    "NormalizationDescriptor",
    "ProfileReplayDiff",
    "QualityCode",
    "QualityFinding",
    "SyntheticMappingEngine",
    "TargetContract",
    "diff_replays",
]
