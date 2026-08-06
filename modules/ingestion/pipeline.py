"""Synthetic-only register/hash/extract/locate/staging pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from typing import Callable, Mapping, Tuple
from uuid import UUID, uuid5

from core.contracts import ScopeRef
from modules.ingestion.contracts import (
    ExtractionResultRecord,
    FailureStage,
    IngestionBoundaryError,
    IngestionFailureRecord,
    IngestionJobRecord,
    IngestionOutcome,
    IngestionOutcomeState,
    IngestionWorkflowState,
    PrivateStorageLocator,
    RegisterSourceCommand,
    SUPPORTED_MIME_TYPES,
    SourceDisposition,
    SourceFileRecord,
    SourceKind,
    StagingCandidateRecord,
    SyntheticFieldDescriptor,
    _require_aware_time,
    _require_identifier,
    _reject_sensitive_text,
)
from modules.ingestion.ports import ExtractorPort
from modules.ingestion.store import InMemoryIngestionStore


_ID_NAMESPACE = UUID("6b79c76a-ef24-4c0b-8d56-f56b58ec7d4a")
_MIME = re.compile(r"^[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*$")


def _stable_id(kind: str, *parts: object) -> UUID:
    return uuid5(_ID_NAMESPACE, "|".join((kind, *(str(part) for part in parts))))


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class IngestionPipeline:
    """Local-only pipeline that never stores input bytes or extracted values."""

    def __init__(
        self,
        *,
        store: InMemoryIngestionStore,
        extractors: Mapping[SourceKind, ExtractorPort],
        max_source_bytes: int,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(store, InMemoryIngestionStore):
            raise TypeError("ingestion_store_required")
        if not isinstance(extractors, Mapping):
            raise TypeError("extractor_registry_required")
        if (
            not isinstance(max_source_bytes, int)
            or isinstance(max_source_bytes, bool)
            or max_source_bytes < 1
        ):
            raise ValueError("max_source_bytes_required")
        self._store = store
        self._extractors = dict(extractors)
        self._max_source_bytes = max_source_bytes
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def ingest(
        self,
        command: RegisterSourceCommand,
        payload: bytes,
        fields: Tuple[SyntheticFieldDescriptor, ...],
    ) -> IngestionOutcome:
        """Run the fixed route while retaining only hashes, locators, and codes."""

        payload_fingerprint = self._payload_fingerprint(payload)
        try:
            scope, locator = self._validate_command(command)
        except IngestionBoundaryError as exc:
            return self._failure_outcome(
                state=IngestionOutcomeState.BLOCKED_MANUAL,
                scope=None,
                source_file=None,
                ingestion_job=None,
                stage=FailureStage.REGISTER,
                code=exc.code,
                input_fingerprint=payload_fingerprint,
            )

        if not isinstance(payload, bytes):
            return self._failure_outcome(
                state=IngestionOutcomeState.BLOCKED_MANUAL,
                scope=scope,
                source_file=None,
                ingestion_job=None,
                stage=FailureStage.REGISTER,
                code="source_body_required",
                input_fingerprint=payload_fingerprint,
            )
        content_sha256 = _sha256(payload)
        source_kind = SUPPORTED_MIME_TYPES.get(command.declared_mime)
        quarantine_code = None
        if len(payload) > self._max_source_bytes:
            quarantine_code = "source_oversize"
        elif not payload:
            quarantine_code = "source_empty"
        elif source_kind is None:
            quarantine_code = "unsupported_mime"

        source_file = SourceFileRecord(
            id=_stable_id(
                "source",
                scope.tenant_id,
                scope.project_id,
                scope.business_line_id,
                content_sha256,
                command.storage_locator_version,
            ),
            scope=scope,
            storage_locator=locator,
            storage_locator_version=command.storage_locator_version,
            content_sha256=content_sha256,
            size_bytes=len(payload),
            declared_mime=command.declared_mime,
            source_kind=source_kind,
            disposition=(
                SourceDisposition.QUARANTINED
                if quarantine_code is not None
                else SourceDisposition.REGISTERED
            ),
            quarantine_code=quarantine_code,
            received_at=command.received_at,
            received_by=command.received_by,
        )
        try:
            source_file = self._store.register_source(source_file)
        except IngestionBoundaryError as exc:
            return self._failure_outcome(
                state=IngestionOutcomeState.BLOCKED_MANUAL,
                scope=scope,
                source_file=None,
                ingestion_job=None,
                stage=FailureStage.REGISTER,
                code=exc.code,
                input_fingerprint=content_sha256,
            )
        if quarantine_code is not None or source_file.disposition is SourceDisposition.QUARANTINED:
            code = source_file.quarantine_code or "source_quarantined"
            return self._failure_outcome(
                state=IngestionOutcomeState.QUARANTINED,
                scope=scope,
                source_file=source_file,
                ingestion_job=None,
                stage=FailureStage.CLASSIFY,
                code=code,
                input_fingerprint=content_sha256,
            )
        if source_file.source_kind is None:
            return self._failure_outcome(
                state=IngestionOutcomeState.QUARANTINED,
                scope=scope,
                source_file=source_file,
                ingestion_job=None,
                stage=FailureStage.CLASSIFY,
                code="unsupported_mime",
                input_fingerprint=content_sha256,
            )

        extractor = self._extractors.get(source_file.source_kind)
        if extractor is None:
            return self._failure_outcome(
                state=IngestionOutcomeState.BLOCKED_MANUAL,
                scope=scope,
                source_file=source_file,
                ingestion_job=None,
                stage=FailureStage.EXTRACT,
                code="extractor_unavailable",
                input_fingerprint=content_sha256,
            )
        if (
            getattr(extractor, "source_kind", None) is not source_file.source_kind
            or not isinstance(getattr(extractor, "extractor_version", None), str)
        ):
            return self._failure_outcome(
                state=IngestionOutcomeState.BLOCKED_MANUAL,
                scope=scope,
                source_file=source_file,
                ingestion_job=None,
                stage=FailureStage.EXTRACT,
                code="extractor_contract_invalid",
                input_fingerprint=content_sha256,
            )
        try:
            field_tuple = self._validate_field_container(fields)
            _require_identifier(extractor.extractor_version, "extractor_version_required")
            input_signature = self._field_signature(
                field_tuple,
                extractor.extractor_version,
            )
            ingestion_job = IngestionJobRecord(
                id=_stable_id(
                    "job",
                    source_file.id,
                    command.parser_version,
                    command.mapping_profile_version,
                ),
                scope=scope,
                source_file_id=source_file.id,
                parser_version=command.parser_version,
                extractor_version=extractor.extractor_version,
                mapping_profile_version=command.mapping_profile_version,
                input_signature=input_signature,
                idempotency_key=command.idempotency_key,
                workflow_state=IngestionWorkflowState.REGISTERED,
            )
            ingestion_job = self._store.register_job(ingestion_job)
        except IngestionBoundaryError as exc:
            return self._failure_outcome(
                state=IngestionOutcomeState.BLOCKED_MANUAL,
                scope=scope,
                source_file=source_file,
                ingestion_job=None,
                stage=FailureStage.EXTRACT,
                code=exc.code,
                input_fingerprint=content_sha256,
            )

        try:
            extracted = extractor.extract(source_file, field_tuple)
            extracted = self._validate_field_container(extracted)
            if extracted != field_tuple:
                raise IngestionBoundaryError("extraction_output_mismatch")
        except IngestionBoundaryError as exc:
            return self._failure_outcome(
                state=IngestionOutcomeState.BLOCKED_MANUAL,
                scope=scope,
                source_file=source_file,
                ingestion_job=ingestion_job,
                stage=FailureStage.EXTRACT,
                code=exc.code,
                input_fingerprint=content_sha256,
            )

        pending_results: list[ExtractionResultRecord] = []
        pending_candidates: list[StagingCandidateRecord] = []
        try:
            for field in extracted:
                if field.locator is None:
                    raise IngestionBoundaryError("field_locator_required")
                field.locator.validate_for(source_file.source_kind)
                result = ExtractionResultRecord(
                    id=_stable_id(
                        "result",
                        ingestion_job.id,
                        extractor.extractor_version,
                        field.field_name,
                        field.value_hash,
                        field.locator.stable_token(),
                    ),
                    scope=scope,
                    source_file_id=source_file.id,
                    ingestion_job_id=ingestion_job.id,
                    extractor_version=extractor.extractor_version,
                    field_name=field.field_name,
                    content_hash=field.value_hash,
                    locator=field.locator,
                    confidence_basis=field.confidence_basis,
                )
                candidate = StagingCandidateRecord(
                    id=_stable_id("candidate", ingestion_job.id, result.id),
                    scope=scope,
                    source_file_id=source_file.id,
                    ingestion_job_id=ingestion_job.id,
                    extraction_result_id=result.id,
                    field_name=result.field_name,
                    content_hash=result.content_hash,
                    locator=result.locator,
                )
                pending_results.append(result)
                pending_candidates.append(candidate)
        except IngestionBoundaryError as exc:
            return self._failure_outcome(
                state=IngestionOutcomeState.BLOCKED_MANUAL,
                scope=scope,
                source_file=source_file,
                ingestion_job=ingestion_job,
                stage=FailureStage.LOCATE,
                code=exc.code,
                input_fingerprint=content_sha256,
            )

        try:
            results, candidates = self._store.append_staging_batch(
                tuple(pending_results),
                tuple(pending_candidates),
            )
        except IngestionBoundaryError as exc:
            return self._failure_outcome(
                state=IngestionOutcomeState.BLOCKED_MANUAL,
                scope=scope,
                source_file=source_file,
                ingestion_job=ingestion_job,
                stage=FailureStage.STAGING,
                code=exc.code,
                input_fingerprint=content_sha256,
            )

        ingestion_job = self._store.set_job_state(
            ingestion_job,
            IngestionWorkflowState.STAGED,
        )
        return IngestionOutcome(
            state=IngestionOutcomeState.STAGED,
            source_file=source_file,
            ingestion_job=ingestion_job,
            extraction_results=results,
            staging_candidates=candidates,
        )

    def _validate_command(
        self,
        command: object,
    ) -> tuple[ScopeRef, PrivateStorageLocator]:
        if not isinstance(command, RegisterSourceCommand):
            raise IngestionBoundaryError("register_source_command_required")
        if not isinstance(command.scope, ScopeRef):
            raise IngestionBoundaryError("scope_required")
        _reject_sensitive_text(command.scope.correlation_id)
        if command.is_synthetic is not True:
            raise IngestionBoundaryError("synthetic_input_required")
        if command.external_execution_allowed is not False:
            raise IngestionBoundaryError("external_execution_forbidden")
        if command.business_external_ready is not False:
            raise IngestionBoundaryError("business_external_ready_forbidden")
        locator = PrivateStorageLocator.parse(command.storage_locator)
        _require_identifier(command.storage_locator_version, "storage_locator_version_required")
        _reject_sensitive_text(command.storage_locator_version)
        if (
            not isinstance(command.declared_mime, str)
            or len(command.declared_mime) > 127
            or _MIME.fullmatch(command.declared_mime) is None
        ):
            raise IngestionBoundaryError("unsupported_mime")
        _reject_sensitive_text(command.declared_mime)
        _require_identifier(command.parser_version, "parser_version_required")
        _reject_sensitive_text(command.parser_version)
        _require_identifier(command.mapping_profile_version, "mapping_profile_version_required")
        _reject_sensitive_text(command.mapping_profile_version)
        _require_aware_time(command.received_at, "received_at_required")
        _require_identifier(command.received_by, "received_by_required")
        _reject_sensitive_text(command.received_by)
        _require_identifier(command.idempotency_key, "idempotency_key_required")
        _reject_sensitive_text(command.idempotency_key)
        return command.scope, locator

    @staticmethod
    def _payload_fingerprint(payload: object) -> str:
        if isinstance(payload, bytes):
            return _sha256(payload)
        return _sha256(type(payload).__name__.encode("ascii", errors="ignore"))

    @staticmethod
    def _validate_field_container(
        fields: object,
    ) -> Tuple[SyntheticFieldDescriptor, ...]:
        if not isinstance(fields, tuple):
            raise IngestionBoundaryError("synthetic_fields_required")
        if not fields:
            raise IngestionBoundaryError("synthetic_fields_required")
        if any(not isinstance(field, SyntheticFieldDescriptor) for field in fields):
            raise IngestionBoundaryError("synthetic_field_invalid")
        names = tuple(field.field_name for field in fields)
        if len(set(names)) != len(names):
            raise IngestionBoundaryError("duplicate_field_name")
        return fields

    @staticmethod
    def _field_signature(
        fields: Tuple[SyntheticFieldDescriptor, ...],
        extractor_version: str,
    ) -> str:
        digest = hashlib.sha256()
        digest.update(extractor_version.encode("utf-8"))
        for field in fields:
            digest.update(field.field_name.encode("utf-8"))
            digest.update(field.value_hash.encode("ascii"))
            locator_token = "missing" if field.locator is None else field.locator.stable_token()
            digest.update(locator_token.encode("utf-8"))
            digest.update(field.confidence_basis.encode("utf-8"))
        return digest.hexdigest()

    def _failure_outcome(
        self,
        *,
        state: IngestionOutcomeState,
        scope: ScopeRef | None,
        source_file: SourceFileRecord | None,
        ingestion_job: IngestionJobRecord | None,
        stage: FailureStage,
        code: str,
        input_fingerprint: str,
    ) -> IngestionOutcome:
        if ingestion_job is not None:
            ingestion_job = self._store.set_job_state(
                ingestion_job,
                IngestionWorkflowState.BLOCKED_MANUAL,
                code,
            )
        failure = IngestionFailureRecord(
            id=_stable_id(
                "failure",
                scope.tenant_id if scope else "unscoped",
                scope.project_id if scope else "unscoped",
                scope.business_line_id if scope else "unscoped",
                source_file.id if source_file else "no_source",
                ingestion_job.id if ingestion_job else "no_job",
                stage.value,
                code,
                input_fingerprint,
            ),
            scope=scope,
            source_file_id=source_file.id if source_file else None,
            ingestion_job_id=ingestion_job.id if ingestion_job else None,
            stage=stage,
            error_code=code,
            error=IngestionBoundaryError(code),
            input_fingerprint=input_fingerprint,
            recorded_at=self._clock(),
        )
        failure = self._store.record_failure(failure)
        return IngestionOutcome(
            state=state,
            source_file=source_file,
            ingestion_job=ingestion_job,
            failure=failure,
        )


__all__ = ["IngestionPipeline"]
