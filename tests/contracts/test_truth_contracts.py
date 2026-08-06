"""P02-02 synthetic contract probes for truth lifecycle and current reads."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest
from uuid import UUID

from core.contracts import (
    BaseMetadata,
    ContractValidationError,
    DataState,
    DataVersionRef,
    ScopeRef,
    Sensitivity,
    SourceRef,
    synthetic_scope,
)
from modules.truth_center import (
    ApprovalEvidence,
    InMemoryTruthRepository,
    TruthEntityKind,
    TruthPayloadRef,
    TruthVersion,
    is_current_readable_state,
    validate_transition,
)


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def uid(number: int) -> UUID:
    return UUID(int=number)


def contract_probe_scope() -> ScopeRef:
    return ScopeRef(
        tenant_id=uid(90_001),
        project_id=uid(90_101),
        business_line_id=uid(90_201),
        correlation_id="contract_probe",
    )


def truth_record(
    *,
    state: DataState,
    version_no: int,
    seed: int,
    entity_kind: TruthEntityKind = TruthEntityKind.PRICE,
    scope: ScopeRef | None = None,
    parent_version_id: UUID | None = None,
    with_approval: bool | None = None,
    effective_from: datetime | None = None,
    effective_until: datetime | None = None,
    subject_ref: str = "synthetic_subject",
) -> TruthVersion:
    synthetic_marker = state in {DataState.FIXTURE, DataState.MOCK}
    scoped = scope or (synthetic_scope() if synthetic_marker else contract_probe_scope())
    source_id = uid(10_000 + seed)
    data_version_id = uid(20_000 + seed)
    source_state = state if synthetic_marker else DataState.STAGING
    source = SourceRef(
        id=source_id,
        scope=scoped,
        source_kind="contract_probe",
        source_version=f"v{version_no}",
        data_state=source_state,
        sensitivity=Sensitivity.INTERNAL,
        is_synthetic=synthetic_marker,
    )
    version = DataVersionRef(
        id=data_version_id,
        scope=scoped,
        source_ref_id=source_id,
        version_no=version_no,
        data_state=state,
        sensitivity=Sensitivity.INTERNAL,
        is_synthetic=synthetic_marker,
    )
    metadata = BaseMetadata(
        id=uid(30_000 + seed),
        scope=scoped,
        data_state=state,
        source_ref_id=source_id,
        data_version_id=data_version_id,
        sensitivity=Sensitivity.INTERNAL,
        is_synthetic=synthetic_marker,
        external_execution_allowed=False,
        created_at=NOW + timedelta(seconds=version_no),
        updated_at=NOW + timedelta(seconds=version_no),
        created_by="contract_probe",
    )
    approval_required = state is DataState.APPROVED
    include_approval = approval_required if with_approval is None else with_approval
    approval = None
    if include_approval:
        approval = ApprovalEvidence(
            id=uid(40_000 + seed),
            scope=scoped,
            source_ref_id=source_id,
            data_version_id=data_version_id,
            actor_ref="synthetic_reviewer",
            decision_ref=f"decision_{seed}",
            evidence_ref=f"evidence_{seed}",
            policy_version="policy_v1",
            approved_at=NOW,
        )
    if approval_required and effective_from is None:
        effective_from = NOW
    return TruthVersion(
        entity_kind=entity_kind,
        payload=TruthPayloadRef(
            subject_ref=subject_ref,
            field_names=("contract_field",),
            payload_hash=f"{seed:064x}",
        ),
        source=source,
        version=version,
        metadata=metadata,
        changed_fields=("contract_field",),
        diff_hash=f"{50_000 + seed:064x}",
        effective_from=effective_from,
        effective_until=effective_until,
        parent_version_id=parent_version_id,
        approval=approval,
    )


def approved_chain(
    entity_kind: TruthEntityKind = TruthEntityKind.PRICE,
) -> tuple[InMemoryTruthRepository, TruthVersion, TruthVersion]:
    repository = InMemoryTruthRepository()
    candidate = truth_record(
        state=DataState.STAGING,
        version_no=1,
        seed=1,
        entity_kind=entity_kind,
    )
    approved = truth_record(
        state=DataState.APPROVED,
        version_no=2,
        seed=2,
        entity_kind=entity_kind,
        parent_version_id=candidate.version.id,
        effective_from=NOW,
        effective_until=NOW + timedelta(days=2),
    )
    repository.append(candidate)
    repository.append(approved)
    return repository, candidate, approved


class TruthContractTests(unittest.TestCase):
    def test_all_required_entity_kinds_have_candidate_contracts(self) -> None:
        self.assertEqual(
            {kind.value for kind in TruthEntityKind},
            {
                "product",
                "sku",
                "price",
                "inventory",
                "delivery_rule",
                "compliance_document",
                "content_asset",
                "approved_fact",
                "forbidden_expression",
            },
        )
        for seed, entity_kind in enumerate(TruthEntityKind, start=100):
            with self.subTest(entity_kind=entity_kind):
                record = truth_record(
                    state=DataState.STAGING,
                    version_no=1,
                    seed=seed,
                    entity_kind=entity_kind,
                )
                self.assertTrue(record.is_candidate)
                self.assertFalse(record.payload.external_execution_allowed)

    def test_candidate_to_approved_requires_explicit_successor(self) -> None:
        repository, candidate, approved = approved_chain()

        self.assertEqual(
            repository.current(
                approved.scope,
                approved.entity_kind,
                approved.payload.subject_ref,
                at=NOW + timedelta(days=1),
            ),
            approved,
        )
        self.assertEqual(
            len(
                repository.versions(
                    approved.scope,
                    approved.entity_kind,
                    approved.payload.subject_ref,
                )
            ),
            2,
        )

    def test_fixture_and_candidate_are_never_current_truth(self) -> None:
        for seed, state in enumerate((DataState.FIXTURE, DataState.STAGING), start=10):
            repository = InMemoryTruthRepository()
            record = truth_record(state=state, version_no=1, seed=seed)
            repository.append(record)
            with self.subTest(state=state):
                self.assertIsNone(
                    repository.current(
                        record.scope,
                        record.entity_kind,
                        record.payload.subject_ref,
                        at=NOW,
                    )
                )

    def test_approved_truth_requires_source_version_and_approval_lineage(self) -> None:
        _, _, approved = approved_chain()

        with self.assertRaisesRegex(ContractValidationError, "approval_evidence_required"):
            replace(approved, approval=None)
        with self.assertRaisesRegex(
            ContractValidationError,
            "approval_source_lineage_mismatch",
        ):
            replace(
                approved,
                approval=replace(approved.approval, source_ref_id=uid(99_001)),
            )
        with self.assertRaisesRegex(
            ContractValidationError,
            "approval_version_lineage_mismatch",
        ):
            replace(
                approved,
                approval=replace(approved.approval, data_version_id=uid(99_002)),
            )

    def test_approved_truth_outside_effective_window_is_not_current(self) -> None:
        repository, _, approved = approved_chain()

        self.assertIsNone(
            repository.current(
                approved.scope,
                approved.entity_kind,
                approved.payload.subject_ref,
                at=NOW - timedelta(seconds=1),
            )
        )
        self.assertIsNone(
            repository.current(
                approved.scope,
                approved.entity_kind,
                approved.payload.subject_ref,
                at=NOW + timedelta(days=2),
            )
        )

    def test_expired_conflict_and_superseded_heads_are_not_current(self) -> None:
        terminal_states = (
            DataState.EXPIRED,
            DataState.CONFLICT,
            DataState.SUPERSEDED,
        )
        for seed, terminal_state in enumerate(terminal_states, start=20):
            repository, _, approved = approved_chain()
            terminal = truth_record(
                state=terminal_state,
                version_no=3,
                seed=seed,
                parent_version_id=approved.version.id,
                with_approval=True,
                effective_from=NOW,
                effective_until=(
                    NOW + timedelta(days=1)
                    if terminal_state is DataState.EXPIRED
                    else None
                ),
            )
            repository.append(terminal)
            with self.subTest(state=terminal_state):
                self.assertIsNone(
                    repository.current(
                        terminal.scope,
                        terminal.entity_kind,
                        terminal.payload.subject_ref,
                        at=NOW + timedelta(hours=1),
                    )
                )

    def test_conflict_resolution_needs_new_approved_version_and_evidence(self) -> None:
        repository = InMemoryTruthRepository()
        candidate = truth_record(state=DataState.STAGING, version_no=1, seed=30)
        conflict = truth_record(
            state=DataState.CONFLICT,
            version_no=2,
            seed=31,
            parent_version_id=candidate.version.id,
        )
        resolved = truth_record(
            state=DataState.APPROVED,
            version_no=3,
            seed=32,
            parent_version_id=conflict.version.id,
        )
        repository.append(candidate)
        repository.append(conflict)
        self.assertIsNone(
            repository.current(
                conflict.scope,
                conflict.entity_kind,
                conflict.payload.subject_ref,
                at=NOW,
            )
        )
        repository.append(resolved)
        self.assertEqual(
            repository.current(
                resolved.scope,
                resolved.entity_kind,
                resolved.payload.subject_ref,
                at=NOW,
            ),
            resolved,
        )

    def test_fixture_cannot_transition_to_approved(self) -> None:
        fixture = truth_record(state=DataState.FIXTURE, version_no=1, seed=40)
        approved = truth_record(
            state=DataState.APPROVED,
            version_no=2,
            seed=41,
            scope=fixture.scope,
            parent_version_id=fixture.version.id,
        )

        with self.assertRaisesRegex(
            ContractValidationError,
            "truth_state_transition_forbidden",
        ):
            validate_transition(fixture, approved)

    def test_direct_approved_root_is_rejected(self) -> None:
        repository = InMemoryTruthRepository()
        approved = truth_record(state=DataState.APPROVED, version_no=1, seed=50)

        with self.assertRaisesRegex(
            ContractValidationError,
            "initial_truth_state_forbidden",
        ):
            repository.append(approved)

    def _assert_terminal_root_rejected(self, state: DataState, seed: int) -> None:
        repository = InMemoryTruthRepository()
        root = truth_record(
            state=state,
            version_no=1,
            seed=seed,
            effective_from=NOW if state is DataState.EXPIRED else None,
            effective_until=(
                NOW + timedelta(days=1) if state is DataState.EXPIRED else None
            ),
        )
        with self.assertRaisesRegex(
            ContractValidationError,
            "initial_truth_state_forbidden",
        ):
            repository.append(root)

    def test_conflict_root_is_rejected(self) -> None:
        self._assert_terminal_root_rejected(DataState.CONFLICT, 51)

    def test_blocked_root_is_rejected(self) -> None:
        self._assert_terminal_root_rejected(DataState.BLOCKED, 52)

    def test_expired_root_is_rejected(self) -> None:
        self._assert_terminal_root_rejected(DataState.EXPIRED, 53)

    def test_superseded_root_is_rejected(self) -> None:
        self._assert_terminal_root_rejected(DataState.SUPERSEDED, 54)

    def test_conflict_root_cannot_seed_an_approved_current_truth(self) -> None:
        repository = InMemoryTruthRepository()
        conflict_root = truth_record(
            state=DataState.CONFLICT,
            version_no=1,
            seed=55,
        )
        approved_child = truth_record(
            state=DataState.APPROVED,
            version_no=2,
            seed=56,
            parent_version_id=conflict_root.version.id,
        )

        with self.assertRaisesRegex(
            ContractValidationError,
            "initial_truth_state_forbidden",
        ):
            repository.append(conflict_root)
        with self.assertRaisesRegex(ContractValidationError, "parent_version_not_found"):
            repository.append(approved_child)
        self.assertIsNone(
            repository.current(
                approved_child.scope,
                approved_child.entity_kind,
                approved_child.payload.subject_ref,
                at=NOW,
            )
        )

    def test_cross_scope_transition_and_read_are_rejected(self) -> None:
        repository = InMemoryTruthRepository()
        candidate = truth_record(state=DataState.STAGING, version_no=1, seed=60)
        other_scope = replace(
            synthetic_scope(),
            business_line_id=uid(60_001),
        )
        cross_scope_approved = truth_record(
            state=DataState.APPROVED,
            version_no=2,
            seed=61,
            scope=other_scope,
            parent_version_id=candidate.version.id,
        )
        repository.append(candidate)

        with self.assertRaisesRegex(ContractValidationError, "cross_scope_forbidden"):
            repository.append(cross_scope_approved)
        with self.assertRaisesRegex(ContractValidationError, "cross_scope_forbidden"):
            repository.get_by_id(other_scope, candidate.version.id)

    def test_history_is_immutable_and_cannot_branch(self) -> None:
        repository, _, approved = approved_chain()

        with self.assertRaisesRegex(ContractValidationError, "truth_version_immutable"):
            repository.append(approved)

        first_child = truth_record(
            state=DataState.SUPERSEDED,
            version_no=3,
            seed=70,
            parent_version_id=approved.version.id,
            with_approval=True,
        )
        second_child = truth_record(
            state=DataState.CONFLICT,
            version_no=4,
            seed=71,
            parent_version_id=approved.version.id,
            with_approval=True,
        )
        repository.append(first_child)
        with self.assertRaisesRegex(
            ContractValidationError,
            "truth_history_branch_forbidden",
        ):
            repository.append(second_child)

    def test_invalid_windows_fields_and_state_lineage_fail_closed(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "effective_window_invalid"):
            truth_record(
                state=DataState.STAGING,
                version_no=1,
                seed=80,
                effective_from=NOW,
                effective_until=NOW,
            )

        candidate = truth_record(state=DataState.STAGING, version_no=1, seed=81)
        with self.assertRaisesRegex(
            ContractValidationError,
            "changed_fields_not_in_payload",
        ):
            replace(candidate, changed_fields=("unknown_field",))
        with self.assertRaisesRegex(ContractValidationError, "truth_diff_hash_required"):
            replace(candidate, diff_hash="not_a_hash")
        with self.assertRaisesRegex(
            ContractValidationError,
            "truth_state_lineage_mismatch",
        ):
            replace(
                candidate,
                version=replace(candidate.version, data_state=DataState.CONFLICT),
            )

    def test_only_approved_is_a_current_readable_state(self) -> None:
        for state in DataState:
            with self.subTest(state=state):
                self.assertEqual(
                    is_current_readable_state(state),
                    state is DataState.APPROVED,
                )

    def test_invalid_read_inputs_fail_closed(self) -> None:
        repository = InMemoryTruthRepository()
        with self.assertRaisesRegex(ContractValidationError, "read_time_required"):
            repository.current(
                synthetic_scope(),
                TruthEntityKind.PRICE,
                "synthetic_subject",
                at=datetime(2026, 1, 1),
            )
        with self.assertRaisesRegex(
            ContractValidationError,
            "truth_subject_ref_required",
        ):
            repository.versions(
                synthetic_scope(),
                TruthEntityKind.PRICE,
                "not a safe subject",
            )


if __name__ == "__main__":
    unittest.main()
