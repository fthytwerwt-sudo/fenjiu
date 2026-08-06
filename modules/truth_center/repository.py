"""Append-only in-memory contract repository and scoped current-truth read model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from core.contracts import ContractValidationError, DataState, ScopeRef
from core.contracts.access import (
    RepositoryGrantVerifier,
    RepositoryReadGrant,
)
from core.contracts.scope import _require_identifier, _require_uuid
from modules.truth_center.models import (
    TruthEntityKind,
    TruthVersion,
    is_current_readable_state,
    validate_transition,
)


class InMemoryTruthRepository:
    """A no-I/O probe for repository invariants; it is not a production adapter."""

    def __init__(self) -> None:
        self._versions_by_id: dict[UUID, TruthVersion] = {}
        self._entity_ids: set[UUID] = set()
        self._series_versions: set[tuple[ScopeRef, TruthEntityKind, str, int]] = set()
        self._child_by_parent: dict[UUID, UUID] = {}
        self.__grant_verifier: RepositoryGrantVerifier | None = None

    def _bind_grant_verifier(self, verifier: RepositoryGrantVerifier) -> None:
        """Bind one policy verifier for all public current reads."""

        if (
            type(verifier) is RepositoryGrantVerifier
            or not isinstance(verifier, RepositoryGrantVerifier)
        ):
            raise ContractValidationError("repository_grant_verifier_required")
        if self.__grant_verifier is not None and self.__grant_verifier is not verifier:
            raise ContractValidationError("repository_grant_verifier_already_bound")
        self.__grant_verifier = verifier

    def append(self, record: TruthVersion) -> None:
        if not isinstance(record, TruthVersion):
            raise ContractValidationError("truth_version_required")
        if record.version.id in self._versions_by_id:
            raise ContractValidationError("truth_version_immutable")
        if record.metadata.id in self._entity_ids:
            raise ContractValidationError("truth_record_immutable")
        series_key = (
            record.scope,
            record.entity_kind,
            record.payload.subject_ref,
            record.version.version_no,
        )
        if series_key in self._series_versions:
            raise ContractValidationError("truth_version_number_conflict")

        if record.parent_version_id is None:
            if record.version.version_no != 1:
                raise ContractValidationError("initial_truth_version_required")
            allowed_root_states = (
                {DataState.FIXTURE, DataState.MOCK}
                if record.metadata.is_synthetic
                else {DataState.STAGING}
            )
            if record.data_state not in allowed_root_states:
                raise ContractValidationError("initial_truth_state_forbidden")
        else:
            parent = self._versions_by_id.get(record.parent_version_id)
            if parent is None:
                raise ContractValidationError("parent_version_not_found")
            if record.parent_version_id in self._child_by_parent:
                raise ContractValidationError("truth_history_branch_forbidden")
            validate_transition(parent, record)

        self._versions_by_id[record.version.id] = record
        self._entity_ids.add(record.metadata.id)
        self._series_versions.add(series_key)
        if record.parent_version_id is not None:
            self._child_by_parent[record.parent_version_id] = record.version.id

    def _get_by_id_for_policy(
        self,
        scope: ScopeRef,
        version_id: UUID,
    ) -> TruthVersion | None:
        if not isinstance(scope, ScopeRef):
            raise ContractValidationError("scope_required")
        _require_uuid(version_id, "data_version_id_required")
        record = self._versions_by_id.get(version_id)
        if record is None:
            return None
        if record.scope != scope:
            raise ContractValidationError("cross_scope_forbidden")
        return record

    def _versions_for_contract_probe(
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
            for record in self._versions_by_id.values()
            if record.scope == scope
            and record.entity_kind is entity_kind
            and record.payload.subject_ref == subject_ref
        )
        return tuple(sorted(records, key=lambda record: record.version.version_no))

    def _current_for_contract_probe(
        self,
        scope: ScopeRef,
        entity_kind: TruthEntityKind,
        subject_ref: str,
        *,
        at: datetime,
    ) -> TruthVersion | None:
        if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
            raise ContractValidationError("read_time_required")
        records = self._versions_for_contract_probe(scope, entity_kind, subject_ref)
        if not records:
            return None
        heads = [
            record
            for record in records
            if record.version.id not in self._child_by_parent
        ]
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

    def current(
        self,
        grant: RepositoryReadGrant,
        entity_kind: TruthEntityKind,
        subject_ref: str,
    ) -> TruthVersion | None:
        """Return current truth only through a policy-issued exact grant."""

        if self.__grant_verifier is None:
            raise ContractValidationError("repository_grant_verifier_required")
        validated = self.__grant_verifier.assert_repository_grant(grant)
        current = self._current_for_contract_probe(
            validated.scope,
            entity_kind,
            subject_ref,
            at=validated.read_at,
        )
        if current is not None and current.version.id != validated.data_version_id:
            raise ContractValidationError("repository_grant_target_mismatch")
        if current is not None and (
            current.data_state is not validated.data_state
            or current.metadata.sensitivity is not validated.sensitivity
            or current.metadata.is_synthetic is not validated.is_synthetic
        ):
            raise ContractValidationError("repository_grant_target_metadata_mismatch")
        return current
