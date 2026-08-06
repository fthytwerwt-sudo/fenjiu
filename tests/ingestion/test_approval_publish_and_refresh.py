"""P03-03 synthetic approval, immutable publish, and refresh contract probes."""

from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from uuid import UUID

from core.contracts import ContractValidationError, synthetic_scope
from modules.ingestion.approval import (
    ApprovalBoundaryError,
    ApprovalDecisionKind,
    ApprovalRequestState,
    CanonicalMappingCandidateGate,
    InMemoryApprovalRequestStore,
    InMemoryInvalidationOutbox,
    InternalPublicationState,
    ReviewerRole,
    SyntheticApprovalPublisher,
    SyntheticInternalPublicationLedger,
    SyntheticPublicationTransactionLog,
    SyntheticReviewerCapabilityRegistry,
)
from modules.ingestion.mapping import MappingRunState, QualityCode, SyntheticMappingEngine
from modules.ingestion.store import InMemoryIngestionStore
from modules.truth_center import TruthEntityKind
from tests.contracts.truth_repository_harness import TruthRepositoryContractHarness
from tests.ingestion.test_mapping_normalization_and_quality import (
    SCOPE,
    batch_for,
    evidence_for,
    load_profiles,
    unsafe_replace_frozen,
)


NOW = datetime(2040, 2, 3, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[2]


class ApprovalPublishAndRefreshTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_profiles()["profile_alpha"]
        self.mapping_engine = SyntheticMappingEngine(now=lambda: NOW)
        self.ingestion_store = InMemoryIngestionStore()
        self.candidate_gate = CanonicalMappingCandidateGate(
            ingestion_store=self.ingestion_store,
            mapping_engine=self.mapping_engine,
        )
        self.candidate_gate.register_profile(self.profile)
        self.candidate = self._canonical_candidate(31)
        self.reviewer_registry = SyntheticReviewerCapabilityRegistry(now=lambda: NOW)
        self.reviewer_grant = self.reviewer_registry.grant_reviewer(
            actor_ref="human_reviewer",
            role=ReviewerRole.DATA_REVIEWER,
            scope=SCOPE,
            policy_version="approval_policy_v1",
            evidence_ref="capability_evidence_1",
            issued_at=NOW,
            expires_at=NOW + timedelta(hours=1),
            idempotency_key="grant_human_reviewer",
        )
        self.store = InMemoryApprovalRequestStore(
            candidate_gate=self.candidate_gate,
            reviewer_registry=self.reviewer_registry,
            now=lambda: NOW,
        )
        self.ledger = SyntheticInternalPublicationLedger()
        self.outbox = InMemoryInvalidationOutbox()
        self.transaction_log = SyntheticPublicationTransactionLog()
        self.publisher = SyntheticApprovalPublisher(
            request_store=self.store,
            reviewer_registry=self.reviewer_registry,
            ledger=self.ledger,
            outbox=self.outbox,
            transaction_log=self.transaction_log,
            now=lambda: NOW,
        )

    def _store_evidence(self, evidence):
        self.ingestion_store.register_source(evidence.source_file)
        self.ingestion_store.register_job(evidence.ingestion_job)
        self.ingestion_store.append_staging_batch(
            (evidence.extraction_result,),
            (evidence.staging_candidate,),
        )
        return evidence

    def _report_for(self, sequence: int, *, source_hash: str | None = None):
        evidence = self._store_evidence(
            evidence_for(
                profile=self.profile,
                sequence=sequence,
                source_hash=source_hash,
                observed_at=NOW,
            )
        )
        return self.mapping_engine.map(self.profile, batch_for(self.profile, evidence))

    def _canonical_candidate(self, sequence: int):
        report = self._report_for(sequence)
        self.assertEqual(report.state, MappingRunState.MAPPED)
        registered = self.candidate_gate.register_report(
            self.profile,
            report,
            quality_checked_at=NOW,
        )
        return registered[0]

    def _request(
        self,
        *,
        candidate=None,
        subject_ref: str = "subject_alpha",
        idempotency_key: str | None = None,
    ):
        selected = candidate or self.candidate
        return self.store.create_request(
            candidate=selected,
            subject_ref=subject_ref,
            requested_by="system_worker",
            evidence_ref="evidence_packet_1",
            policy_version="approval_policy_v1",
            requested_at=NOW,
            expires_at=NOW + timedelta(hours=1),
            idempotency_key=idempotency_key
            or f"request_{subject_ref}_{selected.id.hex[:12]}",
        )

    def _approve(self, request):
        return self.store.record_decision(
            request_id=request.id,
            decision=ApprovalDecisionKind.APPROVE,
            reviewer_grant_id=self.reviewer_grant.id,
            evidence_ref="review_evidence_1",
            policy_version=request.policy_version,
            decided_at=NOW + timedelta(minutes=5),
            idempotency_key=f"decision_{request.id.hex}",
        )

    def test_approval_to_immutable_internal_publication_and_invalidation_e2e(self) -> None:
        request = self._request()
        self.assertEqual(request.state, ApprovalRequestState.PENDING)
        with self.assertRaisesRegex(ApprovalBoundaryError, "approval_request_not_publishable"):
            self.publisher.publish(request)

        approved_request = self._approve(request)
        publication = self.publisher.publish(approved_request)

        self.assertEqual(approved_request.state, ApprovalRequestState.APPROVED)
        self.assertEqual(
            publication.approved_record.state,
            InternalPublicationState.APPROVED_INTERNAL,
        )
        self.assertEqual(publication.approved_record.version_no, 1)
        self.assertEqual(publication.approved_record.actor_ref, "human_reviewer")
        self.assertEqual(publication.approved_record.evidence_ref, "review_evidence_1")
        self.assertEqual(publication.approved_record.subject_ref, "subject_alpha")
        self.assertEqual(
            publication.approved_record.payload_hash,
            self.candidate.candidate.normalized_value_hash,
        )
        self.assertTrue(publication.approved_record.is_synthetic)
        self.assertFalse(publication.approved_record.p02_current_truth_readable)
        self.assertFalse(publication.approved_record.external_execution_allowed)
        self.assertFalse(publication.approved_record.business_external_ready)
        self.assertEqual(publication.event.event_type, "TruthFactsChanged")
        self.assertEqual(publication.event.destination, "internal_invalidation_outbox")
        self.assertEqual(publication.event.correlation_id, SCOPE.correlation_id)
        self.assertFalse(publication.event.external_execution_allowed)
        self.assertFalse(publication.event.business_external_ready)
        self.assertEqual(self.ledger.appended_record_count, 1)
        self.assertEqual(self.outbox.event_count, 1)

    def test_internal_publication_is_not_p02_current_truth(self) -> None:
        publication = self.publisher.publish(self._approve(self._request()))
        truth_harness = TruthRepositoryContractHarness()

        self.assertIsNone(
            truth_harness.probe_current(
                publication.approved_record.scope,
                TruthEntityKind.APPROVED_FACT,
                publication.approved_record.subject_ref,
                at=NOW,
            )
        )
        with self.assertRaisesRegex(ContractValidationError, "truth_version_required"):
            truth_harness.append(publication.approved_record)
        self.assertFalse(publication.safe_summary()["p02_current_truth_readable"])

    def test_approval_module_ast_never_imports_or_emits_p02_approved_truth(self) -> None:
        source = (ROOT / "modules" / "ingestion" / "approval.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_imports: list[str] = []
        forbidden_approved_refs: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                forbidden_imports.extend(
                    alias.name
                    for alias in node.names
                    if alias.name.startswith("modules.truth_center")
                )
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("modules.truth_center"):
                    forbidden_imports.append(node.module)
            elif isinstance(node, ast.Name) and node.id == "TruthVersion":
                forbidden_approved_refs.append("TruthVersion")
            elif (
                isinstance(node, ast.Attribute)
                and node.attr == "APPROVED"
                and isinstance(node.value, ast.Name)
                and node.value.id == "DataState"
            ):
                forbidden_approved_refs.append("DataState.APPROVED")

        self.assertFalse(forbidden_imports)
        self.assertFalse(forbidden_approved_refs)

    def test_rerun_does_not_duplicate_approval_request_publication_or_event(self) -> None:
        first_request = self._request()
        replayed_request = self._request()
        approved_once = self._approve(first_request)
        approved_twice = self._approve(first_request)
        first_publication = self.publisher.publish(approved_once)
        second_publication = self.publisher.publish(approved_twice)

        self.assertEqual(first_request, replayed_request)
        self.assertEqual(approved_once, approved_twice)
        self.assertEqual(first_publication, second_publication)
        self.assertEqual(self.store.request_version_count(first_request.id), 2)
        self.assertEqual(self.store.audit_event_count, 2)
        self.assertEqual(self.ledger.appended_record_count, 1)
        self.assertEqual(self.outbox.event_count, 1)

    def test_reject_expire_revise_conflict_and_pending_requests_never_publish(self) -> None:
        cases = (
            (ApprovalDecisionKind.REJECT, ApprovalRequestState.REJECTED),
            (ApprovalDecisionKind.EXPIRE, ApprovalRequestState.EXPIRED),
            (ApprovalDecisionKind.REVISE, ApprovalRequestState.REVISION_REQUESTED),
            (ApprovalDecisionKind.MARK_CONFLICT, ApprovalRequestState.CONFLICT),
        )
        for index, (decision, expected_state) in enumerate(cases, start=1):
            with self.subTest(decision=decision):
                request = self._request(subject_ref=f"subject_blocked_{index}")
                blocked = self.store.record_decision(
                    request_id=request.id,
                    decision=decision,
                    reviewer_grant_id=self.reviewer_grant.id,
                    evidence_ref=f"review_evidence_{index}",
                    policy_version=request.policy_version,
                    decided_at=NOW + timedelta(minutes=index),
                    idempotency_key=f"blocked_decision_{index}",
                )
                self.assertEqual(blocked.state, expected_state)
                with self.assertRaisesRegex(ApprovalBoundaryError, "approval_request_not_publishable"):
                    self.publisher.publish(blocked)
        self.assertEqual(self.ledger.appended_record_count, 0)
        self.assertEqual(self.outbox.event_count, 0)

    def test_self_approval_expired_decision_and_policy_mismatch_fail_closed(self) -> None:
        request = self._request()
        self_grant = self.reviewer_registry.grant_reviewer(
            actor_ref=request.requested_by,
            role=ReviewerRole.DATA_REVIEWER,
            scope=request.scope,
            policy_version=request.policy_version,
            evidence_ref="self_capability_evidence",
            issued_at=NOW,
            expires_at=NOW + timedelta(hours=1),
            idempotency_key="grant_system_worker",
        )
        with self.assertRaisesRegex(ApprovalBoundaryError, "self_approval_forbidden"):
            self.store.record_decision(
                request_id=request.id,
                decision=ApprovalDecisionKind.APPROVE,
                reviewer_grant_id=self_grant.id,
                evidence_ref="review_evidence_1",
                policy_version=request.policy_version,
                decided_at=NOW + timedelta(minutes=1),
                idempotency_key="self_decision",
            )
        with self.assertRaisesRegex(ApprovalBoundaryError, "approval_request_expired"):
            self.store.record_decision(
                request_id=request.id,
                decision=ApprovalDecisionKind.APPROVE,
                reviewer_grant_id=self.reviewer_grant.id,
                evidence_ref="review_evidence_2",
                policy_version=request.policy_version,
                decided_at=NOW + timedelta(hours=2),
                idempotency_key="late_decision",
            )
        with self.assertRaisesRegex(ApprovalBoundaryError, "approval_policy_mismatch"):
            self.store.record_decision(
                request_id=request.id,
                decision=ApprovalDecisionKind.APPROVE,
                reviewer_grant_id=self.reviewer_grant.id,
                evidence_ref="review_evidence_3",
                policy_version="approval_policy_v2",
                decided_at=NOW + timedelta(minutes=2),
                idempotency_key="wrong_policy_decision",
            )

    def test_non_quality_cross_scope_or_real_like_candidates_are_rejected(self) -> None:
        blocked_candidate = unsafe_replace_frozen(
            self.candidate,
            state=MappingRunState.BLOCKED_MANUAL,
        )
        cross_scope = replace(synthetic_scope(), correlation_id="other_correlation")
        forged_inner = unsafe_replace_frozen(
            self.candidate.candidate,
            external_execution_allowed=True,
        )
        forged_candidate = unsafe_replace_frozen(self.candidate, candidate=forged_inner)

        with self.assertRaisesRegex(ApprovalBoundaryError, "canonical_candidate_required"):
            self._request(candidate=blocked_candidate)
        with self.assertRaisesRegex(ApprovalBoundaryError, "cross_scope_forbidden"):
            self.store.create_request(
                candidate=self.candidate,
                subject_ref="subject_alpha",
                requested_by="system_worker",
                evidence_ref="evidence_packet_1",
                policy_version="approval_policy_v1",
                requested_at=NOW,
                expires_at=NOW + timedelta(hours=1),
                idempotency_key="cross_scope_request",
                scope=cross_scope,
            )
        with self.assertRaisesRegex(ApprovalBoundaryError, "canonical_candidate_required"):
            self._request(candidate=forged_candidate)

    def test_blocked_mapping_report_and_mapped_conflict_candidates_never_enter_approval(self) -> None:
        first = self._store_evidence(
            evidence_for(
                profile=self.profile,
                sequence=41,
                observed_at=NOW,
                source_hash=f"{4101:064x}",
            )
        )
        second = self._store_evidence(
            evidence_for(
                profile=self.profile,
                sequence=42,
                observed_at=NOW,
                source_hash=f"{4102:064x}",
            )
        )
        report = self.mapping_engine.map(self.profile, batch_for(self.profile, first, second))

        self.assertEqual(report.state, MappingRunState.BLOCKED_MANUAL)
        self.assertIn(QualityCode.MAPPING_CONFLICT, {finding.code for finding in report.findings})
        self.assertEqual({candidate.state for candidate in report.candidates}, {MappingRunState.MAPPED})
        with self.assertRaisesRegex(ApprovalBoundaryError, "canonical_mapping_report_required"):
            self.candidate_gate.register_report(self.profile, report, quality_checked_at=NOW)

    def test_replaced_candidate_or_profile_report_drift_is_rejected_by_canonical_gate(self) -> None:
        report = self._report_for(43)
        canonical = self.candidate_gate.register_report(
            self.profile,
            report,
            quality_checked_at=NOW,
        )[0]
        forged_inner = unsafe_replace_frozen(
            canonical.candidate,
            source_file_id=UUID("00000000-0000-4000-8000-999999999999"),
        )
        forged_candidate = unsafe_replace_frozen(canonical, candidate=forged_inner)
        forged_profile = replace(self.profile, source_signature=f"{5151:064x}")
        forged_profile_report = replace(
            report,
            profile_fingerprint=forged_profile.fingerprint,
        )
        drifted_report = replace(report, run_fingerprint=f"{9999:064x}")

        with self.assertRaisesRegex(ApprovalBoundaryError, "canonical_candidate_required"):
            self._request(candidate=forged_candidate)
        with self.assertRaisesRegex(ApprovalBoundaryError, "mapping_profile_fingerprint_mismatch"):
            self.candidate_gate.register_report(
                forged_profile,
                forged_profile_report,
                quality_checked_at=NOW,
            )
        with self.assertRaisesRegex(ApprovalBoundaryError, "mapping_report_replay_mismatch"):
            self.candidate_gate.register_report(
                self.profile,
                drifted_report,
                quality_checked_at=NOW,
            )

    def test_publish_rejects_replaced_or_noncanonical_approved_request(self) -> None:
        pending = self._request()
        fake = replace(
            pending,
            state=ApprovalRequestState.APPROVED,
            version_no=2,
            decision_id=UUID("00000000-0000-4000-8000-000000009001"),
            decision_kind=ApprovalDecisionKind.APPROVE,
            decision_actor_ref="human_reviewer",
            decision_evidence_ref="review_evidence_1",
            reviewer_grant_id=self.reviewer_grant.id,
            decided_at=NOW + timedelta(minutes=5),
        )

        with self.assertRaisesRegex(ApprovalBoundaryError, "approval_request_not_canonical"):
            self.publisher.publish(fake)

    def test_publish_rechecks_expiry_after_decision(self) -> None:
        request = self._request()
        approved = self._approve(request)
        late_publisher = SyntheticApprovalPublisher(
            request_store=self.store,
            reviewer_registry=self.reviewer_registry,
            ledger=self.ledger,
            outbox=self.outbox,
            transaction_log=self.transaction_log,
            now=lambda: NOW + timedelta(hours=2),
        )

        with self.assertRaisesRegex(ApprovalBoundaryError, "approval_request_expired_at_publish"):
            late_publisher.publish(approved)

    def test_publish_transaction_rolls_back_ledger_when_outbox_fails_then_retries(self) -> None:
        class FailingOutbox(InMemoryInvalidationOutbox):
            def append(self, event):  # type: ignore[override]
                raise ApprovalBoundaryError("forced_outbox_failure")

        request = self._request(subject_ref="subject_atomic")
        approved = self._approve(request)
        failing_outbox = FailingOutbox()
        failing_publisher = SyntheticApprovalPublisher(
            request_store=self.store,
            reviewer_registry=self.reviewer_registry,
            ledger=self.ledger,
            outbox=failing_outbox,
            transaction_log=self.transaction_log,
            now=lambda: NOW,
        )

        with self.assertRaisesRegex(ApprovalBoundaryError, "forced_outbox_failure"):
            failing_publisher.publish(approved)
        self.assertEqual(self.ledger.appended_record_count, 0)
        self.assertEqual(failing_outbox.event_count, 0)
        retry = self.publisher.publish(approved)
        self.assertEqual(retry.approved_record.state, InternalPublicationState.APPROVED_INTERNAL)
        self.assertEqual(self.ledger.appended_record_count, 1)
        self.assertEqual(self.outbox.event_count, 1)

    def test_restart_idempotency_uses_shared_transaction_state(self) -> None:
        approved = self._approve(self._request(subject_ref="subject_restart"))
        first = self.publisher.publish(approved)
        restarted = SyntheticApprovalPublisher(
            request_store=self.store,
            reviewer_registry=self.reviewer_registry,
            ledger=self.ledger,
            outbox=self.outbox,
            transaction_log=self.transaction_log,
            now=lambda: NOW,
        )
        second = restarted.publish(approved)

        self.assertEqual(first, second)
        self.assertEqual(self.ledger.appended_record_count, 1)
        self.assertEqual(self.outbox.event_count, 1)

    def test_supersede_appends_new_versions_and_refresh_event_without_external_sync(self) -> None:
        first_publication = self.publisher.publish(self._approve(self._request()))
        replacement_candidate = self._canonical_candidate(32)
        replacement_request = self._request(
            candidate=replacement_candidate,
            subject_ref="subject_alpha",
        )
        replacement_approved = self._approve(replacement_request)
        replacement_publication = self.publisher.publish(
            replacement_approved,
            supersedes=first_publication,
        )

        self.assertEqual(
            replacement_publication.superseded_record.state,
            InternalPublicationState.SUPERSEDED_INTERNAL,
        )
        self.assertEqual(
            replacement_publication.superseded_record.parent_record_id,
            first_publication.approved_record.id,
        )
        self.assertEqual(
            replacement_publication.approved_record.parent_record_id,
            replacement_publication.superseded_record.id,
        )
        self.assertEqual(
            replacement_publication.approved_record.version_no,
            replacement_publication.superseded_record.version_no + 1,
        )
        self.assertEqual(
            replacement_publication.event.superseded_publication_id,
            first_publication.approved_record.id,
        )
        self.assertEqual(replacement_publication.event.destination, "internal_invalidation_outbox")
        self.assertEqual(self.ledger.appended_record_count, 3)
        self.assertEqual(self.outbox.event_count, 2)

    def test_revoke_appends_internal_record_and_invalidation_without_delete_or_external_sync(self) -> None:
        publication = self.publisher.publish(
            self._approve(self._request(subject_ref="subject_revoke"))
        )
        revoke = self.publisher.revoke(
            publication,
            reviewer_grant_id=self.reviewer_grant.id,
            evidence_ref="revoke_evidence_1",
            policy_version="approval_policy_v1",
            idempotency_key="revoke_subject_revoke",
        )
        replay = self.publisher.revoke(
            publication,
            reviewer_grant_id=self.reviewer_grant.id,
            evidence_ref="revoke_evidence_1",
            policy_version="approval_policy_v1",
            idempotency_key="revoke_subject_revoke",
        )

        self.assertEqual(revoke, replay)
        self.assertEqual(revoke.revoked_record.state, InternalPublicationState.REVOKED_INTERNAL)
        self.assertEqual(revoke.revoked_record.parent_record_id, publication.approved_record.id)
        self.assertEqual(revoke.event.destination, "internal_invalidation_outbox")
        self.assertFalse(revoke.revoked_record.external_execution_allowed)
        self.assertEqual(self.ledger.appended_record_count, 2)
        self.assertEqual(self.outbox.event_count, 2)

    def test_safe_summaries_do_not_expose_values_paths_or_external_actions(self) -> None:
        publication = self.publisher.publish(self._approve(self._request()))
        rendered = repr(
            (
                publication.safe_summary(),
                publication.event.safe_summary(),
                self.store.safe_audit_summary(),
                self.outbox.safe_summary(),
            )
        )

        for forbidden in (
            "raw_text",
            "body",
            "/" + "Users" + "/",
            "secret",
            "token",
            "external_sync",
            "DataState.APPROVED",
            "TruthVersion",
            self.candidate.candidate.source_content_hash,
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)
        self.assertIn("internal_invalidation_outbox", rendered)


if __name__ == "__main__":
    unittest.main()
