"""P06-01 customer-service conversation, replay, and privacy contract probes."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import json
import unittest
from uuid import UUID

from core.contracts import synthetic_scope
from modules.customer_service import contracts as customer_contracts
from modules.customer_service.contracts import (
    ConversationBoundaryError,
    HandoffReason,
    InMemoryConversationStore,
    InboundMessageCommand,
    RiskLevel,
    ScopeStatus,
    SupportDisposition,
)


NOW = datetime(2040, 7, 8, tzinfo=timezone.utc)
SCOPE = synthetic_scope()


class Clock:
    def __init__(self) -> None:
        self.current = NOW

    def __call__(self) -> datetime:
        result = self.current
        self.current = self.current + timedelta(seconds=1)
        return result


def inbound_command(
    *,
    scope=SCOPE,
    scope_status: ScopeStatus = ScopeStatus.KNOWN,
    external_conversation_id: str = "external_conversation_1",
    external_message_id: str = "external_message_1",
    body_text: str = "synthetic product question",
    content_ref: str = "ref:conversation:synthetic_body_1",
    intent_label: str = "faq_general",
    risk_level: RiskLevel = RiskLevel.LOW,
    dnc_blocked: bool = False,
    personal_data_detected: bool = False,
    idempotency_key: str = "message_replay_key_1",
) -> InboundMessageCommand:
    return InboundMessageCommand(
        scope=scope,
        scope_status=scope_status,
        channel_ref="channel:tiktok.synthetic",
        external_conversation_id=external_conversation_id,
        external_message_id=external_message_id,
        received_at=NOW,
        received_by="synthetic_channel",
        body_text=body_text,
        content_ref=content_ref,
        intent_label=intent_label,
        risk_level=risk_level,
        retention_policy_ref="retention_policy:p06_synthetic",
        consent_ref="consent:synthetic_present",
        dnc_blocked=dnc_blocked,
        personal_data_detected=personal_data_detected,
        policy_version="support_contract_v1",
        idempotency_key=idempotency_key,
    )


class CustomerServiceConversationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemoryConversationStore(now=Clock())

    def test_external_message_replay_is_idempotent_without_new_draft_or_audit_side_effect(self) -> None:
        command = inbound_command()

        first = self.store.receive(command)
        replay = self.store.receive(command)

        self.assertFalse(first.replayed)
        self.assertTrue(replay.replayed)
        self.assertEqual(first.disposition, SupportDisposition.DRAFT_READY)
        self.assertEqual(replay.message.id, first.message.id)
        self.assertEqual(replay.draft.id, first.draft.id)
        self.assertEqual(
            self.store.snapshot_counts(),
            {
                "conversations": 1,
                "messages": 1,
                "intents": 1,
                "drafts": 1,
                "handoffs": 0,
                "audit_events": 1,
            },
        )

        with self.assertRaises(FrozenInstanceError):
            first.message.content_hash = "changed"

        rendered = json.dumps(first.safe_summary(), sort_keys=True)
        self.assertNotIn("synthetic product question", rendered)
        self.assertNotIn("body_text", rendered)

    def test_replay_with_changed_payload_or_scope_fails_closed_before_side_effects(self) -> None:
        self.store.receive(inbound_command())
        before = self.store.snapshot_counts()

        with self.assertRaisesRegex(ConversationBoundaryError, "idempotency_conflict"):
            self.store.receive(
                inbound_command(
                    body_text="different synthetic question",
                    content_ref="ref:conversation:synthetic_body_2",
                )
            )

        other_scope = replace(
            SCOPE,
            business_line_id=UUID(int=SCOPE.business_line_id.int + 1),
        )
        with self.assertRaisesRegex(ConversationBoundaryError, "cross_scope_forbidden"):
            self.store.receive(
                inbound_command(
                    scope=other_scope,
                    external_message_id="external_message_2",
                    idempotency_key="message_replay_key_2",
                )
            )

        self.assertEqual(self.store.snapshot_counts(), before)

    def test_scope_is_mandatory_and_unknown_scope_is_quarantined_for_handoff(self) -> None:
        with self.assertRaisesRegex(ConversationBoundaryError, "scope_required"):
            inbound_command(scope=None, scope_status=ScopeStatus.KNOWN)

        receipt = self.store.receive(
            inbound_command(
                scope=None,
                scope_status=ScopeStatus.UNKNOWN,
                external_conversation_id="unknown_scope_conversation",
                external_message_id="unknown_scope_message",
                idempotency_key="unknown_scope_key",
            )
        )

        self.assertEqual(receipt.disposition, SupportDisposition.QUARANTINED)
        self.assertIsNone(receipt.conversation)
        self.assertIsNone(receipt.message)
        self.assertIsNotNone(receipt.handoff)
        self.assertEqual(receipt.handoff.reason, HandoffReason.UNKNOWN_SCOPE)
        self.assertEqual(
            self.store.snapshot_counts(),
            {
                "conversations": 0,
                "messages": 0,
                "intents": 0,
                "drafts": 0,
                "handoffs": 1,
                "audit_events": 1,
            },
        )

    def test_dnc_and_personal_data_minimize_content_and_force_handoff_without_draft(self) -> None:
        dnc_receipt = self.store.receive(
            inbound_command(
                external_conversation_id="conversation_dnc",
                external_message_id="message_dnc",
                dnc_blocked=True,
                idempotency_key="dnc_key",
            )
        )
        self.assertEqual(dnc_receipt.disposition, SupportDisposition.HANDOFF_REQUIRED)
        self.assertIsNone(dnc_receipt.draft)
        self.assertEqual(dnc_receipt.handoff.reason, HandoffReason.DNC_BLOCKED)

        private_contact = "person" + "@" + "example.invalid"
        privacy_receipt = self.store.receive(
            inbound_command(
                external_conversation_id="conversation_privacy",
                external_message_id="message_privacy",
                body_text=f"synthetic contact {private_contact}",
                personal_data_detected=True,
                idempotency_key="privacy_key",
            )
        )
        self.assertEqual(privacy_receipt.disposition, SupportDisposition.HANDOFF_REQUIRED)
        self.assertIsNone(privacy_receipt.draft)
        self.assertEqual(
            privacy_receipt.handoff.reason,
            HandoffReason.PRIVACY_REVIEW_REQUIRED,
        )
        rendered = json.dumps(
            [record.safe_summary() for record in self.store.messages],
            sort_keys=True,
        )
        self.assertNotIn(private_contact, rendered)
        self.assertNotIn("body_text", rendered)
        self.assertNotIn("raw", rendered.lower())

    def test_absolute_path_secret_and_unflagged_personal_data_are_rejected_before_records(self) -> None:
        private_segment = "priv" + "ate"
        unsafe_inputs = (
            ("local_path", "/" + "Users" + "/example/private_chat.txt"),
            ("private_storage", "/" + "Volumes" + f"/{private_segment}/chat.txt"),
            ("secret_like", "sk" + "-" + "syntheticsecretvalue"),
            ("unflagged_personal", "person" + "@" + "example.invalid"),
        )

        for suffix, body_text in unsafe_inputs:
            with self.subTest(suffix=suffix):
                with self.assertRaisesRegex(
                    ConversationBoundaryError,
                    "privacy_payload_forbidden",
                ):
                    self.store.receive(
                        inbound_command(
                            external_conversation_id=f"conversation_{suffix}",
                            external_message_id=f"message_{suffix}",
                            body_text=body_text,
                            idempotency_key=f"unsafe_key_{suffix}",
                        )
                    )

        self.assertEqual(
            self.store.snapshot_counts(),
            {
                "conversations": 0,
                "messages": 0,
                "intents": 0,
                "drafts": 0,
                "handoffs": 0,
                "audit_events": 0,
            },
        )

    def test_customer_service_contracts_expose_no_channel_adapter_webhook_or_send_endpoint(self) -> None:
        forbidden_fragments = ("adapter", "webhook", "send")
        public_callables = {
            name
            for name, value in vars(customer_contracts).items()
            if not name.startswith("_") and callable(value)
        }

        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertFalse(
                    any(fragment in name.lower() for name in public_callables),
                    public_callables,
                )

        for name in ("webhook", "send", "send_message", "connect_channel"):
            self.assertFalse(hasattr(self.store, name))


if __name__ == "__main__":
    unittest.main()
