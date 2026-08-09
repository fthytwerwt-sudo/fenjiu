"""P06-03 fake support adapter, human takeover, and zero-send E2E probes."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import unittest
from uuid import UUID

from apps.admin import SupportAdminConsole, SupportAdminDecisionCommand, SupportAdminResumeCommand
from adapters.support import FakeSupportPort, SupportInboundEnvelope
from core.application import SupportDraftApprovalCoordinator, SupportTakeoverWorkflow
from core.contracts import DataState, ScopeRef
from core.security import ActionApprovalService, ActorRole, InMemoryAuditLog, PolicyActor
from modules.customer_service import (
    ApprovedFactRef,
    FactApprovalState,
    FakeDraftModel,
    ForbiddenExpressionPolicy,
    HumanDecision,
    InMemoryApprovedFactQuery,
    RiskLevel,
    SupportCaseState,
    SupportDisposition,
    SupportDraftPipeline,
    SupportPolicySnapshot,
    SupportTakeoverBoundaryError,
)


NOW = datetime(2040, 8, 10, tzinfo=timezone.utc)
SCOPE = ScopeRef(
    tenant_id=UUID(int=96_003),
    project_id=UUID(int=96_103),
    business_line_id=UUID(int=96_203),
    correlation_id="p06_03_fixture",
)
SUPPORT_DRAFT_FLAGS = (
    ("external_send_enabled", True),
    ("content_publish_enabled", False),
    ("price_quote_enabled", False),
    ("refund_enabled", False),
    ("order_enabled", False),
    ("payment_enabled", False),
    ("inventory_write_enabled", False),
    ("real_crawl_enabled", False),
    ("real_video_provider_enabled", False),
    ("external_execution_allowed", False),
    ("business_external_ready", False),
)


class Clock:
    def __init__(self) -> None:
        self.current = NOW

    def __call__(self) -> datetime:
        result = self.current
        self.current = self.current + timedelta(seconds=1)
        return result


def digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def uuid_tail(value: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{value:012d}")


def envelope(
    *,
    raw_external_message_id: str = "message_one",
    body_text: str = "synthetic support question",
    intent_label: str = "faq_general",
    risk_level: RiskLevel = RiskLevel.LOW,
    dnc_blocked: bool = False,
    personal_data_detected: bool = False,
) -> SupportInboundEnvelope:
    return SupportInboundEnvelope(
        scope=SCOPE,
        channel_ref="channel:tiktok.synthetic",
        raw_external_conversation_id="conversation_one",
        raw_external_message_id=raw_external_message_id,
        received_at=NOW,
        received_by="synthetic_channel",
        body_text=body_text,
        content_ref=f"ref:content:{raw_external_message_id}",
        intent_label=intent_label,
        risk_level=risk_level,
        retention_policy_ref="retention_policy:p06_03_synthetic",
        consent_ref="consent:synthetic_present",
        dnc_blocked=dnc_blocked,
        personal_data_detected=personal_data_detected,
        policy_version="support_contract_v3",
        idempotency_key=f"inbound:{raw_external_message_id}",
    )


def fact(
    *,
    approval_state: FactApprovalState = FactApprovalState.APPROVED,
    expires_at: datetime | None = None,
    version_tail: int = 6301,
) -> ApprovedFactRef:
    return ApprovedFactRef(
        scope=SCOPE,
        fact_ref="fact.synthetic.faq_general",
        fact_type="faq_general",
        subject_ref="subject.synthetic.faq",
        version_id=uuid_tail(version_tail),
        version_no=1,
        approval_state=approval_state,
        data_state=DataState.FIXTURE,
        observed_at=NOW - timedelta(minutes=5),
        expires_at=expires_at or (NOW + timedelta(hours=1)),
        source_ref="source.synthetic.approved",
        evidence_ref="evidence.synthetic.approved",
        value_hash=digest("synthetic approved faq"),
        policy_version="fact_policy_v1",
        is_synthetic=True,
        external_execution_allowed=False,
    )


def policy_snapshot() -> SupportPolicySnapshot:
    return SupportPolicySnapshot(
        scope=SCOPE,
        subject_hash=digest("synthetic support subject"),
        source_evidence_ref="source_evidence:synthetic_support",
        consent_ref="consent:synthetic_present",
        consent_granted=True,
        dnc_blocked=False,
        feature_flag_snapshot=SUPPORT_DRAFT_FLAGS,
        policy_version="p04_support_policy_snapshot_v1",
        observed_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
        is_synthetic=True,
        external_execution_allowed=False,
    )


def draft_pipeline(*, fact_query: InMemoryApprovedFactQuery | None = None) -> SupportDraftPipeline:
    return SupportDraftPipeline(
        fact_query=fact_query or InMemoryApprovedFactQuery((fact(),)),
        model=FakeDraftModel(outputs={"faq_general": "synthetic draft answer"}),
        forbidden_policy=ForbiddenExpressionPolicy(
            scope=SCOPE,
            locale="en",
            policy_version="support_forbidden_v1",
            denied_tokens=("forbidden_claim",),
            observed_at=NOW - timedelta(minutes=5),
            expires_at=NOW + timedelta(hours=1),
            is_synthetic=True,
            external_execution_allowed=False,
        ),
        now=Clock(),
    )


class SupportAdapterTakeoverE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = Clock()
        self.adapter = FakeSupportPort(now=self.clock)
        self.admin = SupportAdminConsole()
        self.audit = InMemoryAuditLog(now=self.clock)
        self.workflow = SupportTakeoverWorkflow(audit_log=self.audit, now=self.clock)
        self.approvals = ActionApprovalService(now=self.clock)
        self.coordinator = SupportDraftApprovalCoordinator(now=self.clock)

    def prepare_low_risk_case(self, *, raw_external_message_id: str = "message_one"):
        receipt = self.adapter.receive(envelope(raw_external_message_id=raw_external_message_id))
        outcome = draft_pipeline().prepare(
            receipt,
            locale="en",
            policy_snapshot=policy_snapshot(),
            subject_ref="subject.synthetic.faq",
            original_text="synthetic support question",
            translated_text="synthetic support question",
            translation_ref="translation.synthetic.p06_03",
            translation_model_ref="fake_translation_model_v1",
            template_version="support_template_v1",
        )
        return self.workflow.open_case(receipt, outcome, actor_ref="support_worker.synthetic")

    def test_fake_receive_to_human_approved_draft_is_internal_and_zero_send(self) -> None:
        case_receipt = self.prepare_low_risk_case()
        case = case_receipt.case

        self.assertEqual(case.state, SupportCaseState.DRAFT_ONLY)
        self.assertEqual(case.external_send_attempts, 0)
        self.assertFalse(case.external_execution_allowed)
        self.assertTrue(case.automation_paused)
        self.assertIsNotNone(case.draft_ref)
        self.assertEqual(case_receipt.zero_send_proof.external_send_attempts, 0)
        self.assertFalse(case_receipt.zero_send_proof.send_approved_present)

        creator = PolicyActor(
            actor_ref="support_creator.synthetic",
            role=ActorRole.SUPPORT_AGENT,
            scope=SCOPE,
        )
        reviewer = PolicyActor(
            actor_ref="support_reviewer.synthetic",
            role=ActorRole.SUPPORT_AGENT,
            scope=SCOPE,
        )
        request = self.coordinator.request_approval(
            case,
            approval_service=self.approvals,
            creator=creator,
            expires_at=NOW + timedelta(hours=1),
            idempotency_key="support_approval_request",
        )
        approved = self.coordinator.approve_case(
            case,
            workflow=self.workflow,
            approval_service=self.approvals,
            request_id=request.id,
            reviewer=reviewer,
            evidence_ref="support_review_evidence_ref",
            idempotency_key="support_approval_decision",
        )

        self.assertEqual(approved.state, SupportCaseState.HUMAN_APPROVED_INTERNAL)
        self.assertEqual(approved.external_send_attempts, 0)
        self.assertFalse(approved.external_execution_allowed)
        self.assertEqual(self.workflow.zero_send_proof().external_send_attempts, 0)
        self.assertTrue(self.audit.verify_chain())

        rendered = json.dumps(approved.safe_summary(), sort_keys=True)
        self.assertNotIn("synthetic support question", rendered)
        self.assertNotIn("synthetic draft answer", rendered)
        self.assertNotIn("body_text", rendered)
        self.assertNotIn("prompt", rendered.lower())

    def test_replay_returns_same_case_without_duplicate_audit_or_send(self) -> None:
        first_receipt = self.adapter.receive(envelope(raw_external_message_id="replay"))
        first_outcome = draft_pipeline().prepare(
            first_receipt,
            locale="en",
            policy_snapshot=policy_snapshot(),
            subject_ref="subject.synthetic.faq",
            original_text="synthetic replay question",
            translated_text="synthetic replay question",
            translation_ref="translation.synthetic.replay",
            translation_model_ref="fake_translation_model_v1",
            template_version="support_template_v1",
        )
        first_case = self.workflow.open_case(
            first_receipt,
            first_outcome,
            actor_ref="support_worker.synthetic",
        )
        audit_count = self.audit.snapshot_counts()["audit_events"]

        replay_receipt = self.adapter.receive(envelope(raw_external_message_id="replay"))
        replay_case = self.workflow.open_case(
            replay_receipt,
            first_outcome,
            actor_ref="support_worker.synthetic",
        )

        self.assertTrue(replay_receipt.replayed)
        self.assertTrue(replay_case.replayed)
        self.assertEqual(replay_case.case.case_ref, first_case.case.case_ref)
        self.assertEqual(self.audit.snapshot_counts()["audit_events"], audit_count)
        self.assertEqual(self.workflow.zero_send_proof().external_send_attempts, 0)

    def test_dnc_pii_and_high_risk_force_manual_handoff_before_draft(self) -> None:
        private_contact = "person" + "@" + "example.invalid"
        blocked = (
            ("dnc_blocked", envelope(raw_external_message_id="dnc", dnc_blocked=True)),
            (
                "privacy_review_required",
                envelope(
                    raw_external_message_id="privacy",
                    body_text=f"synthetic private contact {private_contact}",
                    personal_data_detected=True,
                ),
            ),
            (
                "risk_policy_manual_required",
                envelope(raw_external_message_id="risk", intent_label="price", risk_level=RiskLevel.LOW),
            ),
            (
                "high_risk",
                envelope(raw_external_message_id="high", risk_level=RiskLevel.HIGH),
            ),
        )

        for expected_reason, inbound in blocked:
            with self.subTest(expected_reason=expected_reason):
                receipt = self.adapter.receive(inbound)
                outcome = draft_pipeline().prepare(
                    receipt,
                    locale="en",
                    policy_snapshot=policy_snapshot(),
                    subject_ref="subject.synthetic.faq",
                    original_text="synthetic blocked question",
                    translated_text="synthetic blocked question",
                    translation_ref=f"translation.synthetic.{expected_reason}",
                    translation_model_ref="fake_translation_model_v1",
                    template_version="support_template_v1",
                )
                case = self.workflow.open_case(
                    receipt,
                    outcome,
                    actor_ref="support_worker.synthetic",
                ).case

                self.assertEqual(case.state, SupportCaseState.MANUAL_HANDOFF)
                self.assertEqual(case.handoff_reason_code, expected_reason)
                self.assertIsNone(case.draft_ref)
                self.assertEqual(case.external_send_attempts, 0)

        rendered = json.dumps(self.workflow.safe_case_summaries(), sort_keys=True)
        self.assertNotIn(private_contact, rendered)

    def test_fact_invalidations_and_bad_fact_states_fail_closed_without_send(self) -> None:
        cases = (
            ("approved_fact_expired", InMemoryApprovedFactQuery((fact(expires_at=NOW - timedelta(seconds=1)),))),
            ("approved_fact_revoked", InMemoryApprovedFactQuery((fact(approval_state=FactApprovalState.REVOKED),))),
            ("approved_fact_conflict", InMemoryApprovedFactQuery((fact(approval_state=FactApprovalState.CONFLICT),))),
            ("approved_fact_missing", InMemoryApprovedFactQuery(())),
        )
        for expected_reason, fact_query in cases:
            with self.subTest(expected_reason=expected_reason):
                receipt = self.adapter.receive(envelope(raw_external_message_id=expected_reason))
                outcome = draft_pipeline(fact_query=fact_query).prepare(
                    receipt,
                    locale="en",
                    policy_snapshot=policy_snapshot(),
                    subject_ref="subject.synthetic.faq",
                    original_text="synthetic fact gate question",
                    translated_text="synthetic fact gate question",
                    translation_ref=f"translation.synthetic.{expected_reason}",
                    translation_model_ref="fake_translation_model_v1",
                    template_version="support_template_v1",
                )
                case = self.workflow.open_case(
                    receipt,
                    outcome,
                    actor_ref="support_worker.synthetic",
                ).case
                self.assertEqual(case.state, SupportCaseState.MANUAL_HANDOFF)
                self.assertEqual(case.handoff_reason_code, expected_reason)
                self.assertEqual(case.external_send_attempts, 0)

        ready = self.prepare_low_risk_case().case
        invalidated = self.workflow.invalidate_on_fact_change(
            ready.case_ref,
            invalidated_version_ids=(str(uuid_tail(6301)),),
            current_policy_version=ready.policy_version,
            actor_ref="support_worker.synthetic",
        )

        self.assertEqual(invalidated.state, SupportCaseState.INVALIDATED)
        self.assertEqual(invalidated.invalidation_reason, "fact_version_invalidated")
        self.assertEqual(invalidated.external_send_attempts, 0)
        with self.assertRaises(SupportTakeoverBoundaryError):
            self.workflow.apply_human_decision(
                invalidated.case_ref,
                action=HumanDecision.APPROVE,
                actor_ref="support_reviewer.invalidated",
                evidence_ref="invalidated_evidence_ref",
                idempotency_key="decision_invalidated_approve",
            )

    def test_human_reject_revise_and_explicit_resume_are_audited_without_auto_send(self) -> None:
        rejected = self.admin.apply_decision(
            self.workflow,
            SupportAdminDecisionCommand(
                case_ref=self.prepare_low_risk_case(raw_external_message_id="reject_case").case.case_ref,
                action=HumanDecision.REJECT,
                actor_ref="support_reviewer.reject",
                evidence_ref="reject_evidence_ref",
                idempotency_key="decision_reject",
            ),
        )
        self.assertEqual(rejected.state, SupportCaseState.HUMAN_REJECTED)

        revised = self.workflow.apply_human_decision(
            self.prepare_low_risk_case(raw_external_message_id="revise_case").case.case_ref,
            action=HumanDecision.REVISE,
            actor_ref="support_reviewer.revise",
            evidence_ref="revise_evidence_ref",
            revision_ref="revision_ref_1",
            idempotency_key="decision_revise",
        )
        self.assertEqual(revised.state, SupportCaseState.HUMAN_REVISED)

        resumed = self.admin.resume_case(
            self.workflow,
            SupportAdminResumeCommand(
                case_ref=revised.case_ref,
                actor_ref="support_reviewer.resume",
                evidence_ref="resume_evidence_ref",
                idempotency_key="decision_resume",
            ),
        )
        self.assertEqual(resumed.state, SupportCaseState.RESUMED_INTERNAL)
        self.assertEqual(resumed.external_send_attempts, 0)
        self.assertFalse(resumed.external_execution_allowed)
        self.assertTrue(resumed.automation_paused)
        event_kinds = [event.event_kind for event in self.audit.events]
        self.assertEqual(event_kinds.count("support_case_opened"), 2)
        self.assertEqual(event_kinds.count("support_human_decision"), 2)
        self.assertEqual(event_kinds.count("support_resume_recorded"), 1)
        self.assertTrue(self.audit.verify_chain())

    def test_no_send_approved_or_sender_surface_exists(self) -> None:
        public_adapter = {name for name in dir(self.adapter) if not name.startswith("_")}
        public_workflow = {name for name in dir(self.workflow) if not name.startswith("_")}

        for forbidden in ("send", "send_approved", "sender", "provider_endpoint"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, public_adapter)
                self.assertNotIn(forbidden, public_workflow)

        proof = self.workflow.zero_send_proof()
        self.assertEqual(proof.external_send_attempts, 0)
        self.assertFalse(proof.send_approved_present)
        self.assertFalse(proof.provider_endpoint_present)


if __name__ == "__main__":
    unittest.main()
