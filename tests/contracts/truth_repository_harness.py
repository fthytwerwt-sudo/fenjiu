"""Test-only observation harness for P02-02 repository contract probes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from core.contracts import ContractValidationError, ScopeRef
from core.contracts.scope import _require_identifier, _require_uuid
from modules.truth_center import InMemoryTruthRepository, TruthEntityKind, TruthVersion
from modules.truth_center.models import is_current_readable_state


class TruthRepositoryContractHarness:
    """Mirror synthetic appends for tests without widening the runtime API."""

    def __init__(self) -> None:
        self.repository = InMemoryTruthRepository()
        self.__records: tuple[TruthVersion, ...] = ()

    def append(self, record: TruthVersion) -> None:
        self.repository.append(record)
        self.__records = (*self.__records, record)

    def probe_get_by_id(
        self,
        scope: ScopeRef,
        version_id: UUID,
    ) -> TruthVersion | None:
        if not isinstance(scope, ScopeRef):
            raise ContractValidationError("scope_required")
        _require_uuid(version_id, "data_version_id_required")
        record = next(
            (
                item
                for item in self.__records
                if item.version.id == version_id
            ),
            None,
        )
        if record is not None and record.scope != scope:
            raise ContractValidationError("cross_scope_forbidden")
        return record

    def probe_versions(
        self,
        scope: ScopeRef,
        entity_kind: TruthEntityKind,
        subject_ref: str,
    ) -> tuple[TruthVersion, ...]:
        if not isinstance(scope, ScopeRef):
            raise ContractValidationError("scope_required")
        if not isinstance(entity_kind, TruthEntityKind):
            raise ContractValidationError("truth_entity_kind_required")
        _require_identifier(subject_ref, "truth_subject_ref_required")
        records = (
            record
            for record in self.__records
            if record.scope == scope
            and record.entity_kind is entity_kind
            and record.payload.subject_ref == subject_ref
        )
        return tuple(sorted(records, key=lambda record: record.version.version_no))

    def probe_current(
        self,
        scope: ScopeRef,
        entity_kind: TruthEntityKind,
        subject_ref: str,
        *,
        at: datetime,
    ) -> TruthVersion | None:
        if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
            raise ContractValidationError("read_time_required")
        records = self.probe_versions(scope, entity_kind, subject_ref)
        if not records:
            return None
        parent_ids = {
            record.parent_version_id
            for record in records
            if record.parent_version_id is not None
        }
        heads = tuple(
            record for record in records if record.version.id not in parent_ids
        )
        if len(heads) != 1:
            raise ContractValidationError("truth_head_conflict")
        head = heads[0]
        if not is_current_readable_state(head.data_state):
            return None
        if head.approval is None:
            raise ContractValidationError("approval_evidence_required")
        if not head.is_fresh_at(at):
            return None
        return head
