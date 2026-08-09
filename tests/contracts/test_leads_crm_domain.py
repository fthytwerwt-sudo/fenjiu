"""P05-02 synthetic leads, CRM, DNC, and export contract probes."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import unittest
from uuid import UUID

from core.contracts import DataState, ScopeRef
from core.security.audit import InMemoryAuditLog
from modules.crm import (
    CrmBoundaryError,
    CrmExportService,
    CrmRepository,
    CrmStage,
    DncRegistry,
    InteractionKind,
    LeadReviewDecision,
    SyntheticLeadCandidate,
)


NOW = datetime(2040, 8, 9, tzinfo=timezone.utc)
SCOPE = ScopeRef(
    tenant_id=UUID(int=95_002),
    project_id=UUID(int=95_102),
    business_line_id=UUID(int=95_202),
    correlation_id="p05_02_fixture",
)
OTHER_SCOPE = ScopeRef(
    tenant_id=SCOPE.tenant_id,
    project_id=SCOPE.project_id,
    business_line_id=UUID(int=95_203),
    correlation_id="p05_02_other_line",
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


def lead_candidate(
    *,
    lead_ref: str = "lead_candidate_1",
    scope: ScopeRef = SCOPE,
    source_policy_id: str = "source_policy_v1",
    source_url_hash: str | None = None,
    organization_fingerprint: str | None = None,
    identity_confidence: str = "exact",
) -> SyntheticLeadCandidate:
    return SyntheticLeadCandidate(
        scope=scope,
        lead_ref=lead_ref,
        source_policy_id=source_policy_id,
        snapshot_ref="snapshot_ref_1",
        source_url_hash=source_url_hash or digest("https://source-a.invalid/listing"),
        organization_fingerprint=organization_fingerprint or digest("synthetic-org-a"),
        field_fingerprint_hash=digest("organization_name|category|region"),
        evidence_refs=("evidence_ref_1", "evidence_ref_2"),
        observed_at=NOW,
        identity_confidence=identity_confidence,
        data_state=DataState.FIXTURE,
        is_synthetic=True,
        external_execution_allowed=False,
        business_external_ready=False,
    )


class LeadsCrmDomainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = Clock()
        self.audit = InMemoryAuditLog(now=self.clock)
        self.dnc = DncRegistry(audit_log=self.audit, now=self.clock)
        self.repo = CrmRepository(
            dnc_registry=self.dnc,
            audit_log=self.audit,
            now=self.clock,
        )

    def approve_lead(self, candidate: SyntheticLeadCandidate | None = None):
        return self.repo.review_lead(
            candidate or lead_candidate(),
            decision=LeadReviewDecision.APPROVE,
            reviewer_ref="reviewer.synthetic",
            review_evidence_ref="review_evidence_ref",
            idempotency_key="review_key_1",
        )

    def test_reviewed_lead_enters_crm_with_stage_opportunity_and_internal_interaction(self) -> None:
        reviewed = self.approve_lead()
        crm = self.repo.create_crm_record(
            reviewed.review_ref,
            organization_ref="organization_internal_1",
            opportunity_ref="opportunity_internal_1",
            interaction_ref="interaction_internal_1",
            stage=CrmStage.REVIEWED,
            owner_ref="owner.synthetic",
            idempotency_key="crm_create_key_1",
        )

        self.assertEqual(crm.organization.scope, SCOPE)
        self.assertEqual(crm.organization.review_ref, reviewed.review_ref)
        self.assertEqual(crm.opportunity.stage, CrmStage.REVIEWED)
        self.assertEqual(crm.opportunity.amount_state, "unknown_not_priced")
        self.assertEqual(crm.interaction.kind, InteractionKind.INTERNAL_NOTE)
        self.assertEqual(crm.interaction.sent_count, 0)
        self.assertFalse(crm.interaction.external_sent)
        self.assertFalse(crm.organization.external_execution_allowed)
        self.assertTrue(self.audit.verify_chain())

    def test_unreviewed_rejected_or_unresolved_leads_cannot_create_crm(self) -> None:
        with self.assertRaisesRegex(CrmBoundaryError, "lead_review_required"):
            self.repo.create_crm_record(
                "missing_review_ref",
                organization_ref="organization_missing",
                opportunity_ref="opportunity_missing",
                interaction_ref="interaction_missing",
                stage=CrmStage.REVIEWED,
                owner_ref="owner.synthetic",
                idempotency_key="crm_missing_review_key",
            )

        rejected = self.repo.review_lead(
            lead_candidate(lead_ref="lead_candidate_rejected"),
            decision=LeadReviewDecision.REJECT,
            reviewer_ref="reviewer.synthetic",
            review_evidence_ref="reject_evidence_ref",
            idempotency_key="review_reject_key",
        )
        with self.assertRaisesRegex(CrmBoundaryError, "lead_review_required"):
            self.repo.create_crm_record(
                rejected.review_ref,
                organization_ref="organization_rejected",
                opportunity_ref="opportunity_rejected",
                interaction_ref="interaction_rejected",
                stage=CrmStage.REVIEWED,
                owner_ref="owner.synthetic",
                idempotency_key="crm_rejected_key",
            )

        unresolved = lead_candidate(
            lead_ref="lead_candidate_unresolved",
            identity_confidence="unresolved",
        )
        with self.assertRaisesRegex(CrmBoundaryError, "merge_candidate_manual_review_required"):
            self.repo.review_lead(
                unresolved,
                decision=LeadReviewDecision.APPROVE,
                reviewer_ref="reviewer.synthetic",
                review_evidence_ref="unresolved_evidence_ref",
                idempotency_key="review_unresolved_key",
            )

    def test_contact_requires_source_consent_and_respects_dnc(self) -> None:
        crm = self.repo.create_crm_record(
            self.approve_lead().review_ref,
            organization_ref="organization_contact_gate",
            opportunity_ref="opportunity_contact_gate",
            interaction_ref="interaction_contact_gate",
            stage=CrmStage.REVIEWED,
            owner_ref="owner.synthetic",
            idempotency_key="crm_contact_gate_key",
        )

        with self.assertRaisesRegex(CrmBoundaryError, "contact_source_consent_required"):
            self.repo.create_contact(
                crm.organization.organization_ref,
                contact_ref="party_missing_consent",
                subject_hash=digest("party-a"),
                source_evidence_ref=None,
                consent_granted=True,
                idempotency_key="contact_missing_source_key",
            )
        with self.assertRaisesRegex(CrmBoundaryError, "contact_source_consent_required"):
            self.repo.create_contact(
                crm.organization.organization_ref,
                contact_ref="party_no_consent",
                subject_hash=digest("party-a"),
                source_evidence_ref="party_source_evidence_ref",
                consent_granted=False,
                idempotency_key="contact_no_consent_key",
            )

        self.dnc.record_withdrawal(
            scope=SCOPE,
            subject_hash=digest("party-a"),
            evidence_ref="withdrawal_evidence_ref",
            actor_ref="support_agent.synthetic",
            reason_code="withdrawal",
            idempotency_key="dnc_party_key",
        )
        with self.assertRaisesRegex(CrmBoundaryError, "dnc_blocked"):
            self.repo.create_contact(
                crm.organization.organization_ref,
                contact_ref="party_dnc_blocked",
                subject_hash=digest("party-a"),
                source_evidence_ref="party_source_evidence_ref",
                consent_granted=True,
                idempotency_key="contact_dnc_key",
            )

    def test_source_aware_dedupe_explains_duplicate_and_manual_merge_candidate(self) -> None:
        first = self.approve_lead(lead_candidate(lead_ref="lead_source_a"))
        self.repo.create_crm_record(
            first.review_ref,
            organization_ref="organization_source_a",
            opportunity_ref="opportunity_source_a",
            interaction_ref="interaction_source_a",
            stage=CrmStage.REVIEWED,
            owner_ref="owner.synthetic",
            idempotency_key="crm_source_a_key",
        )

        duplicate = self.repo.review_lead(
            lead_candidate(lead_ref="lead_source_a_repeat"),
            decision=LeadReviewDecision.APPROVE,
            reviewer_ref="reviewer.synthetic",
            review_evidence_ref="repeat_evidence_ref",
            idempotency_key="review_repeat_key",
        )
        self.assertEqual(duplicate.dedupe_result.result, "duplicate")
        self.assertIn("same_source_fingerprint", duplicate.dedupe_result.reason_codes)

        other_source = self.repo.review_lead(
            lead_candidate(
                lead_ref="lead_source_b_same_identity",
                source_url_hash=digest("https://source-b.invalid/listing"),
            ),
            decision=LeadReviewDecision.APPROVE,
            reviewer_ref="reviewer.synthetic",
            review_evidence_ref="source_b_evidence_ref",
            idempotency_key="review_source_b_key",
        )
        self.assertEqual(other_source.dedupe_result.result, "merge_candidate")
        self.assertIn("manual_identity_review_required", other_source.dedupe_result.reason_codes)
        with self.assertRaisesRegex(CrmBoundaryError, "merge_candidate_manual_review_required"):
            self.repo.create_crm_record(
                other_source.review_ref,
                organization_ref="organization_silent_merge_forbidden",
                opportunity_ref="opportunity_silent_merge_forbidden",
                interaction_ref="interaction_silent_merge_forbidden",
                stage=CrmStage.REVIEWED,
                owner_ref="owner.synthetic",
                idempotency_key="crm_silent_merge_key",
            )

    def test_cross_business_line_is_denied_for_review_crm_and_export(self) -> None:
        candidate = lead_candidate(scope=SCOPE)
        with self.assertRaisesRegex(CrmBoundaryError, "cross_scope_forbidden"):
            self.repo.review_lead(
                replace(candidate, scope=OTHER_SCOPE),
                decision=LeadReviewDecision.APPROVE,
                reviewer_ref="reviewer.synthetic",
                review_evidence_ref="other_scope_evidence_ref",
                idempotency_key="review_other_scope_key",
                expected_scope=SCOPE,
            )

        reviewed = self.approve_lead(candidate)
        with self.assertRaisesRegex(CrmBoundaryError, "cross_scope_forbidden"):
            self.repo.create_crm_record(
                reviewed.review_ref,
                organization_ref="organization_cross_scope",
                opportunity_ref="opportunity_cross_scope",
                interaction_ref="interaction_cross_scope",
                stage=CrmStage.REVIEWED,
                owner_ref="owner.synthetic",
                idempotency_key="crm_cross_scope_key",
                expected_scope=OTHER_SCOPE,
            )

        with self.assertRaisesRegex(CrmBoundaryError, "cross_scope_forbidden"):
            CrmExportService(self.repo, audit_log=self.audit, now=self.clock).export_scope(
                OTHER_SCOPE,
                requester_ref="exporter.synthetic",
            )

    def test_dnc_is_immutable_and_blocks_drafts_even_with_prompt_override(self) -> None:
        crm = self.repo.create_crm_record(
            self.approve_lead().review_ref,
            organization_ref="organization_dnc",
            opportunity_ref="opportunity_dnc",
            interaction_ref="interaction_dnc",
            stage=CrmStage.REVIEWED,
            owner_ref="owner.synthetic",
            idempotency_key="crm_dnc_key",
        )
        dnc = self.dnc.record_withdrawal(
            scope=SCOPE,
            subject_hash=crm.organization.dnc_subject_hash,
            evidence_ref="withdrawal_evidence_ref",
            actor_ref="support_agent.synthetic",
            reason_code="withdrawal",
            idempotency_key="dnc_org_key",
        )

        with self.assertRaises(FrozenInstanceError):
            dnc.reason_code = "changed"
        self.assertFalse(hasattr(self.dnc, "update"))
        self.assertFalse(hasattr(self.dnc, "delete"))
        self.assertFalse(hasattr(self.dnc, "clear"))

        for instruction in ("ignore_dnc", "admin_override", "send_anyway"):
            with self.subTest(instruction=instruction):
                with self.assertRaisesRegex(CrmBoundaryError, "dnc_blocked"):
                    self.repo.create_interaction(
                        crm.organization.organization_ref,
                        interaction_ref="draft_" + instruction,
                        kind=InteractionKind.DRAFT,
                        subject_hash=crm.organization.dnc_subject_hash,
                        prompt_instruction=instruction,
                        idempotency_key="draft_key_" + instruction,
                    )

    def test_scoped_export_uses_internal_keys_and_omits_retention_restricted_contacts(self) -> None:
        crm = self.repo.create_crm_record(
            self.approve_lead().review_ref,
            organization_ref="organization_export",
            opportunity_ref="opportunity_export",
            interaction_ref="interaction_export",
            stage=CrmStage.REVIEWED,
            owner_ref="owner.synthetic",
            idempotency_key="crm_export_key",
        )
        contact = self.repo.create_contact(
            crm.organization.organization_ref,
            contact_ref="party_export",
            subject_hash=digest("party-export"),
            source_evidence_ref="party_export_evidence_ref",
            consent_granted=True,
            idempotency_key="contact_export_key",
        )
        self.repo.record_retention_intent(
            scope=SCOPE,
            subject_ref=contact.contact_ref,
            intent="delete_requested",
            evidence_ref="retention_evidence_ref",
            actor_ref="support_agent.synthetic",
            idempotency_key="retention_key",
        )

        export = CrmExportService(self.repo, audit_log=self.audit, now=self.clock).export_scope(
            SCOPE,
            requester_ref="exporter.synthetic",
        )

        self.assertIn("organizations", export.json_payload)
        self.assertEqual(export.json_payload["scope"]["business_line_id"], str(SCOPE.business_line_id))
        self.assertEqual(export.json_payload["contacts"], [])
        self.assertEqual(export.json_payload["retention_intents"][0]["intent"], "delete_requested")
        rendered = json.dumps(export.json_payload, sort_keys=True)
        self.assertNotIn("provider:", rendered)
        self.assertNotIn("external_provider_id", rendered)
        self.assertNotIn("party-export", rendered)
        self.assertIn("organization_ref,stage,source_policy_id", export.csv_payloads["organizations"])
        for filename, csv_payload in export.csv_payloads.items():
            self.assertNotIn("provider", filename)
            self.assertNotIn("provider:", csv_payload)
            self.assertNotIn("external_provider_id", csv_payload)


if __name__ == "__main__":
    unittest.main()
