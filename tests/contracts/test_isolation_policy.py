"""P02-03 adversarial isolation, fixture, policy, and audit probes."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
import unittest

from core.application.truth_consumer import ScopedTruthConsumer, TruthConsumerCommand
from core.contracts import ContractValidationError, DataState, ScopeRef, Sensitivity
from core.contracts.access import _issue_repository_read_grant
from core.security import (
    AuditPolicyResult,
    InMemoryIsolationAuditLog,
    IsolationAction,
    IsolationPolicy,
    IsolationTarget,
    PolicyDeniedError,
    disabled_feature_flag_snapshot,
)
from modules.truth_center import InMemoryTruthRepository, TruthEntityKind
from tests.contracts.test_truth_contracts import (
    NOW,
    approved_chain,
    truth_record,
    uid,
)


def command_for(record, **overrides: object) -> TruthConsumerCommand:
    values: dict[str, object] = {
        "scope": record.scope,
        "entity_kind": record.entity_kind,
        "subject_ref": record.payload.subject_ref,
        "data_version_id": record.version.id,
        "read_at": NOW + timedelta(hours=1),
        "action": IsolationAction.INTERNAL_TRUTH_READ,
        "actor_ref": "synthetic_consumer",
        "idempotency_key": "synthetic_read_1",
        "policy_decision_ref": "policy_decision_1",
        "feature_flag_snapshot": disabled_feature_flag_snapshot(),
    }
    values.update(overrides)
    return TruthConsumerCommand(**values)


class IsolationPolicyContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = InMemoryIsolationAuditLog(clock=lambda: NOW)
        self.policy = IsolationPolicy()

    def consumer(self, repository: InMemoryTruthRepository) -> ScopedTruthConsumer:
        return ScopedTruthConsumer(repository, self.policy, self.audit)

    def assert_denied(
        self,
        consumer: ScopedTruthConsumer,
        command: TruthConsumerCommand,
        code: str,
    ) -> PolicyDeniedError:
        with self.assertRaises(PolicyDeniedError) as raised:
            consumer.execute(command)
        self.assertEqual(raised.exception.code, code)
        self.assertEqual(raised.exception.audit_event.error_code, code)
        self.assertEqual(
            raised.exception.audit_event.policy_result,
            AuditPolicyResult.DENIED,
        )
        return raised.exception

    def test_complete_scope_approved_fresh_truth_is_allowed_and_audited(self) -> None:
        repository, _, approved = approved_chain()

        current = self.consumer(repository).execute(command_for(approved))

        self.assertEqual(current, approved)
        self.assertEqual(len(self.audit.events), 1)
        self.assertEqual(self.audit.events[0].policy_result, AuditPolicyResult.ALLOWED)
        self.assertIsNone(self.audit.events[0].error_code)
        self.assertFalse(self.audit.events[0].external_execution_attempted)

    def test_cross_tenant_project_and_business_line_are_denied(self) -> None:
        for field, replacement_id in (
            ("tenant_id", uid(91_001)),
            ("project_id", uid(91_101)),
            ("business_line_id", uid(91_201)),
        ):
            repository, _, approved = approved_chain()
            wrong_scope = replace(approved.scope, **{field: replacement_id})
            with self.subTest(field=field):
                self.assert_denied(
                    self.consumer(repository),
                    command_for(approved, scope=wrong_scope),
                    "cross_scope_forbidden",
                )

    def test_unscoped_and_wildcard_scope_are_denied_with_audit(self) -> None:
        repository, _, approved = approved_chain()
        consumer = self.consumer(repository)

        for invalid_scope in (None, "*"):
            with self.subTest(scope=invalid_scope):
                denial = self.assert_denied(
                    consumer,
                    command_for(approved, scope=invalid_scope),
                    "scope_required",
                )
                self.assertIsNone(denial.audit_event.scope)
                self.assertEqual(
                    denial.audit_event.correlation_id,
                    "unscoped_request",
                )

    def test_repository_current_rejects_direct_scope_bypass(self) -> None:
        repository, _, approved = approved_chain()
        self.consumer(repository)

        self.assertFalse(hasattr(repository, "get_by_id"))
        self.assertFalse(hasattr(repository, "versions"))
        for bypass_name in (
            "_get_by_id_for_policy",
            "_versions_for_contract_probe",
            "_current_for_contract_probe",
        ):
            with self.subTest(bypass_name=bypass_name):
                self.assertFalse(hasattr(repository, bypass_name))
                with self.assertRaises(AttributeError):
                    getattr(repository, bypass_name)

        target = repository.policy_target(
            approved.scope,
            approved.version.id,
        )
        self.assertIsNotNone(target)
        assert target is not None
        self.assertFalse(hasattr(target, "payload"))
        self.assertFalse(hasattr(target, "source"))
        self.assertFalse(hasattr(target, "version"))

        with self.assertRaisesRegex(
            ContractValidationError,
            "repository_read_grant_required",
        ):
            repository.current(
                approved.scope,
                approved.entity_kind,
                approved.payload.subject_ref,
                actor_ref="synthetic_consumer",
            )

    def test_repository_rejects_structural_fake_verifier_binding(self) -> None:
        class FakeVerifier:
            @staticmethod
            def assert_repository_grant(grant):
                return grant

        repository = InMemoryTruthRepository()
        self.assertFalse(hasattr(repository, "_bind_grant_verifier"))
        with self.assertRaisesRegex(
            ContractValidationError,
            "repository_grant_verifier_required",
        ):
            repository._bind_read_context(FakeVerifier(), self.audit)

        class FakeAuditRecorder:
            @staticmethod
            def record_repository_read_allowed(**kwargs):
                return None

        with self.assertRaisesRegex(
            ContractValidationError,
            "repository_audit_recorder_required",
        ):
            repository._bind_read_context(self.policy, FakeAuditRecorder())

    def test_direct_policy_grant_read_cannot_bypass_mandatory_audit(self) -> None:
        repository, _, approved = approved_chain()
        direct_policy = IsolationPolicy()
        direct_audit = InMemoryIsolationAuditLog(clock=lambda: NOW)
        repository._bind_read_context(direct_policy, direct_audit)
        target = repository.policy_target(approved.scope, approved.version.id)
        assert target is not None
        evaluation = direct_policy.evaluate(
            scope=approved.scope,
            target=IsolationTarget(
                scope=target.scope,
                data_version_id=target.data_version_id,
                data_state=target.data_state,
                sensitivity=target.sensitivity,
                is_synthetic=target.is_synthetic,
            ),
            action=IsolationAction.INTERNAL_TRUTH_READ,
            feature_flag_snapshot=disabled_feature_flag_snapshot(),
            read_at=NOW + timedelta(hours=1),
            policy_decision_ref="direct_policy_read",
        )
        assert evaluation.grant is not None

        current = repository.current(
            evaluation.grant,
            approved.entity_kind,
            approved.payload.subject_ref,
            actor_ref="direct_in_process_caller",
        )

        self.assertEqual(current, approved)
        self.assertEqual(len(direct_audit.events), 1)
        self.assertEqual(
            direct_audit.events[0].policy_result,
            AuditPolicyResult.ALLOWED,
        )
        self.assertEqual(direct_audit.events[0].data_version_id, approved.version.id)

    def test_repository_grant_cannot_be_tampered_or_reused_for_another_version(self) -> None:
        repository, _, approved = approved_chain()
        self.consumer(repository)
        evaluation = self.policy.evaluate(
            scope=approved.scope,
            target=IsolationTarget(
                scope=approved.scope,
                data_version_id=approved.version.id,
                data_state=approved.data_state,
                sensitivity=approved.metadata.sensitivity,
                is_synthetic=approved.metadata.is_synthetic,
            ),
            action=IsolationAction.INTERNAL_TRUTH_READ,
            feature_flag_snapshot=disabled_feature_flag_snapshot(),
            read_at=NOW + timedelta(hours=1),
            policy_decision_ref="policy_decision_grant",
        )
        self.assertTrue(evaluation.allowed)
        self.assertIsNotNone(evaluation.grant)
        grant = evaluation.grant
        assert grant is not None

        with self.assertRaisesRegex(
            ContractValidationError,
            "repository_read_grant_invalid",
        ):
            repository.current(
                replace(
                    grant,
                    scope=replace(grant.scope, business_line_id=uid(92_201)),
                ),
                approved.entity_kind,
                approved.payload.subject_ref,
                actor_ref="synthetic_consumer",
            )

        other_candidate = truth_record(
            state=DataState.STAGING,
            version_no=1,
            seed=230,
            subject_ref="other_subject",
        )
        other_approved = truth_record(
            state=DataState.APPROVED,
            version_no=2,
            seed=231,
            parent_version_id=other_candidate.version.id,
            subject_ref="other_subject",
        )
        repository.append(other_candidate)
        repository.append(other_approved)
        with self.assertRaisesRegex(
            ContractValidationError,
            "repository_grant_target_mismatch",
        ):
            repository.current(
                grant,
                other_approved.entity_kind,
                other_approved.payload.subject_ref,
                actor_ref="synthetic_consumer",
            )

    def test_direct_grant_issuer_call_is_rejected_without_policy_registration(self) -> None:
        repository, _, approved = approved_chain()
        self.consumer(repository)
        forged = _issue_repository_read_grant(
            scope=approved.scope,
            data_version_id=approved.version.id,
            read_at=NOW + timedelta(hours=1),
            policy_decision_ref="forged_policy_decision",
            data_state=approved.data_state,
            sensitivity=approved.metadata.sensitivity,
            is_synthetic=approved.metadata.is_synthetic,
        )

        with self.assertRaisesRegex(
            ContractValidationError,
            "repository_read_grant_not_issued",
        ):
            repository.current(
                forged,
                approved.entity_kind,
                approved.payload.subject_ref,
                actor_ref="synthetic_consumer",
            )

    def test_fixture_external_action_is_denied_and_records_intent(self) -> None:
        repository = InMemoryTruthRepository()
        fixture = truth_record(state=DataState.FIXTURE, version_no=1, seed=201)
        repository.append(fixture)

        denial = self.assert_denied(
            self.consumer(repository),
            command_for(fixture, action=IsolationAction.EXTERNAL_SEND),
            "fixture_external_action_forbidden",
        )

        self.assertTrue(denial.audit_event.external_execution_attempted)
        self.assertEqual(denial.audit_event.data_state, DataState.FIXTURE)
        self.assertEqual(denial.audit_event.sensitivity, Sensitivity.INTERNAL)

    def test_approved_truth_still_cannot_enable_any_external_action(self) -> None:
        repository, _, approved = approved_chain()

        for action in IsolationAction:
            if action is IsolationAction.INTERNAL_TRUTH_READ:
                continue
            with self.subTest(action=action):
                self.assert_denied(
                    self.consumer(repository),
                    command_for(approved, action=action),
                    "external_action_disabled",
                )

    def test_candidate_expired_conflict_and_superseded_consumer_attempts_fail(self) -> None:
        candidate_repository = InMemoryTruthRepository()
        candidate = truth_record(
            state=DataState.STAGING,
            version_no=1,
            seed=210,
        )
        candidate_repository.append(candidate)
        cases = [(candidate_repository, candidate)]

        for seed, terminal_state in enumerate(
            (DataState.EXPIRED, DataState.CONFLICT, DataState.SUPERSEDED),
            start=211,
        ):
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
            cases.append((repository, terminal))

        for repository, record in cases:
            with self.subTest(state=record.data_state):
                self.assert_denied(
                    self.consumer(repository),
                    command_for(record),
                    "truth_not_current",
                )

    def test_superseded_or_conflicted_head_invalidates_prior_approved_version(self) -> None:
        for seed, state in ((220, DataState.CONFLICT), (221, DataState.SUPERSEDED)):
            repository, _, approved = approved_chain()
            repository.append(
                truth_record(
                    state=state,
                    version_no=3,
                    seed=seed,
                    parent_version_id=approved.version.id,
                    with_approval=True,
                )
            )
            with self.subTest(state=state):
                self.assert_denied(
                    self.consumer(repository),
                    command_for(approved),
                    "truth_not_current",
                )

    def test_expired_effective_window_is_denied(self) -> None:
        repository, _, approved = approved_chain()

        self.assert_denied(
            self.consumer(repository),
            command_for(approved, read_at=NOW + timedelta(days=2)),
            "truth_not_current",
        )

    def test_restricted_truth_is_denied_by_fixed_local_sensitivity_policy(self) -> None:
        repository, candidate, approved = approved_chain()
        restricted = replace(
            approved,
            source=replace(approved.source, sensitivity=Sensitivity.RESTRICTED),
            version=replace(approved.version, sensitivity=Sensitivity.RESTRICTED),
            metadata=replace(approved.metadata, sensitivity=Sensitivity.RESTRICTED),
        )
        isolated_repository = InMemoryTruthRepository()
        isolated_repository.append(candidate)
        isolated_repository.append(restricted)

        self.assert_denied(
            self.consumer(isolated_repository),
            command_for(restricted),
            "sensitivity_forbidden",
        )

    def test_repository_rejects_spoofed_policy_target_metadata(self) -> None:
        _, candidate, approved = approved_chain()
        restricted = replace(
            approved,
            source=replace(approved.source, sensitivity=Sensitivity.RESTRICTED),
            version=replace(approved.version, sensitivity=Sensitivity.RESTRICTED),
            metadata=replace(approved.metadata, sensitivity=Sensitivity.RESTRICTED),
        )
        repository = InMemoryTruthRepository()
        repository.append(candidate)
        repository.append(restricted)
        self.consumer(repository)
        evaluation = self.policy.evaluate(
            scope=restricted.scope,
            target=IsolationTarget(
                scope=restricted.scope,
                data_version_id=restricted.version.id,
                data_state=DataState.APPROVED,
                sensitivity=Sensitivity.INTERNAL,
                is_synthetic=restricted.metadata.is_synthetic,
            ),
            action=IsolationAction.INTERNAL_TRUTH_READ,
            feature_flag_snapshot=disabled_feature_flag_snapshot(),
            read_at=NOW + timedelta(hours=1),
            policy_decision_ref="policy_decision_spoof",
        )
        self.assertTrue(evaluation.allowed)
        assert evaluation.grant is not None
        with self.assertRaisesRegex(
            ContractValidationError,
            "repository_grant_target_metadata_mismatch",
        ):
            repository.current(
                evaluation.grant,
                restricted.entity_kind,
                restricted.payload.subject_ref,
                actor_ref="synthetic_consumer",
            )

    def test_incomplete_or_enabled_feature_snapshot_is_denied(self) -> None:
        repository, _, approved = approved_chain()
        consumer = self.consumer(repository)
        complete = dict(disabled_feature_flag_snapshot())

        incomplete = tuple(sorted({
            key: value
            for key, value in complete.items()
            if key != "external_send_enabled"
        }.items()))
        self.assert_denied(
            consumer,
            command_for(approved, feature_flag_snapshot=incomplete),
            "feature_flag_snapshot_invalid",
        )
        complete["external_send_enabled"] = True
        self.assert_denied(
            consumer,
            command_for(
                approved,
                feature_flag_snapshot=tuple(sorted(complete.items())),
            ),
            "external_flags_must_remain_false",
        )

    def test_audit_contract_is_payload_free_sequential_and_append_only(self) -> None:
        repository, _, approved = approved_chain()
        consumer = self.consumer(repository)
        self.assert_denied(
            consumer,
            command_for(approved, feature_flag_snapshot=()),
            "feature_flag_snapshot_invalid",
        )
        self.assert_denied(
            consumer,
            command_for(approved, scope=None),
            "scope_required",
        )

        events = self.audit.events
        self.assertIsInstance(events, tuple)
        self.assertEqual([event.sequence for event in events], [1, 2])
        self.assertFalse(hasattr(self.audit, "update"))
        self.assertFalse(hasattr(self.audit, "delete"))
        self.assertFalse(hasattr(self.audit, "__dict__"))
        with self.assertRaises(AttributeError):
            self.audit._events.clear()  # type: ignore[attr-defined]
        with self.assertRaises(FrozenInstanceError):
            events[0].error_code = "changed"  # type: ignore[misc]
        self.assertEqual(len(self.audit.events), 2)
        event_fields = set(events[0].__dataclass_fields__)
        self.assertTrue(
            {"policy_result", "error_code", "scope", "data_version_id"}
            <= event_fields
        )
        self.assertTrue(
            {"payload", "message", "file", "secret", "url"}.isdisjoint(
                event_fields
            )
        )

    def test_command_requires_safe_actor_idempotency_and_policy_references(self) -> None:
        repository, _, approved = approved_chain()
        consumer = self.consumer(repository)

        for field, value, code in (
            ("actor_ref", "", "actor_ref_required"),
            ("idempotency_key", "*", "idempotency_key_required"),
            ("policy_decision_ref", None, "policy_decision_ref_required"),
        ):
            with self.subTest(field=field):
                self.assert_denied(
                    consumer,
                    command_for(approved, **{field: value}),
                    code,
                )


if __name__ == "__main__":
    unittest.main()
