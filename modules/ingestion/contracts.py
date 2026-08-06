"""Value-free contracts for synthetic source registration and staging."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import PurePosixPath
import re
from typing import Optional, Tuple
from uuid import UUID

from core.contracts import ContractValidationError, DataState, ScopeRef, Sensitivity


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_PATH_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_PRIVATE_REFERENCE = re.compile(r"^ref:private:[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MIME = re.compile(r"^[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*$")
_SENSITIVE_METADATA = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)


class IngestionBoundaryError(ContractValidationError):
    """Fail-closed error whose string representation is only a stable code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class SourceKind(str, Enum):
    XLSX = "xlsx"
    CSV = "csv"
    DOCX = "docx"
    PDF = "pdf"
    IMAGE = "image"
    FOLDER = "folder"
    JSON_EXPORT = "json_export"


class SourceDisposition(str, Enum):
    REGISTERED = "registered"
    QUARANTINED = "quarantined"


class IngestionWorkflowState(str, Enum):
    REGISTERED = "registered"
    STAGED = "staged"
    BLOCKED_MANUAL = "blocked_manual"


class IngestionOutcomeState(str, Enum):
    STAGED = "staged"
    QUARANTINED = "quarantined"
    BLOCKED_MANUAL = "blocked_manual"


class FailureStage(str, Enum):
    REGISTER = "register"
    CLASSIFY = "classify"
    EXTRACT = "extract"
    LOCATE = "locate"
    STAGING = "staging"


SUPPORTED_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": SourceKind.XLSX,
    "text/csv": SourceKind.CSV,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": SourceKind.DOCX,
    "application/pdf": SourceKind.PDF,
    "image/png": SourceKind.IMAGE,
    "image/jpeg": SourceKind.IMAGE,
    "application/x.synthetic-folder-manifest": SourceKind.FOLDER,
    "application/json": SourceKind.JSON_EXPORT,
}


def _require_identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise IngestionBoundaryError(code)
    return value


def _require_hash(value: object, code: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise IngestionBoundaryError(code)
    return value


def _require_aware_time(value: object, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise IngestionBoundaryError(code)
    return value


def _reject_sensitive_text(value: object) -> None:
    if isinstance(value, str) and _SENSITIVE_METADATA.search(value) is not None:
        raise IngestionBoundaryError("sensitive_metadata_forbidden")


def _require_uuid(value: object, code: str) -> UUID:
    if not isinstance(value, UUID) or value.int == 0:
        raise IngestionBoundaryError(code)
    return value


def _require_internal_fixture(
    data_state: object,
    is_synthetic: object,
    external_execution_allowed: object,
    business_external_ready: object,
) -> None:
    if data_state is not DataState.FIXTURE:
        raise IngestionBoundaryError("fixture_data_state_required")
    if is_synthetic is not True:
        raise IngestionBoundaryError("synthetic_input_required")
    if external_execution_allowed is not False:
        raise IngestionBoundaryError("external_execution_forbidden")
    if business_external_ready is not False:
        raise IngestionBoundaryError("business_external_ready_forbidden")


def _validate_relative_path(value: object, *, private_root: bool, code: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 255:
        raise IngestionBoundaryError(code)
    if value.startswith("/") or "\\" in value or ":" in value:
        raise IngestionBoundaryError(code)
    path = PurePosixPath(value)
    parts = path.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise IngestionBoundaryError(code)
    if private_root and parts[0] != "private":
        raise IngestionBoundaryError(code)
    if any(_PATH_SEGMENT.fullmatch(part) is None for part in parts):
        raise IngestionBoundaryError(code)
    normalized = path.as_posix()
    if normalized != value:
        raise IngestionBoundaryError(code)
    return normalized


@dataclass(frozen=True)
class PrivateStorageLocator:
    """A private relative path or opaque private reference; never an absolute path."""

    value: str
    is_reference: bool

    def __post_init__(self) -> None:
        if not isinstance(self.is_reference, bool):
            raise IngestionBoundaryError("storage_locator_unsafe")
        if self.is_reference:
            if not isinstance(self.value, str) or _PRIVATE_REFERENCE.fullmatch(self.value) is None:
                raise IngestionBoundaryError("storage_locator_unsafe")
        else:
            _validate_relative_path(
                self.value,
                private_root=True,
                code="storage_locator_unsafe",
            )
        _reject_sensitive_text(self.value)

    @classmethod
    def parse(cls, value: object) -> "PrivateStorageLocator":
        if isinstance(value, str) and _PRIVATE_REFERENCE.fullmatch(value) is not None:
            return cls(value=value, is_reference=True)
        return cls(
            value=_validate_relative_path(
                value,
                private_root=True,
                code="storage_locator_unsafe",
            ),
            is_reference=False,
        )


@dataclass(frozen=True)
class FieldLocator:
    """Traceable source location without extracted body text."""

    page: Optional[int] = None
    sheet: Optional[str] = None
    row: Optional[int] = None
    cell: Optional[str] = None
    bbox: Optional[Tuple[int, int, int, int]] = None
    export_record: Optional[str] = None
    member_relative_path: Optional[str] = None

    def __post_init__(self) -> None:
        for value in (
            self.sheet,
            self.cell,
            self.export_record,
            self.member_relative_path,
        ):
            _reject_sensitive_text(value)

    @property
    def has_traceable_location(self) -> bool:
        return any(
            value is not None
            for value in (
                self.page,
                self.sheet,
                self.row,
                self.cell,
                self.bbox,
                self.export_record,
                self.member_relative_path,
            )
        )

    def validate_for(self, source_kind: SourceKind) -> None:
        if not isinstance(source_kind, SourceKind):
            raise IngestionBoundaryError("source_kind_required")
        if source_kind is SourceKind.XLSX:
            self._require_sheet_row_cell()
        elif source_kind is SourceKind.CSV:
            self._require_row_cell()
        elif source_kind in {SourceKind.DOCX, SourceKind.PDF, SourceKind.IMAGE}:
            self._require_page_bbox()
        elif source_kind is SourceKind.FOLDER:
            _validate_relative_path(
                self.member_relative_path,
                private_root=False,
                code="field_locator_invalid",
            )
            _require_identifier(self.export_record, "field_locator_invalid")
        elif source_kind is SourceKind.JSON_EXPORT:
            _require_identifier(self.export_record, "field_locator_invalid")
        else:
            raise IngestionBoundaryError("source_kind_required")
        for value in (
            self.sheet,
            self.cell,
            self.export_record,
            self.member_relative_path,
        ):
            _reject_sensitive_text(value)

    def stable_token(self) -> str:
        values = (
            self.page,
            self.sheet,
            self.row,
            self.cell,
            self.bbox,
            self.export_record,
            self.member_relative_path,
        )
        return "|".join("-" if value is None else repr(value) for value in values)

    def _require_sheet_row_cell(self) -> None:
        _require_identifier(self.sheet, "field_locator_invalid")
        self._require_row_cell()

    def _require_row_cell(self) -> None:
        if not isinstance(self.row, int) or isinstance(self.row, bool) or self.row < 1:
            raise IngestionBoundaryError("field_locator_invalid")
        _require_identifier(self.cell, "field_locator_invalid")

    def _require_page_bbox(self) -> None:
        if not isinstance(self.page, int) or isinstance(self.page, bool) or self.page < 1:
            raise IngestionBoundaryError("field_locator_invalid")
        if (
            not isinstance(self.bbox, tuple)
            or len(self.bbox) != 4
            or any(not isinstance(item, int) or isinstance(item, bool) for item in self.bbox)
            or any(item < 0 for item in self.bbox)
            or self.bbox[2] <= self.bbox[0]
            or self.bbox[3] <= self.bbox[1]
        ):
            raise IngestionBoundaryError("field_locator_invalid")


@dataclass(frozen=True)
class RegisterSourceCommand:
    """Synthetic-only registration envelope; raw bytes remain ephemeral."""

    scope: object
    storage_locator: object
    storage_locator_version: object
    declared_mime: object
    parser_version: object
    mapping_profile_version: object
    received_at: object
    received_by: object
    idempotency_key: object
    is_synthetic: object
    external_execution_allowed: object
    business_external_ready: object


@dataclass(frozen=True)
class SyntheticFieldDescriptor:
    """Value-free fake extraction descriptor used only by contract probes."""

    field_name: str
    value_hash: str
    locator: Optional[FieldLocator]
    confidence_basis: str

    def __post_init__(self) -> None:
        _require_identifier(self.field_name, "field_name_required")
        _reject_sensitive_text(self.field_name)
        _require_hash(self.value_hash, "field_value_hash_required")
        if self.locator is not None and not isinstance(self.locator, FieldLocator):
            raise IngestionBoundaryError("field_locator_invalid")
        _require_identifier(self.confidence_basis, "confidence_basis_required")
        _reject_sensitive_text(self.confidence_basis)


@dataclass(frozen=True)
class SourceFileRecord:
    id: UUID
    scope: ScopeRef
    storage_locator: PrivateStorageLocator
    storage_locator_version: str
    content_sha256: str
    size_bytes: int
    declared_mime: str
    source_kind: Optional[SourceKind]
    disposition: SourceDisposition
    quarantine_code: Optional[str]
    received_at: datetime
    received_by: str
    data_state: DataState = DataState.FIXTURE
    sensitivity: Sensitivity = Sensitivity.CONFIDENTIAL
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "source_file_id_required")
        if not isinstance(self.scope, ScopeRef):
            raise IngestionBoundaryError("scope_required")
        _reject_sensitive_text(self.scope.correlation_id)
        if not isinstance(self.storage_locator, PrivateStorageLocator):
            raise IngestionBoundaryError("storage_locator_unsafe")
        _require_identifier(
            self.storage_locator_version,
            "storage_locator_version_required",
        )
        _reject_sensitive_text(self.storage_locator_version)
        _require_hash(self.content_sha256, "source_hash_required")
        if not isinstance(self.size_bytes, int) or isinstance(self.size_bytes, bool) or self.size_bytes < 0:
            raise IngestionBoundaryError("source_size_invalid")
        if not isinstance(self.declared_mime, str) or _MIME.fullmatch(self.declared_mime) is None:
            raise IngestionBoundaryError("declared_mime_required")
        _reject_sensitive_text(self.declared_mime)
        if self.source_kind is not None and not isinstance(self.source_kind, SourceKind):
            raise IngestionBoundaryError("source_kind_required")
        if SUPPORTED_MIME_TYPES.get(self.declared_mime) is not self.source_kind:
            raise IngestionBoundaryError("source_kind_mime_mismatch")
        if not isinstance(self.disposition, SourceDisposition):
            raise IngestionBoundaryError("source_disposition_required")
        if self.disposition is SourceDisposition.REGISTERED:
            if self.source_kind is None or self.quarantine_code is not None:
                raise IngestionBoundaryError("source_disposition_invalid")
        else:
            _require_identifier(self.quarantine_code, "quarantine_code_required")
        _require_aware_time(self.received_at, "received_at_required")
        _require_identifier(self.received_by, "received_by_required")
        _reject_sensitive_text(self.received_by)
        if self.sensitivity is not Sensitivity.CONFIDENTIAL:
            raise IngestionBoundaryError("source_sensitivity_invalid")
        _require_internal_fixture(
            self.data_state,
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )


@dataclass(frozen=True)
class IngestionJobRecord:
    id: UUID
    scope: ScopeRef
    source_file_id: UUID
    parser_version: str
    extractor_version: str
    mapping_profile_version: str
    input_signature: str
    idempotency_key: str
    workflow_state: IngestionWorkflowState
    error_code: Optional[str] = None
    data_state: DataState = DataState.FIXTURE
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "ingestion_job_id_required")
        if not isinstance(self.scope, ScopeRef):
            raise IngestionBoundaryError("scope_required")
        _reject_sensitive_text(self.scope.correlation_id)
        _require_uuid(self.source_file_id, "source_file_id_required")
        _require_identifier(self.parser_version, "parser_version_required")
        _reject_sensitive_text(self.parser_version)
        _require_identifier(self.extractor_version, "extractor_version_required")
        _reject_sensitive_text(self.extractor_version)
        _require_identifier(
            self.mapping_profile_version,
            "mapping_profile_version_required",
        )
        _reject_sensitive_text(self.mapping_profile_version)
        _require_hash(self.input_signature, "ingestion_input_signature_required")
        _require_identifier(self.idempotency_key, "idempotency_key_required")
        _reject_sensitive_text(self.idempotency_key)
        if not isinstance(self.workflow_state, IngestionWorkflowState):
            raise IngestionBoundaryError("ingestion_workflow_state_required")
        if self.error_code is not None:
            _require_identifier(self.error_code, "ingestion_error_code_invalid")
        if (
            self.workflow_state is IngestionWorkflowState.BLOCKED_MANUAL
        ) is (self.error_code is None):
            raise IngestionBoundaryError("ingestion_error_state_mismatch")
        _require_internal_fixture(
            self.data_state,
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )


@dataclass(frozen=True)
class ExtractionResultRecord:
    id: UUID
    scope: ScopeRef
    source_file_id: UUID
    ingestion_job_id: UUID
    extractor_version: str
    field_name: str
    content_hash: str
    locator: FieldLocator
    confidence_basis: str
    data_state: DataState = DataState.FIXTURE
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "extraction_result_id_required")
        if not isinstance(self.scope, ScopeRef):
            raise IngestionBoundaryError("scope_required")
        _reject_sensitive_text(self.scope.correlation_id)
        _require_uuid(self.source_file_id, "source_file_id_required")
        _require_uuid(self.ingestion_job_id, "ingestion_job_id_required")
        _require_identifier(self.extractor_version, "extractor_version_required")
        _reject_sensitive_text(self.extractor_version)
        _require_identifier(self.field_name, "field_name_required")
        _reject_sensitive_text(self.field_name)
        _require_hash(self.content_hash, "extraction_content_hash_required")
        if not isinstance(self.locator, FieldLocator) or not self.locator.has_traceable_location:
            raise IngestionBoundaryError("field_locator_required")
        _require_identifier(self.confidence_basis, "confidence_basis_required")
        _reject_sensitive_text(self.confidence_basis)
        _require_internal_fixture(
            self.data_state,
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )


@dataclass(frozen=True)
class StagingCandidateRecord:
    id: UUID
    scope: ScopeRef
    source_file_id: UUID
    ingestion_job_id: UUID
    extraction_result_id: UUID
    field_name: str
    content_hash: str
    locator: FieldLocator
    workflow_state: IngestionWorkflowState = IngestionWorkflowState.STAGED
    data_state: DataState = DataState.FIXTURE
    is_synthetic: bool = True
    external_execution_allowed: bool = False
    business_external_ready: bool = False

    def __post_init__(self) -> None:
        _require_uuid(self.id, "staging_candidate_id_required")
        if not isinstance(self.scope, ScopeRef):
            raise IngestionBoundaryError("scope_required")
        _reject_sensitive_text(self.scope.correlation_id)
        _require_uuid(self.source_file_id, "source_file_id_required")
        _require_uuid(self.ingestion_job_id, "ingestion_job_id_required")
        _require_uuid(self.extraction_result_id, "extraction_result_id_required")
        _require_identifier(self.field_name, "field_name_required")
        _reject_sensitive_text(self.field_name)
        _require_hash(self.content_hash, "staging_content_hash_required")
        if not isinstance(self.locator, FieldLocator) or not self.locator.has_traceable_location:
            raise IngestionBoundaryError("field_locator_required")
        if self.workflow_state is not IngestionWorkflowState.STAGED:
            raise IngestionBoundaryError("staging_workflow_state_required")
        _require_internal_fixture(
            self.data_state,
            self.is_synthetic,
            self.external_execution_allowed,
            self.business_external_ready,
        )


@dataclass(frozen=True)
class IngestionFailureRecord:
    id: UUID
    scope: Optional[ScopeRef]
    source_file_id: Optional[UUID]
    ingestion_job_id: Optional[UUID]
    stage: FailureStage
    error_code: str
    error: IngestionBoundaryError
    input_fingerprint: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        _require_uuid(self.id, "failure_record_id_required")
        if self.scope is not None and not isinstance(self.scope, ScopeRef):
            raise IngestionBoundaryError("scope_required")
        if self.scope is not None:
            _reject_sensitive_text(self.scope.correlation_id)
        if self.source_file_id is not None:
            _require_uuid(self.source_file_id, "source_file_id_required")
        if self.ingestion_job_id is not None:
            _require_uuid(self.ingestion_job_id, "ingestion_job_id_required")
        if not isinstance(self.stage, FailureStage):
            raise IngestionBoundaryError("failure_stage_required")
        _require_identifier(self.error_code, "ingestion_error_code_invalid")
        if not isinstance(self.error, IngestionBoundaryError) or self.error.code != self.error_code:
            raise IngestionBoundaryError("failure_error_mismatch")
        _require_hash(self.input_fingerprint, "failure_input_fingerprint_required")
        _require_aware_time(self.recorded_at, "failure_recorded_at_required")


@dataclass(frozen=True)
class IngestionOutcome:
    state: IngestionOutcomeState
    source_file: Optional[SourceFileRecord] = None
    ingestion_job: Optional[IngestionJobRecord] = None
    extraction_results: Tuple[ExtractionResultRecord, ...] = ()
    staging_candidates: Tuple[StagingCandidateRecord, ...] = ()
    failure: Optional[IngestionFailureRecord] = None

    def __post_init__(self) -> None:
        if not isinstance(self.state, IngestionOutcomeState):
            raise IngestionBoundaryError("ingestion_outcome_state_required")
        if self.state is IngestionOutcomeState.STAGED:
            if (
                self.source_file is None
                or self.ingestion_job is None
                or self.ingestion_job.workflow_state is not IngestionWorkflowState.STAGED
                or self.failure is not None
                or not self.extraction_results
                or not self.staging_candidates
            ):
                raise IngestionBoundaryError("staged_outcome_invalid")
        elif (
            self.failure is None
            or self.extraction_results
            or self.staging_candidates
        ):
            raise IngestionBoundaryError("blocked_outcome_invalid")

    def safe_summary(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "source_file_id": str(self.source_file.id) if self.source_file else None,
            "ingestion_job_id": str(self.ingestion_job.id) if self.ingestion_job else None,
            "extraction_count": len(self.extraction_results),
            "staging_count": len(self.staging_candidates),
            "error_code": self.failure.error_code if self.failure else None,
            "external_execution_allowed": False,
            "business_external_ready": False,
        }


__all__ = [
    "FailureStage",
    "FieldLocator",
    "IngestionBoundaryError",
    "IngestionFailureRecord",
    "IngestionJobRecord",
    "IngestionOutcome",
    "IngestionOutcomeState",
    "IngestionWorkflowState",
    "PrivateStorageLocator",
    "RegisterSourceCommand",
    "SUPPORTED_MIME_TYPES",
    "SourceDisposition",
    "SourceFileRecord",
    "SourceKind",
    "StagingCandidateRecord",
    "SyntheticFieldDescriptor",
    "ExtractionResultRecord",
    "_require_aware_time",
    "_require_hash",
    "_require_identifier",
    "_reject_sensitive_text",
]
