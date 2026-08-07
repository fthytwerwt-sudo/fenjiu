"""P03-03 synthetic approval, publication, and refresh contract probes."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest
from uuid import UUID

from core.contracts import DataState, ScopeRef, synthetic_scope
from modules.ingestion.contracts import (
    ExtractionResultRecord,
    FieldLocator,
    IngestionJobRecord,
    IngestionWorkflowState,
    SourceFileRecord,
    StagingCandidateRecord,
)
from modules.ingestion.mapping import (
    AttributeStatus,
    MappingBatch,
    MappingEvidence,
    MappingProfile,
    MappingReport,
    MappingRunState,
    NormalizationDescriptor,
    QualityCode,
    SyntheticMappingEngine,
)
from modules.ingestion.approval import (
    ApprovalAction,
    ApprovalBoundaryError,
    ApprovalRequestState,
    HumanDecisionCommand,
    RefreshConsumer,
    ReviewRequestCommand,
    RiskLevel,
    SyntheticApprovalPublisher,
    SyntheticTruthStatus,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "ingestion" / "synthetic_mapping_profiles.json"
NOW = datetime(2040, 1, 2, tzinfo=timezone.utc)
SCOPE = synthetic_scope()


def load_profile(name: str = "profile_alpha") -> MappingProfile:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for profile_payload in payload["profiles"]:
        profile = MappingProfile.from_mapping(profile_payload)
        if profile.profile_id == name and profile.version == "v1":
            return profile
    raise AssertionError(f"missing profile {name}")


def evidence_for(
    *,
    profile: MappingProfile,
    sequence: int,
    scope: ScopeRef = SCOPE,
    source_field: str = "field_alpha",
    source_hash: str | None = None,
    descriptor: NormalizationDescriptor | None = None,
    observed_at: datetime = NOW,
) -> MappingEvidence:
    source_id = UUID(f"00000000-0000-4000-8000-{sequence:012d}")
    job_id = UUID(f"00000000-0000-4000-8000-{sequence + 100:012d}")
    result_id = UUID(f"00000000-0000-4000-8000-{sequence + 200:012d}")
    candidate_id = UUID(f"00000000-0000-4000-8000-{sequence + 300:012d}")
    content_hash = source_hash or f"{sequence:064x}"
    locator = FieldLocator(sheet="Sheet_1", row=sequence, cell=f"A{sequence}")
    source = SourceFileRecord(
        id=source_id,
        scope=scope,
        storage_locator=profile.synthetic_storage_locator,
        storage_locator_version="locator_v1",
        content_sha256=f"{sequence + 400:064x}",
        size_bytes=16,
        declared_mime="text/csv",
        source_kind=profile.synthetic_source_kind,
        disposition=profile.synthetic_source_disposition,
        quarantine_code=None,
        received_at=NOW,
        received_by="synthetic_actor",
    )
    job = IngestionJobRecord(
        id=job_id,
        scope=scope,
        source_file_id=source.id,
        parser_version="parser_v1",
        extractor_version="extractor_v1",
        mapping_profile_version=profile.version,
        input_signature=f"{sequence + 500:064x}",
        idempotency_key=f"approval_input_{sequence}",
        workflow_state=IngestionWorkflowState.STAGED,
    )
    result = ExtractionResultRecord(
        id=result_id,
        scope=scope,
        source_file_id=source.id,
        ingestion_job_id=job.id,
        extractor_version=job.extractor_version,
        field_name=source_field,
        content_hash=content_hash,
        locator=locator,
        confidence_basis="synthetic_fixture",
    )
    candidate = StagingCandidateRecord(
        id=candidate_id,
        scope=scope,
        source_file_id=source.id,
        ingestion_job_id=job.id,
        extraction_result_id=result.id,
        field_name=source_field,
        content_hash=content_hash,
        locator=locator,
    )
    return MappingEvidence(
        source_file=source,
        ingestion_job=job,
        extraction_result=result,
        staging_candidate=candidate,
        descriptor=descriptor or NormalizationDescriptor(),
        observed_at=observed_at,
    )


def mapped_report(
    *,
    profile: MappingProfile,
    sequence: int,
    scope: ScopeRef = SCOPE,
    source_hash: str | None = None,
    descriptor: NormalizationDescriptor | None = None,
) -> MappingReport:
    evidence = evidence_for(
        profile=profile,
        sequence=sequence,
        scope=scope,
        source_hash=source_hash,
        descriptor=descriptor,
    )
    return SyntheticMappingEngine(now=lambda: NOW).map(
        profile,
        MappingBatch(
            scope=scope,
            source_signature=profile.source_signature,
            evidence=(evidence,),
        ),
    )


def request_command(
    report: MappingReport,
    *,
    subject_ref: str = "subject_alpha",
    fact_type: str = "synthetic_fact",
    creator_actor_ref: str = "creator_actor",
    idempotency_key: str = "request_key_1",
    requested_version_no: int = 1,
    supersedes_version_id: UUID | None = None,
    expires_at: datetime | None = None,
    scope: ScopeRef = SCOPE,
) -> ReviewRequestCommand:
    return ReviewRequestCommand(
        scope=scope,
        candidate=report.candidates[0],
        mapping_report=report,
        subject_ref=subject_ref,
        fact_type=fact_type,
        creator_actor_ref=creator_actor_ref,
        requested_version_no=requested_version_no,
        risk_level=RiskLevel.HIGH,
        correlation_id=scope.correlation_id,
        idempotency_key=idempotency_key,
        requested_at=NOW,
        expires_at=expires_at or (NOW + timedelta(days=1)),
        supersedes_version_id=supersedes_version_id,
    )


def decision_command(
    request_id: UUID,
    *,
    action: ApprovalAction = ApprovalAction.APPROVE,
    actor_ref: str = "reviewer_actor",
    idempotency_key: str = "decision_key_1",
    decided_at: datetime = NOW + timedelta(minutes=1),
    revision_ref: str | None = None,
) -> HumanDecisionCommand:
    return HumanDecisionCommand(
        request_id=request_id,
        action=action,
        actor_ref=actor_ref,
        decided_at=decided_at,
        evidence_ref="approval_evidence_ref",
        policy_version="approval_policy_v1",
        correlation_id=SCOPE.correlation_id,
        idempotency_key=idempotency_key,
        revision_ref=revision_ref,
    )


class ApprovalPublishAndRefreshTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_profile()
        self.report = mapped_report(profile=self.profile, sequence=1)
        self.publisher = SyntheticApprovalPublisher(now=lambda: NOW)

    def test_positive_e2e_publishes_only_current_approved_synthetic_version_and_internal_refresh(self) -> None:
        request = self.publisher.request_review(request_command(self.report))
        decision = self.publisher.decide(decision_command(request.id))

        current = self.publisher.current(SCOPE, "synthetic_fact", "subject_alpha")
        self.assertIsNotNone(current)
        self.assertEqual(current.id, decision.published_version_id)
        self.assertEqual(current.status, SyntheticTruthStatus.APPROVED)
        self.assertEqual(current.data_state, DataState.FIXTURE)
        self.assertTrue(current.is_synthetic)
        self.assertFalse(current.external_execution_allowed)
        self.assertFalse(current.business_external_ready)
        self.assertEqual(current.mapping_report_fingerprint, self.report.run_fingerprint)
        self.assertEqual(current.mapping_profile_fingerprint, self.report.profile_fingerprint)
        self.assertEqual(current.source_file_id, self.report.candidates[0].source_file_id)
        self.assertEqual(current.staging_candidate_id, self.report.candidates[0].staging_candidate_id)
        self.assertIsNone(self.publisher.current_candidate(SCOPE, self.report.candidates[0].id))

        self.assertEqual(len(self.publisher.refresh_events), 1)
        refresh = self.publisher.refresh_events[0]
        self.assertEqual(refresh.event_type, "TruthFactsChanged")
        self.assertEqual(refresh.changed_version_id, current.id)
        self.assertEqual(
            set(refresh.consumers),
            {RefreshConsumer.CUSTOMER_SERVICE, RefreshConsumer.CONTENT_VIDEO, RefreshConsumer.CRM},
        )
        self.assertTrue(refresh.internal_invalidation_only)
        self.assertFalse(refresh.external_execution_allowed)
        self.assertFalse(refresh.business_external_ready)
        self.assertGreaterEqual(len(self.publisher.audit_events), 3)
        self.assertTrue(all(event.actor_ref for event in self.publisher.audit_events))
        self.assertEqual(
            [event.sequence for event in self.publisher.audit_events],
            list(range(1, len(self.publisher.audit_events) + 1)),
        )

    def test_reject_and_revise_append_decisions_without_publication_or_refresh(self) -> None:
        rejected = self.publisher.request_review(
            request_command(self.report, idempotency_key="request_reject")
        )
        reject_decision = self.publisher.decide(
            decision_command(
                rejected.id,
                action=ApprovalAction.REJECT,
                idempotency_key="decision_reject",
            )
        )
        revised_report = mapped_report(profile=self.profile, sequence=2, source_hash=f"{44:064x}")
        revised = self.publisher.request_review(
            request_command(
                revised_report,
                subject_ref="subject_beta",
                idempotency_key="request_revise",
            )
        )
        revise_decision = self.publisher.decide(
            decision_command(
                revised.id,
                action=ApprovalAction.REVISE,
                idempotency_key="decision_revise",
                revision_ref="revision_ref_1",
            )
        )

        self.assertEqual(reject_decision.action, ApprovalAction.REJECT)
        self.assertEqual(revise_decision.action, ApprovalAction.REVISE)
        self.assertIsNone(reject_decision.published_version_id)
        self.assertIsNone(revise_decision.published_version_id)
        self.assertEqual(self.publisher.request_state(rejected.id), ApprovalRequestState.REJECTED)
        self.assertEqual(self.publisher.request_state(revised.id), ApprovalRequestState.REVISED)
        self.assertEqual(self.publisher.approved_versions, ())
        self.assertEqual(self.publisher.refresh_events, ())
        self.assertIsNone(self.publisher.current(SCOPE, "synthetic_fact", "subject_alpha"))
        self.assertIsNone(self.publisher.current(SCOPE, "synthetic_fact", "subject_beta"))

    def test_supersede_and_revoke_invalidate_old_versions_without_rewriting_history(self) -> None:
        first_request = self.publisher.request_review(request_command(self.report))
        first_decision = self.publisher.decide(decision_command(first_request.id))
        first_version = self.publisher.current(SCOPE, "synthetic_fact", "subject_alpha")
        replacement_report = mapped_report(profile=self.profile, sequence=3, source_hash=f"{55:064x}")
        supersede_request = self.publisher.request_review(
            request_command(
                replacement_report,
                idempotency_key="request_supersede",
                requested_version_no=2,
                supersedes_version_id=first_version.id,
            )
        )
        supersede_decision = self.publisher.decide(
            decision_command(
                supersede_request.id,
                action=ApprovalAction.SUPERSEDE,
                idempotency_key="decision_supersede",
            )
        )
        second_version = self.publisher.current(SCOPE, "synthetic_fact", "subject_alpha")

        self.assertEqual(second_version.id, supersede_decision.published_version_id)
        self.assertEqual(second_version.version_no, 2)
        self.assertEqual(second_version.parent_version_id, first_version.id)
        self.assertEqual(self.publisher.version_status(first_version.id), SyntheticTruthStatus.SUPERSEDED)
        self.assertEqual(self.publisher.version_status(second_version.id), SyntheticTruthStatus.APPROVED)
        self.assertEqual(len(self.publisher.approved_versions), 2)

        revoke_decision = self.publisher.revoke(
            version_id=second_version.id,
            actor_ref="reviewer_actor",
            decided_at=NOW + timedelta(minutes=2),
            evidence_ref="revoke_evidence_ref",
            policy_version="approval_policy_v1",
            correlation_id=SCOPE.correlation_id,
            idempotency_key="decision_revoke",
        )

        self.assertEqual(revoke_decision.action, ApprovalAction.REVOKE)
        self.assertEqual(self.publisher.version_status(second_version.id), SyntheticTruthStatus.REVOKED)
        self.assertIsNone(self.publisher.current(SCOPE, "synthetic_fact", "subject_alpha"))
        self.assertEqual(len(self.publisher.approved_versions), 2)
        self.assertEqual(len(self.publisher.refresh_events), 3)

    def test_missing_evidence_failed_quality_expired_cross_scope_self_approval_and_version_conflict_fail_closed(self) -> None:
        bad_report = replace(self.report, input_evidence_ids=())
        with self.assertRaisesRegex(ApprovalBoundaryError, "mapping_evidence_required"):
            self.publisher.request_review(request_command(bad_report))

        blocked_report = mapped_report(
            profile=self.profile,
            sequence=4,
            descriptor=NormalizationDescriptor(currency=AttributeStatus.UNKNOWN),
        )
        self.assertEqual(blocked_report.state, MappingRunState.BLOCKED_MANUAL)
        self.assertIn(QualityCode.UNKNOWN_CURRENCY, {item.code for item in blocked_report.findings})
        with self.assertRaisesRegex(ApprovalBoundaryError, "quality_not_passed"):
            self.publisher.request_review(
                request_command(blocked_report, idempotency_key="request_blocked")
            )

        expired = self.publisher.request_review(
            request_command(
                mapped_report(profile=self.profile, sequence=5, source_hash=f"{56:064x}"),
                subject_ref="subject_expired",
                idempotency_key="request_expired",
                expires_at=NOW + timedelta(seconds=30),
            )
        )
        before = self.publisher.snapshot_counts()
        with self.assertRaisesRegex(ApprovalBoundaryError, "approval_request_expired"):
            self.publisher.decide(
                decision_command(expired.id, idempotency_key="decision_expired")
            )
        self.assertEqual(self.publisher.snapshot_counts(), before)

        other_scope = replace(SCOPE, business_line_id=UUID(int=SCOPE.business_line_id.int + 1), correlation_id="other_scope")
        with self.assertRaisesRegex(ApprovalBoundaryError, "cross_scope_forbidden"):
            self.publisher.request_review(
                request_command(self.report, scope=other_scope, idempotency_key="request_cross_scope")
            )

        self_owned = self.publisher.request_review(
            request_command(
                mapped_report(profile=self.profile, sequence=6, source_hash=f"{57:064x}"),
                subject_ref="subject_self",
                idempotency_key="request_self",
                creator_actor_ref="same_actor",
            )
        )
        before = self.publisher.snapshot_counts()
        with self.assertRaisesRegex(ApprovalBoundaryError, "self_approval_forbidden"):
            self.publisher.decide(
                decision_command(
                    self_owned.id,
                    actor_ref="same_actor",
                    idempotency_key="decision_self",
                )
            )
        self.assertEqual(self.publisher.snapshot_counts(), before)

        approved = self.publisher.request_review(
            request_command(
                mapped_report(profile=self.profile, sequence=7, source_hash=f"{58:064x}"),
                subject_ref="subject_conflict",
                idempotency_key="request_ok",
            )
        )
        self.publisher.decide(decision_command(approved.id, idempotency_key="decision_ok"))
        conflict = self.publisher.request_review(
            request_command(
                mapped_report(profile=self.profile, sequence=8, source_hash=f"{59:064x}"),
                subject_ref="subject_conflict",
                idempotency_key="request_conflict",
            )
        )
        before = self.publisher.snapshot_counts()
        with self.assertRaisesRegex(ApprovalBoundaryError, "publication_supersede_required"):
            self.publisher.decide(
                decision_command(conflict.id, idempotency_key="decision_conflict")
            )
        self.assertEqual(self.publisher.snapshot_counts(), before)
        self.assertIsNotNone(self.publisher.current(SCOPE, "synthetic_fact", "subject_conflict"))

    def test_idempotent_requests_and_decisions_do_not_duplicate_audit_versions_or_refresh(self) -> None:
        command = request_command(self.report)
        first_request = self.publisher.request_review(command)
        rerun_request = self.publisher.request_review(command)

        self.assertEqual(first_request, rerun_request)
        decision = decision_command(first_request.id)
        first_decision = self.publisher.decide(decision)
        rerun_decision = self.publisher.decide(decision)

        self.assertEqual(first_decision, rerun_decision)
        self.assertEqual(len(self.publisher.requests), 1)
        self.assertEqual(len(self.publisher.decisions), 1)
        self.assertEqual(len(self.publisher.approved_versions), 1)
        self.assertEqual(len(self.publisher.refresh_events), 1)
        with self.assertRaisesRegex(ApprovalBoundaryError, "duplicate_decision"):
            self.publisher.decide(
                decision_command(
                    first_request.id,
                    idempotency_key="decision_duplicate",
                )
            )
        with self.assertRaisesRegex(ApprovalBoundaryError, "idempotency_conflict"):
            self.publisher.request_review(
                request_command(
                    mapped_report(profile=self.profile, sequence=10, source_hash=f"{61:064x}"),
                    idempotency_key="request_key_1",
                )
            )
        with self.assertRaisesRegex(ApprovalBoundaryError, "idempotency_conflict"):
            self.publisher.decide(
                decision_command(
                    first_request.id,
                    action=ApprovalAction.REJECT,
                    idempotency_key="decision_key_1",
                )
            )

    def test_candidate_and_non_current_statuses_are_never_downstream_readable(self) -> None:
        request = self.publisher.request_review(request_command(self.report))
        self.assertIsNone(self.publisher.current_candidate(SCOPE, self.report.candidates[0].id))
        self.assertIsNone(self.publisher.current(SCOPE, "synthetic_fact", "subject_alpha"))
        self.publisher.decide(decision_command(request.id))
        active = self.publisher.current(SCOPE, "synthetic_fact", "subject_alpha")
        replacement = mapped_report(profile=self.profile, sequence=9, source_hash=f"{60:064x}")
        supersede_request = self.publisher.request_review(
            request_command(
                replacement,
                idempotency_key="request_next",
                requested_version_no=2,
                supersedes_version_id=active.id,
            )
        )
        self.publisher.decide(
            decision_command(
                supersede_request.id,
                action=ApprovalAction.SUPERSEDE,
                idempotency_key="decision_next",
            )
        )

        self.assertIsNone(self.publisher.read_version(active.id))
        self.assertIsNotNone(self.publisher.current(SCOPE, "synthetic_fact", "subject_alpha"))

    def test_safe_summaries_and_actor_validation_reject_real_values_paths_and_sensitive_actor_refs(self) -> None:
        request = self.publisher.request_review(request_command(self.report))
        decision = self.publisher.decide(decision_command(request.id))
        current = self.publisher.current(SCOPE, "synthetic_fact", "subject_alpha")
        rendered = json.dumps(
            {
                "request": request.safe_summary(),
                "decision": decision.safe_summary(),
                "truth": current.safe_summary(),
                "refresh": self.publisher.refresh_events[0].safe_summary(),
            },
            sort_keys=True,
        )

        for forbidden in (
            "/" + "Users" + "/",
            "raw_text",
            "body",
            "contact",
            "price",
            "inventory",
            "cookie",
            "token",
            "secret",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered.lower())
        self.assertFalse(current.external_execution_allowed)
        self.assertFalse(current.business_external_ready)
        with self.assertRaisesRegex(ApprovalBoundaryError, "sensitive_metadata_forbidden"):
            self.publisher.decide(
                decision_command(
                    request.id,
                    actor_ref="actor_token_ref",
                    idempotency_key="decision_sensitive",
                )
            )


if __name__ == "__main__":
    unittest.main()
