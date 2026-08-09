"""P05-03 internal outreach draft, approval, and zero-send probes."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import unittest
from uuid import UUID

from core.application import OutreachDraftApprovalCoordinator
from core.contracts import DataState, ScopeRef
from core.security import ActionApprovalService, ActorRole, InMemoryAuditLog, PolicyActor
from modules.crm import (
    CrmRepository,
    CrmStage,
    DncRegistry,
    LeadReviewDecision,
    OutreachDraftCommand,
    OutreachDraftService,
    OutreachDraftState,
    OutreachFactRef,
    OutreachFactStatus,
    OutreachRisk,
    SyntheticLeadCandidate,
)


NOW = datetime(2040, 8, 9, tzinfo=timezone.utc)
SCOPE = ScopeRef(
    tenant_id=UUID(int=95_503),
    project_id=UUID(int=95_603),
    business_line_id=UUID(int=95_703),
    correlation_id="p05_03_fixture",
)
OTHER_SCOPE = replace(
    SCOPE,
    business_line_id=UUID(int=95_704),
    correlation_id="p05_03_other_line",
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


def lead_candidate() -> SyntheticLeadCandidate:
    return SyntheticLeadCandidate(
        scope=SCOPE,
        lead_ref="lead_candidate_p05_03",
        source_policy_id="source_policy_v1",
        snapshot_ref="snapshot_ref_1",
        source_url_hash=digest("synthetic_source"),
        organization_fingerprint=digest("synthetic_org_p05_03"),
        field_fingerprint_hash=digest("organization_name|region"),
        evidence_refs=("source_evidence_ref",),
        observed_at=NOW,
        identity_confidence="exact",
        data_state=DataState.FIXTURE,
        is_synthetic=True,
        external_execution_allowed=False,
        business_external_ready=False,
    )


def approved_fact(
    *,
    fact_ref: str = "fact_general_1",
    version_ref: str = "version_general_1",
    fact_type: str = "general_product_fact",
    target_field: str = "safe_summary",
    status: OutreachFactStatus = OutreachFactStatus.APPROVED,
    scope: ScopeRef = SCOPE,
    expires_at: datetime | None = None,
) -> OutreachFactRef:
    return OutreachFactRef(
        scope=scope,
        fact_ref=fact_ref,
        version_ref=version_ref,
        fact_type=fact_type,
        subject_ref="subject_synthetic_product",
        target_field=target_field,
        version_no=1,
        observed_at=NOW - timedelta(minutes=5),
        expires_at=expires_at or (NOW + timedelta(days=1)),
        evidence_refs=("approval_evidence_ref",),
        policy_version="approval_policy_v1",
        status=status,
        data_state=DataState.FIXTURE,
        is_synthetic=True,
        external_execution_allowed=False,
        business_external_ready=False,
    )


class OutreachDraftZeroSendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = Clock()
        self.audit = InMemoryAuditLog(now=self.clock)
        self.dnc = DncRegistry(audit_log=self.audit, now=self.clock)
        self.crm = CrmRepository(dnc_registry=self.dnc, audit_log=self.audit, now=self.clock)
        reviewed = self.crm.review_lead(
            lead_candidate(),
            decision=LeadReviewDecision.APPROVE,
            reviewer_ref="reviewer.synthetic",
            review_evidence_ref="review_evidence_ref",
            idempotency_key="review_key_p05_03",
        )
        self.record_set = self.crm.create_crm_record(
            reviewed.review_ref,
            organization_ref="organization_p05_03",
            opportunity_ref="opportunity_p05_03",
            interaction_ref="interaction_seed_p05_03",
            stage=CrmStage.REVIEWED,
            owner_ref="owner.synthetic",
            idempotency_key="crm_key_p05_03",
        )
        self.service = OutreachDraftService(
            crm_repository=self.crm,
            dnc_registry=self.dnc,
            audit_log=self.audit,
            now=self.clock,
        )
        self.approval_coordinator = OutreachDraftApprovalCoordinator(
            dnc_registry=self.dnc,
            now=self.clock,
        )

    def command(self, **overrides: object) -> OutreachDraftCommand:
        values = {
            "scope": SCOPE,
            "organization_ref": self.record_set.organization.organization_ref,
            "subject_hash": self.record_set.organization.dnc_subject_hash,
            "template_ref": "template_p05_03",
            "template_version": "v1",
            "fact_refs": (approved_fact(),),
            "policy_version": "outreach_policy_v1",
            "consent_evidence_ref": "consent_evidence_ref",
            "requested_by": "support_agent.synthetic",
            "risk_level": OutreachRisk.LOW,
            "idempotency_key": "draft_key_p05_03",
        }
        values.update(overrides)
        return OutreachDraftCommand(**values)

    def test_approved_synthetic_facts_render_editable_draft_with_fact_policy_lock_and_zero_send_proof(self) -> None:
        receipt = self.service.prepare_draft(self.command())

        self.assertIsNone(receipt.manual_handoff)
        self.assertIsNotNone(receipt.draft)
        draft = receipt.draft
        self.assertEqual(draft.state, OutreachDraftState.DRAFT_ONLY)
        self.assertEqual(draft.policy_version, "outreach_policy_v1")
        self.assertEqual(draft.fact_locks[0].version_ref, "version_general_1")
        self.assertEqual(draft.template_version, "v1")
        self.assertTrue(draft.editable_by_human)
        self.assertEqual(draft.external_send_attempts, 0)
        self.assertFalse(draft.external_execution_allowed)
        self.assertEqual(receipt.zero_send_proof.external_send_attempts, 0)
        self.assertFalse(receipt.zero_send_proof.external_execution_allowed)
        self.assertFalse(receipt.zero_send_proof.send_port_present)
        self.assertFalse(receipt.zero_send_proof.provider_endpoint_present)
        self.assertFalse(receipt.zero_send_proof.external_recipient_present)
        self.assertTrue(self.audit.verify_chain())

        rendered = json.dumps(draft.safe_summary(), sort_keys=True)
        self.assertIn("commercial_terms_confirmation_required", rendered)
        self.assertIn("inventory_confirmation_required", rendered)
        self.assertNotIn("recipient", rendered.lower())
        self.assertNotIn("provider", rendered.lower())

    def test_dnc_missing_consent_expired_conflict_cross_scope_and_high_risk_return_manual_handoff_only(self) -> None:
        blocked_cases = []
        self.dnc.record_withdrawal(
            scope=SCOPE,
            subject_hash=self.record_set.organization.dnc_subject_hash,
            evidence_ref="withdrawal_evidence_ref",
            actor_ref="support_agent.synthetic",
            reason_code="withdrawal",
            idempotency_key="dnc_p05_03_key",
        )
        blocked_cases.append(("dnc_blocked", self.command(idempotency_key="draft_dnc_key")))
        blocked_cases.append(
            (
                "consent_required",
                self.command(
                    consent_evidence_ref=None,
                    subject_hash=digest("not_dnc_subject"),
                    idempotency_key="draft_no_consent_key",
                ),
            )
        )
        blocked_cases.append(
            (
                "fact_stale",
                self.command(
                    fact_refs=(approved_fact(expires_at=NOW - timedelta(seconds=1)),),
                    subject_hash=digest("not_dnc_subject_2"),
                    idempotency_key="draft_stale_fact_key",
                ),
            )
        )
        blocked_cases.append(
            (
                "fact_not_approved",
                self.command(
                    fact_refs=(approved_fact(status=OutreachFactStatus.CONFLICT),),
                    subject_hash=digest("not_dnc_subject_3"),
                    idempotency_key="draft_conflict_fact_key",
                ),
            )
        )
        blocked_cases.append(
            (
                "cross_scope_forbidden",
                self.command(
                    fact_refs=(approved_fact(scope=OTHER_SCOPE),),
                    subject_hash=digest("not_dnc_subject_4"),
                    idempotency_key="draft_cross_scope_fact_key",
                ),
            )
        )
        blocked_cases.append(
            (
                "manual_review_required",
                self.command(
                    risk_level=OutreachRisk.HIGH,
                    subject_hash=digest("not_dnc_subject_5"),
                    idempotency_key="draft_high_risk_key",
                ),
            )
        )

        for expected_reason, command in blocked_cases:
            with self.subTest(expected_reason=expected_reason):
                receipt = self.service.prepare_draft(command)
                self.assertIsNone(receipt.draft)
                self.assertIsNotNone(receipt.manual_handoff)
                self.assertEqual(receipt.manual_handoff.reason_code, expected_reason)
                self.assertEqual(receipt.zero_send_proof.external_send_attempts, 0)
                self.assertFalse(receipt.zero_send_proof.external_execution_allowed)
                self.assertFalse(receipt.zero_send_proof.send_port_present)

    def test_approval_is_internal_and_policy_or_fact_change_invalidates_without_send(self) -> None:
        receipt = self.service.prepare_draft(self.command(idempotency_key="draft_approval_key"))
        draft = receipt.draft
        approvals = ActionApprovalService(now=self.clock)
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

        request = self.approval_coordinator.request_approval(
            draft,
            approval_service=approvals,
            creator=creator,
            expires_at=NOW + timedelta(days=1),
            idempotency_key="approval_request_p05_03",
        )
        approved = self.approval_coordinator.approve_draft(
            draft,
            approval_service=approvals,
            request_id=request.id,
            reviewer=reviewer,
            evidence_ref="draft_review_evidence_ref",
            idempotency_key="approval_decision_p05_03",
        )

        self.assertEqual(approved.state, OutreachDraftState.APPROVED_INTERNAL)
        self.assertEqual(approved.external_send_attempts, 0)
        self.assertFalse(approved.external_execution_allowed)
        self.assertFalse(self.service.zero_send_proof().send_port_present)

        fact_invalidated = self.service.invalidate_on_fact_change(
            approved,
            invalidated_version_refs=("version_general_1",),
            current_policy_version="outreach_policy_v1",
        )
        self.assertEqual(fact_invalidated.state, OutreachDraftState.INVALIDATED)
        self.assertEqual(fact_invalidated.invalidation_reason, "fact_version_invalidated")
        self.assertEqual(fact_invalidated.external_send_attempts, 0)

        policy_invalidated = self.service.invalidate_on_fact_change(
            approved,
            invalidated_version_refs=(),
            current_policy_version="outreach_policy_v2",
        )
        self.assertEqual(policy_invalidated.state, OutreachDraftState.INVALIDATED)
        self.assertEqual(policy_invalidated.invalidation_reason, "policy_version_changed")

    def test_no_send_port_or_external_endpoint_is_publicly_callable(self) -> None:
        receipt = self.service.prepare_draft(self.command(idempotency_key="draft_no_port_key"))
        proof = receipt.zero_send_proof
        public_names = {
            name for name in dir(self.service) if not name.startswith("_")
        }

        self.assertNotIn("send", public_names)
        self.assertNotIn("send_port", public_names)
        self.assertNotIn("provider_endpoint", public_names)
        self.assertEqual(proof.external_send_attempts, 0)
        self.assertFalse(proof.external_execution_allowed)
        self.assertFalse(proof.send_port_present)
        self.assertFalse(proof.provider_endpoint_present)
        self.assertFalse(proof.external_recipient_present)
        self.assertEqual(receipt.draft.safe_summary()["external_send_attempts"], 0)


if __name__ == "__main__":
    unittest.main()
