"""P06-02 approved-fact retrieval, risk policy, and draft contract probes."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import unittest
from uuid import UUID

from core.contracts import DataState, synthetic_scope
from modules.customer_service.contracts import (
    InMemoryConversationStore,
    InboundMessageCommand,
    RiskLevel,
    ScopeStatus,
)
from modules.customer_service.drafts import (
    ApprovedFactRef,
    DraftBoundaryError,
    DraftDisposition,
    FactApprovalState,
    FakeDraftModel,
    ForbiddenExpressionPolicy,
    InMemoryApprovedFactQuery,
    SupportDraftPipeline,
)


NOW = datetime(2040, 8, 9, tzinfo=timezone.utc)
SCOPE = synthetic_scope()


class Clock:
    def __init__(self) -> None:
        self.current = NOW

    def __call__(self) -> datetime:
        result = self.current
        self.current = self.current + timedelta(seconds=1)
        return result


def uuid_tail(value: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{value:012d}")


def inbound_command(
    *,
    intent_label: str = "faq_general",
    risk_level: RiskLevel = RiskLevel.LOW,
    body_text: str = "synthetic general question",
    message_ref_suffix: str = "general",
) -> InboundMessageCommand:
    return InboundMessageCommand(
        scope=SCOPE,
        scope_status=ScopeStatus.KNOWN,
        channel_ref="channel:tiktok.synthetic",
        external_conversation_ref="ref:conversation:synthetic",
        external_message_ref=f"ref:message:{message_ref_suffix}",
        received_at=NOW,
        received_by="synthetic_channel",
        body_text=body_text,
        content_ref=f"ref:content:{message_ref_suffix}",
        intent_label=intent_label,
        risk_level=risk_level,
        retention_policy_ref="retention_policy:p06_synthetic",
        consent_ref="consent:synthetic_present",
        dnc_blocked=False,
        personal_data_detected=False,
        policy_version="support_contract_v2",
        idempotency_key=f"message_key_{message_ref_suffix}",
    )


def receipt_for(
    *,
    intent_label: str = "faq_general",
    risk_level: RiskLevel = RiskLevel.LOW,
    body_text: str = "synthetic general question",
    message_ref_suffix: str = "general",
):
    store = InMemoryConversationStore(now=Clock())
    return store.receive(
        inbound_command(
            intent_label=intent_label,
            risk_level=risk_level,
            body_text=body_text,
            message_ref_suffix=message_ref_suffix,
        )
    )


def fact(
    *,
    fact_type: str = "faq_general",
    subject_ref: str = "subject.synthetic.faq",
    version_tail: int = 6101,
    approval_state: FactApprovalState = FactApprovalState.APPROVED,
    observed_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> ApprovedFactRef:
    return ApprovedFactRef(
        scope=SCOPE,
        fact_ref=f"fact.synthetic.{fact_type}",
        fact_type=fact_type,
        subject_ref=subject_ref,
        version_id=uuid_tail(version_tail),
        version_no=1,
        approval_state=approval_state,
        data_state=DataState.FIXTURE,
        observed_at=observed_at or (NOW - timedelta(minutes=5)),
        expires_at=expires_at or (NOW + timedelta(hours=1)),
        source_ref="source.synthetic.approved",
        evidence_ref="evidence.synthetic.approved",
        value_hash="a" * 64,
        policy_version="fact_policy_v1",
        is_synthetic=True,
        external_execution_allowed=False,
    )


def forbidden_policy(*, denied_tokens: tuple[str, ...] = ("forbidden_claim",)) -> ForbiddenExpressionPolicy:
    return ForbiddenExpressionPolicy(
        scope=SCOPE,
        locale="en",
        policy_version="support_forbidden_v1",
        denied_tokens=denied_tokens,
        observed_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
        is_synthetic=True,
        external_execution_allowed=False,
    )


def pipeline(
    *,
    facts: tuple[ApprovedFactRef, ...] = (fact(),),
    model: FakeDraftModel | None = None,
    policy: ForbiddenExpressionPolicy | None = None,
) -> SupportDraftPipeline:
    return SupportDraftPipeline(
        fact_query=InMemoryApprovedFactQuery(facts),
        model=model or FakeDraftModel(
            outputs={"faq_general": "synthetic reviewable answer"}
        ),
        forbidden_policy=policy or forbidden_policy(),
        now=Clock(),
    )


class CustomerServiceFactRiskDraftTests(unittest.TestCase):
    def test_low_risk_synthetic_faq_generates_reviewable_draft_with_fact_lock_and_hash_only_refs(self) -> None:
        receipt = receipt_for(body_text="synthetic question that should not persist")

        outcome = pipeline().prepare(
            receipt,
            locale="en",
            subject_ref="subject.synthetic.faq",
            original_text="synthetic question that should not persist",
            translated_text="synthetic translated question",
            translation_ref="translation.synthetic.v1",
            translation_model_ref="fake_translation_model_v1",
            template_version="support_template_v1",
        )

        self.assertEqual(outcome.disposition, DraftDisposition.DRAFT_READY)
        self.assertIsNotNone(outcome.draft)
        self.assertIsNone(outcome.handoff)
        self.assertFalse(outcome.draft.external_execution_allowed)
        self.assertFalse(outcome.draft.send_allowed)
        self.assertFalse(outcome.draft.truth_write_allowed)
        self.assertFalse(outcome.draft.approval_write_allowed)
        self.assertEqual(outcome.draft.fact_locks[0].version_id, uuid_tail(6101))
        self.assertEqual(outcome.draft.locale, "en")
        self.assertEqual(outcome.draft.translation_ref, "translation.synthetic.v1")
        self.assertEqual(outcome.draft.model_ref, "fake_model:support_draft_v1")

        rendered = json.dumps(outcome.safe_summary(), sort_keys=True)
        for forbidden_fragment in (
            "synthetic question that should not persist",
            "synthetic translated question",
            "synthetic reviewable answer",
            '"original_text"',
            '"translated_text"',
            "output_text",
            "prompt_text",
        ):
            self.assertNotIn(forbidden_fragment, rendered)

    def test_risk_policy_forces_handoff_before_fact_query_or_model_for_business_gate_intents(self) -> None:
        high_risk_intents = (
            "price",
            "inventory",
            "delivery",
            "alcohol_purchase",
            "quote",
            "refund",
            "complaint",
            "quality",
            "credit_terms",
            "exclusive",
            "order",
            "payment",
            "unknown",
        )

        for intent_label in high_risk_intents:
            with self.subTest(intent=intent_label):
                fact_query = InMemoryApprovedFactQuery((fact(fact_type=intent_label),))
                model = FakeDraftModel(outputs={intent_label: "synthetic answer"})
                outcome = SupportDraftPipeline(
                    fact_query=fact_query,
                    model=model,
                    forbidden_policy=forbidden_policy(),
                    now=Clock(),
                ).prepare(
                    receipt_for(
                        intent_label=intent_label,
                        risk_level=RiskLevel.LOW,
                        message_ref_suffix=intent_label,
                    ),
                    locale="en",
                    subject_ref="subject.synthetic.faq",
                    original_text=f"synthetic {intent_label} question",
                    translated_text=f"synthetic {intent_label} question",
                    translation_ref=f"translation.synthetic.{intent_label}",
                    translation_model_ref="fake_translation_model_v1",
                    template_version="support_template_v1",
                )

                self.assertEqual(outcome.disposition, DraftDisposition.HANDOFF_REQUIRED)
                self.assertEqual(outcome.handoff.reason_code, "risk_policy_manual_required")
                self.assertIsNone(outcome.draft)
                self.assertEqual(fact_query.call_count, 0)
                self.assertEqual(model.call_count, 0)

    def test_missing_expired_revoked_or_conflict_fact_and_retrieval_failure_are_handoff_only(self) -> None:
        cases = (
            ("approved_fact_missing", InMemoryApprovedFactQuery(())),
            (
                "approved_fact_expired",
                InMemoryApprovedFactQuery((fact(expires_at=NOW - timedelta(seconds=1)),)),
            ),
            (
                "approved_fact_revoked",
                InMemoryApprovedFactQuery((fact(approval_state=FactApprovalState.REVOKED),)),
            ),
            (
                "approved_fact_conflict",
                InMemoryApprovedFactQuery((fact(approval_state=FactApprovalState.CONFLICT),)),
            ),
            ("fact_retrieval_failed", InMemoryApprovedFactQuery((), fail_code="fact_retrieval_failed")),
        )

        for reason_code, fact_query in cases:
            with self.subTest(reason=reason_code):
                outcome = SupportDraftPipeline(
                    fact_query=fact_query,
                    model=FakeDraftModel(outputs={"faq_general": "synthetic answer"}),
                    forbidden_policy=forbidden_policy(),
                    now=Clock(),
                ).prepare(
                    receipt_for(message_ref_suffix=reason_code),
                    locale="en",
                    subject_ref="subject.synthetic.faq",
                    original_text="synthetic low risk question",
                    translated_text="synthetic low risk question",
                    translation_ref=f"translation.synthetic.{reason_code}",
                    translation_model_ref="fake_translation_model_v1",
                    template_version="support_template_v1",
                )

                self.assertEqual(outcome.disposition, DraftDisposition.HANDOFF_REQUIRED)
                self.assertEqual(outcome.handoff.reason_code, reason_code)
                self.assertIsNone(outcome.draft)

    def test_model_failure_and_forbidden_expression_force_handoff_without_raw_output_storage(self) -> None:
        model_failure = pipeline(
            model=FakeDraftModel(outputs={}, fail_code="model_generation_failed")
        ).prepare(
            receipt_for(message_ref_suffix="model_failure"),
            locale="en",
            subject_ref="subject.synthetic.faq",
            original_text="synthetic low risk question",
            translated_text="synthetic low risk question",
            translation_ref="translation.synthetic.model_failure",
            translation_model_ref="fake_translation_model_v1",
            template_version="support_template_v1",
        )
        self.assertEqual(model_failure.disposition, DraftDisposition.HANDOFF_REQUIRED)
        self.assertEqual(model_failure.handoff.reason_code, "model_generation_failed")

        forbidden_phrase = "synthetic forbidden_claim answer"
        forbidden = pipeline(
            model=FakeDraftModel(outputs={"faq_general": forbidden_phrase})
        ).prepare(
            receipt_for(message_ref_suffix="forbidden"),
            locale="en",
            subject_ref="subject.synthetic.faq",
            original_text="synthetic low risk question",
            translated_text="synthetic low risk question",
            translation_ref="translation.synthetic.forbidden",
            translation_model_ref="fake_translation_model_v1",
            template_version="support_template_v1",
        )
        self.assertEqual(forbidden.disposition, DraftDisposition.HANDOFF_REQUIRED)
        self.assertEqual(forbidden.handoff.reason_code, "forbidden_expression_detected")
        self.assertIsNone(forbidden.draft)
        self.assertNotIn(forbidden_phrase, json.dumps(forbidden.safe_summary(), sort_keys=True))

    def test_cross_scope_policy_conflict_and_external_capability_attempts_fail_closed(self) -> None:
        other_scope = replace(
            SCOPE,
            business_line_id=UUID(int=SCOPE.business_line_id.int + 1),
            correlation_id="other_scope_correlation",
        )
        with self.assertRaisesRegex(DraftBoundaryError, "cross_scope_forbidden"):
            SupportDraftPipeline(
                fact_query=InMemoryApprovedFactQuery((replace(fact(), scope=other_scope),)),
                model=FakeDraftModel(outputs={"faq_general": "synthetic answer"}),
                forbidden_policy=forbidden_policy(),
                now=Clock(),
            ).prepare(
                receipt_for(message_ref_suffix="cross_scope"),
                locale="en",
                subject_ref="subject.synthetic.faq",
                original_text="synthetic low risk question",
                translated_text="synthetic low risk question",
                translation_ref="translation.synthetic.cross_scope",
                translation_model_ref="fake_translation_model_v1",
                template_version="support_template_v1",
            )

        policy_conflict = pipeline(policy=forbidden_policy(denied_tokens=())).prepare(
            receipt_for(message_ref_suffix="policy_conflict"),
            locale="en",
            subject_ref="subject.synthetic.faq",
            original_text="synthetic low risk question",
            translated_text="synthetic low risk question",
            translation_ref="translation.synthetic.policy_conflict",
            translation_model_ref="fake_translation_model_v1",
            template_version="support_template_v1",
        )
        self.assertEqual(policy_conflict.disposition, DraftDisposition.HANDOFF_REQUIRED)
        self.assertEqual(policy_conflict.handoff.reason_code, "policy_owner_missing")

        with self.assertRaisesRegex(DraftBoundaryError, "external_execution_forbidden"):
            ApprovedFactRef(
                scope=SCOPE,
                fact_ref="fact.synthetic.bad",
                fact_type="faq_general",
                subject_ref="subject.synthetic.faq",
                version_id=uuid_tail(6199),
                version_no=1,
                approval_state=FactApprovalState.APPROVED,
                data_state=DataState.FIXTURE,
                observed_at=NOW,
                expires_at=NOW + timedelta(hours=1),
                source_ref="source.synthetic.approved",
                evidence_ref="evidence.synthetic.approved",
                value_hash="b" * 64,
                policy_version="fact_policy_v1",
                is_synthetic=True,
                external_execution_allowed=True,
            )


if __name__ == "__main__":
    unittest.main()
