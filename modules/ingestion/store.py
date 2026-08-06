"""Append-only in-memory stores for P03-01 contract probes."""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, Tuple
from uuid import UUID

from core.contracts import ScopeRef
from modules.ingestion.contracts import (
    ExtractionResultRecord,
    IngestionBoundaryError,
    IngestionFailureRecord,
    IngestionJobRecord,
    IngestionWorkflowState,
    SourceFileRecord,
    StagingCandidateRecord,
)


class InMemoryIngestionStore:
    """Local evidence store with no body, update/delete, database, or I/O surface."""

    def __init__(self) -> None:
        self.__sources: Dict[UUID, SourceFileRecord] = {}
        self.__source_keys: Dict[tuple[object, ...], UUID] = {}
        self.__jobs: Dict[UUID, IngestionJobRecord] = {}
        self.__job_keys: Dict[tuple[object, ...], UUID] = {}
        self.__results: Dict[UUID, ExtractionResultRecord] = {}
        self.__candidates: Dict[UUID, StagingCandidateRecord] = {}
        self.__failures: Dict[UUID, IngestionFailureRecord] = {}

    @property
    def source_files(self) -> Tuple[SourceFileRecord, ...]:
        return tuple(self.__sources.values())

    @property
    def ingestion_jobs(self) -> Tuple[IngestionJobRecord, ...]:
        return tuple(self.__jobs.values())

    @property
    def extraction_results(self) -> Tuple[ExtractionResultRecord, ...]:
        return tuple(self.__results.values())

    @property
    def staging_candidates(self) -> Tuple[StagingCandidateRecord, ...]:
        return tuple(self.__candidates.values())

    @property
    def failures(self) -> Tuple[IngestionFailureRecord, ...]:
        return tuple(self.__failures.values())

    @property
    def records(self) -> tuple[object, ...]:
        return (
            *self.source_files,
            *self.ingestion_jobs,
            *self.extraction_results,
            *self.staging_candidates,
            *self.failures,
        )

    def register_source(self, record: SourceFileRecord) -> SourceFileRecord:
        key = (
            record.scope.tenant_id,
            record.scope.project_id,
            record.scope.business_line_id,
            record.content_sha256,
            record.storage_locator_version,
        )
        existing_id = self.__source_keys.get(key)
        if existing_id is not None:
            existing = self.__sources[existing_id]
            if (
                existing.declared_mime != record.declared_mime
                or existing.source_kind != record.source_kind
                or existing.size_bytes != record.size_bytes
            ):
                raise IngestionBoundaryError("source_registration_conflict")
            return existing
        self.__sources[record.id] = record
        self.__source_keys[key] = record.id
        return record

    def get_source(self, scope: ScopeRef, source_file_id: UUID) -> SourceFileRecord:
        record = self.__sources.get(source_file_id)
        if record is None:
            raise IngestionBoundaryError("source_file_not_found")
        if record.scope != scope:
            raise IngestionBoundaryError("cross_scope_forbidden")
        return record

    def register_job(self, record: IngestionJobRecord) -> IngestionJobRecord:
        source = self.__sources.get(record.source_file_id)
        if source is None:
            raise IngestionBoundaryError("source_file_not_found")
        if source.scope != record.scope:
            raise IngestionBoundaryError("cross_scope_forbidden")
        key = (
            record.scope.tenant_id,
            record.scope.project_id,
            record.scope.business_line_id,
            record.source_file_id,
            record.parser_version,
            record.mapping_profile_version,
        )
        existing_id = self.__job_keys.get(key)
        if existing_id is not None:
            existing = self.__jobs[existing_id]
            if existing.input_signature != record.input_signature:
                raise IngestionBoundaryError("extraction_replay_mismatch")
            return existing
        self.__jobs[record.id] = record
        self.__job_keys[key] = record.id
        return record

    def set_job_state(
        self,
        record: IngestionJobRecord,
        state: IngestionWorkflowState,
        error_code: str | None = None,
    ) -> IngestionJobRecord:
        current = self.__jobs.get(record.id)
        if current is None or current.scope != record.scope:
            raise IngestionBoundaryError("ingestion_job_not_found")
        updated = replace(current, workflow_state=state, error_code=error_code)
        self.__jobs[record.id] = updated
        return updated

    def append_result(self, record: ExtractionResultRecord) -> ExtractionResultRecord:
        results, _ = self.append_staging_batch((record,), ())
        return results[0]

    def append_candidate(self, record: StagingCandidateRecord) -> StagingCandidateRecord:
        _, candidates = self.append_staging_batch((), (record,))
        return candidates[0]

    def append_staging_batch(
        self,
        results: Tuple[ExtractionResultRecord, ...],
        candidates: Tuple[StagingCandidateRecord, ...],
    ) -> tuple[Tuple[ExtractionResultRecord, ...], Tuple[StagingCandidateRecord, ...]]:
        """Validate a whole extraction batch before making any record visible."""

        if not isinstance(results, tuple) or not isinstance(candidates, tuple):
            raise IngestionBoundaryError("staging_batch_required")
        next_results = dict(self.__results)
        next_candidates = dict(self.__candidates)
        stored_results: list[ExtractionResultRecord] = []
        stored_candidates: list[StagingCandidateRecord] = []
        for record in results:
            if not isinstance(record, ExtractionResultRecord):
                raise IngestionBoundaryError("extraction_result_required")
            self._assert_result_lineage(record)
            existing = next_results.get(record.id)
            if existing is not None and existing != record:
                raise IngestionBoundaryError("extraction_result_conflict")
            selected = existing or record
            next_results[record.id] = selected
            stored_results.append(selected)
        for record in candidates:
            if not isinstance(record, StagingCandidateRecord):
                raise IngestionBoundaryError("staging_candidate_required")
            self._assert_candidate_lineage(record, next_results)
            existing = next_candidates.get(record.id)
            if existing is not None and existing != record:
                raise IngestionBoundaryError("staging_candidate_conflict")
            selected = existing or record
            next_candidates[record.id] = selected
            stored_candidates.append(selected)
        self.__results = next_results
        self.__candidates = next_candidates
        return tuple(stored_results), tuple(stored_candidates)

    def _assert_result_lineage(self, record: ExtractionResultRecord) -> None:
        source = self.__sources.get(record.source_file_id)
        job = self.__jobs.get(record.ingestion_job_id)
        if source is None:
            raise IngestionBoundaryError("source_file_not_found")
        if job is None:
            raise IngestionBoundaryError("ingestion_job_not_found")
        if source.scope != record.scope or job.scope != record.scope:
            raise IngestionBoundaryError("cross_scope_forbidden")
        if job.source_file_id != source.id:
            raise IngestionBoundaryError("ingestion_source_lineage_mismatch")
        if record.extractor_version != job.extractor_version:
            raise IngestionBoundaryError("extractor_version_mismatch")

    def _assert_candidate_lineage(
        self,
        record: StagingCandidateRecord,
        available_results: Dict[UUID, ExtractionResultRecord],
    ) -> None:
        source = self.__sources.get(record.source_file_id)
        job = self.__jobs.get(record.ingestion_job_id)
        result = available_results.get(record.extraction_result_id)
        if source is None:
            raise IngestionBoundaryError("source_file_not_found")
        if job is None:
            raise IngestionBoundaryError("ingestion_job_not_found")
        if result is None:
            raise IngestionBoundaryError("extraction_result_not_found")
        if (
            source.scope != record.scope
            or job.scope != record.scope
            or result.scope != record.scope
        ):
            raise IngestionBoundaryError("cross_scope_forbidden")
        if (
            job.source_file_id != source.id
            or result.source_file_id != source.id
            or result.ingestion_job_id != job.id
        ):
            raise IngestionBoundaryError("staging_lineage_mismatch")
        if (
            record.field_name != result.field_name
            or record.content_hash != result.content_hash
            or record.locator != result.locator
        ):
            raise IngestionBoundaryError("staging_result_mismatch")

    def record_failure(self, record: IngestionFailureRecord) -> IngestionFailureRecord:
        existing = self.__failures.get(record.id)
        if existing is not None:
            return existing
        self.__failures[record.id] = record
        return self.__failures[record.id]


__all__ = ["InMemoryIngestionStore"]
