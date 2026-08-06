"""Append-only in-memory contract repository and scoped current-truth read model."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from core.contracts import ContractValidationError, DataState, ScopeRef, Sensitivity
from core.contracts.access import (
    RepositoryAuditRecorder,
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


@dataclass(frozen=True)
class TruthPolicyTarget:
    """Value-free repository metadata used only to make a policy decision."""

    scope: ScopeRef
    data_version_id: UUID
    entity_kind: TruthEntityKind
    subject_ref: str
    data_state: DataState
    sensitivity: Sensitivity
    is_synthetic: bool


class InMemoryTruthRepository:
    """A no-I/O probe for repository invariants; it is not a production adapter."""

    def __init__(self) -> None:
        self._versions_by_id: dict[UUID, TruthVersion] = {}
        self._entity_ids: set[UUID] = set()
        self._series_versions: set[tuple[ScopeRef, TruthEntityKind, str, int]] = set()
        self._child_by_parent: dict[UUID, UUID] = {}
        self.__grant_verifier: RepositoryGrantVerifier | None = None
        self.__audit_recorder: RepositoryAuditRecorder | None = None

    def _bind_read_context(
        self,
        verifier: RepositoryGrantVerifier,
        audit_recorder: RepositoryAuditRecorder,
    ) -> None:
        """Bind the exact policy and mandatory audit sink for current reads."""

        if (
            type(verifier) is RepositoryGrantVerifier
            or not isinstance(verifier, RepositoryGrantVerifier)
        ):
            raise ContractValidationError("repository_grant_verifier_required")
        if (
            type(audit_recorder) is RepositoryAuditRecorder
            or not isinstance(audit_recorder, RepositoryAuditRecorder)
        ):
            raise ContractValidationError("repository_audit_recorder_required")
        if self.__grant_verifier is not None and self.__grant_verifier is not verifier:
            raise ContractValidationError("repository_grant_verifier_already_bound")
        if (
            self.__audit_recorder is not None
            and self.__audit_recorder is not audit_recorder
        ):
            raise ContractValidationError("repository_audit_recorder_already_bound")
        self.__grant_verifier = verifier
        self.__audit_recorder = audit_recorder

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

    def policy_target(
        self,
        scope: ScopeRef,
        version_id: UUID,
    ) -> TruthPolicyTarget | None:
        """Return policy metadata, never the truth payload or source record."""

        if not isinstance(scope, ScopeRef):
            raise ContractValidationError("scope_required")
        _require_uuid(version_id, "data_version_id_required")
        record = self._versions_by_id.get(version_id)
        if record is None:
            return None
        if record.scope != scope:
            raise ContractValidationError("cross_scope_forbidden")
        return TruthPolicyTarget(
            scope=record.scope,
            data_version_id=record.version.id,
            entity_kind=record.entity_kind,
            subject_ref=record.payload.subject_ref,
            data_state=record.data_state,
            sensitivity=record.metadata.sensitivity,
            is_synthetic=record.metadata.is_synthetic,
        )

    def current(
        self,
        grant: RepositoryReadGrant,
        entity_kind: TruthEntityKind,
        subject_ref: str,
    ) -> TruthVersion | None:
        """Audit, then return truth through a policy-issued exact grant."""

        if self.__grant_verifier is None:
            raise ContractValidationError("repository_grant_verifier_required")
        if self.__audit_recorder is None:
            raise ContractValidationError("repository_audit_recorder_required")
        validated = self.__grant_verifier.assert_repository_grant(grant)
        if not isinstance(entity_kind, TruthEntityKind):
            raise ContractValidationError("truth_entity_kind_required")
        _require_identifier(subject_ref, "truth_subject_ref_required")
        records = tuple(
            record
            for record in self._versions_by_id.values()
            if record.scope == validated.scope
            and record.entity_kind is entity_kind
            and record.payload.subject_ref == subject_ref
        )
        if not records:
            return None
        heads = tuple(
            record
            for record in records
            if record.version.id not in self._child_by_parent
        )
        if len(heads) != 1:
            raise ContractValidationError("truth_head_conflict")
        current = heads[0]
        if not is_current_readable_state(current.data_state):
            return None
        if current.approval is None:
            raise ContractValidationError("approval_evidence_required")
        if not current.is_fresh_at(validated.read_at):
            return None
        if current is not None and current.version.id != validated.data_version_id:
            raise ContractValidationError("repository_grant_target_mismatch")
        if current is not None and (
            current.data_state is not validated.data_state
            or current.metadata.sensitivity is not validated.sensitivity
            or current.metadata.is_synthetic is not validated.is_synthetic
        ):
            raise ContractValidationError("repository_grant_target_metadata_mismatch")
        self.__audit_recorder.record_repository_read_allowed(
            scope=validated.scope,
            actor_ref=validated.actor_ref,
            target_ref=subject_ref,
            data_version_id=current.version.id,
            data_state=current.data_state,
            sensitivity=current.metadata.sensitivity,
            policy_decision_ref=validated.policy_decision_ref,
        )
        return current
