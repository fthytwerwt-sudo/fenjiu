"""P03-03 synthetic approval, immutable publish, and refresh contract probes."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from core.contracts import synthetic_scope
from modules.ingestion.approval import (
    ApprovalBoundaryError,
    ApprovalDecisionKind,
    ApprovalRequestState,
    InMemoryApprovalRequestStore,
    InMemoryInvalidationOutbox,
    InternalPublicationState,
    SyntheticInternalPublicationLedger,
    SyntheticApprovalPublisher,
)
from modules.ingestion.mapping import MappingRunState
from modules.truth_center import TruthEntityKind
from tests.contracts.truth_repository_harness import TruthRepositoryContractHarness
from tests.ingestion.test_mapping_normalization_and_quality import (
    SCOPE,
    unsafe_replace_frozen,
    batch_for,
    evidence_for,
    load_profiles,
)


NOW = datetime(2040, 2, 3, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[2]


class ApprovalPublishAndRefreshTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_profiles()["profile_alpha"]
        from modules.ingestion.mapping import SyntheticMappingEngine

        self.mapping_engine = SyntheticMappingEngine(now=lambda: NOW)
        self.candidate = self._mapped_candidate(31)
        self.store = InMemoryApprovalRequestStore(now=lambda: NOW)
        self.ledger = SyntheticInternalPublicationLedger()
        self.outbox = InMemoryInvalidationOutbox()
        self.publisher = SyntheticApprovalPublisher(
            ledger=self.ledger,
            outbox=self.outbox,
            now=lambda: NOW,
        )

    def _mapped_candidate(self, sequence: int):
        report = self.mapping_engine.map(
            self.profile,
            batch_for(
                self.profile,
                evidence_for(profile=self.profile, sequence=sequence, observed_at=NOW),
            ),
        )
        self.assertEqual(report.state, MappingRunState.MAPPED)
        return report.candidates[0]

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
            idempotency_key=idempotency_key or f"request_{subject_ref}_{selected.id.hex[:12]}",
        )

    def _approve(self, request):
        return self.store.record_decision(
            request_id=request.id,
            decision=ApprovalDecisionKind.APPROVE,
            actor_ref="human_reviewer",
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
        self.assertEqual(publication.approved_record.state, InternalPublicationState.APPROVED_INTERNAL)
        self.assertEqual(publication.approved_record.version_no, 1)
        self.assertEqual(publication.approved_record.actor_ref, "human_reviewer")
        self.assertEqual(publication.approved_record.evidence_ref, "review_evidence_1")
        self.assertEqual(publication.approved_record.subject_ref, "subject_alpha")
        self.assertEqual(publication.approved_record.payload_hash, self.candidate.normalized_value_hash)
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
        self.assertFalse(publication.safe_summary()["p02_current_truth_readable"])

    def test_approval_module_never_imports_or_emits_p02_approved_truth(self) -> None:
        source = (ROOT / "modules" / "ingestion" / "approval.py").read_text(encoding="utf-8")

        self.assertNotIn("modules.truth_center", source)
        self.assertNotIn("TruthVersion", source)
        self.assertNotIn("DataState.APPROVED", source)

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
                    actor_ref="human_reviewer",
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
        with self.assertRaisesRegex(ApprovalBoundaryError, "self_approval_forbidden"):
            self.store.record_decision(
                request_id=request.id,
                decision=ApprovalDecisionKind.APPROVE,
                actor_ref=request.requested_by,
                evidence_ref="review_evidence_1",
                policy_version=request.policy_version,
                decided_at=NOW + timedelta(minutes=1),
                idempotency_key="self_decision",
            )
        with self.assertRaisesRegex(ApprovalBoundaryError, "approval_request_expired"):
            self.store.record_decision(
                request_id=request.id,
                decision=ApprovalDecisionKind.APPROVE,
                actor_ref="human_reviewer",
                evidence_ref="review_evidence_2",
                policy_version=request.policy_version,
                decided_at=NOW + timedelta(hours=2),
                idempotency_key="late_decision",
            )
        with self.assertRaisesRegex(ApprovalBoundaryError, "approval_policy_mismatch"):
            self.store.record_decision(
                request_id=request.id,
                decision=ApprovalDecisionKind.APPROVE,
                actor_ref="human_reviewer",
                evidence_ref="review_evidence_3",
                policy_version="approval_policy_v2",
                decided_at=NOW + timedelta(minutes=2),
                idempotency_key="wrong_policy_decision",
            )

    def test_non_quality_cross_scope_or_real_like_candidates_are_rejected(self) -> None:
        blocked_candidate = replace(self.candidate, state=MappingRunState.BLOCKED_MANUAL)
        cross_scope = replace(synthetic_scope(), correlation_id="other_correlation")

        with self.assertRaisesRegex(ApprovalBoundaryError, "quality_passed_candidate_required"):
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
        with self.assertRaisesRegex(ApprovalBoundaryError, "external_execution_forbidden"):
            self._request(candidate=unsafe_replace_frozen(self.candidate, external_execution_allowed=True))

    def test_supersede_appends_new_versions_and_refresh_event_without_external_sync(self) -> None:
        first_publication = self.publisher.publish(self._approve(self._request()))
        replacement_candidate = self._mapped_candidate(32)
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
            self.candidate.source_content_hash,
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)
        self.assertIn("internal_invalidation_outbox", rendered)


if __name__ == "__main__":
    unittest.main()
