"""P05-01 synthetic source policy and zero-network crawl port probes."""

from __future__ import annotations

from dataclasses import fields as dataclass_fields
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import unittest
from uuid import UUID

from adapters.crawl import FakeCrawlPort
from core.contracts import DataState, ScopeRef
from core.security.audit import InMemoryAuditLog
from modules.leads import CrawlBoundaryError, SourcePolicy


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2040, 8, 9, tzinfo=timezone.utc)
SCOPE = ScopeRef(
    tenant_id=UUID(int=95_001),
    project_id=UUID(int=95_101),
    business_line_id=UUID(int=95_201),
    correlation_id="p05_01_fixture",
)


class Clock:
    def __init__(self) -> None:
        self.current = NOW

    def __call__(self) -> datetime:
        result = self.current
        self.current = self.current + timedelta(seconds=1)
        return result


class SourcePolicyAndCrawlPortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(
            (ROOT / "fixtures/leads/synthetic_public_sources.json").read_text(
                encoding="utf-8"
            )
        )
        cls.page = cls.fixture["pages"][0]

    def setUp(self) -> None:
        self.clock = Clock()
        self.audit = InMemoryAuditLog(now=self.clock)
        self.port = FakeCrawlPort(
            pages={self.page["url"]: self.page},
            audit_log=self.audit,
            now=self.clock,
        )

    def approved_policy(self) -> SourcePolicy:
        return SourcePolicy(
            policy_id="source_policy_v1",
            scope=SCOPE,
            purpose="public_candidate_snapshot",
            owner_ref="owner.synthetic",
            allowed_url_prefixes=("https://synthetic-public.example.invalid/fenjiu/",),
            robots_review_ref="robots_review.synthetic",
            robots_allowed=True,
            terms_review_ref="terms_review.synthetic",
            terms_allowed=True,
            allowed_fields=("organization_name", "category", "region"),
            max_frequency_per_day=1,
            retention_days=30,
            manual_review_required=True,
            stop_conditions=(
                "login_required",
                "private_source",
                "robots_denied",
                "terms_unknown",
            ),
            data_state=DataState.FIXTURE,
            is_synthetic=True,
            external_execution_allowed=False,
            business_external_ready=False,
        )

    def forged_policy_with_allowed_fields(
        self,
        *allowed_fields: str,
    ) -> SourcePolicy:
        original = self.approved_policy()
        forged = object.__new__(SourcePolicy)
        for field in dataclass_fields(SourcePolicy):
            object.__setattr__(forged, field.name, getattr(original, field.name))
        object.__setattr__(forged, "allowed_fields", allowed_fields)
        return forged

    def contact_page(self) -> dict[str, object]:
        return {
            **self.page,
            "fields": [
                self.page["fields"][0],
                {
                    "field_name": "contact_email",
                    "selector": "[data-field=contact-email]",
                    "value": "person@example.invalid",
                },
            ],
        }

    def assert_denied_with_audit(
        self,
        policy: SourcePolicy | None,
        error_code: str,
    ) -> None:
        before = len(self.audit.events)
        with self.assertRaisesRegex(CrawlBoundaryError, error_code):
            self.port.fetch_snapshot(self.page["url"], policy)

        self.assertEqual(self.port.external_fetch_count, 0)
        self.assertEqual(len(self.audit.events), before + 1)
        event = self.audit.events[-1]
        self.assertEqual(event.event_kind, "crawl_policy_denied")
        self.assertEqual(event.result_code, error_code)
        self.assertEqual(event.metadata["external_fetch_count"], 0)
        rendered = json.dumps(event.safe_summary(), sort_keys=True)
        self.assertNotIn(self.page["url"], rendered)
        self.assertNotIn("Synthetic Trade House", rendered)

    def test_policy_robots_terms_owner_gate_denies_before_snapshot(self) -> None:
        policy = self.approved_policy()
        denial_cases = (
            (None, "source_policy_required"),
            (replace(policy, policy_id=None), "source_policy_required"),
            (replace(policy, owner_ref=None), "source_owner_required"),
            (replace(policy, robots_review_ref=None), "robots_review_required"),
            (replace(policy, robots_allowed=False), "robots_denied"),
            (replace(policy, terms_review_ref=None), "terms_review_required"),
            (replace(policy, terms_allowed=False), "terms_denied"),
        )

        for denied_policy, error_code in denial_cases:
            with self.subTest(error_code=error_code):
                self.assert_denied_with_audit(denied_policy, error_code)

        self.assertTrue(self.audit.verify_chain())

    def test_policy_rejects_contact_like_allowed_fields_before_snapshot(self) -> None:
        policy = self.approved_policy()
        forbidden_fields = (
            "contact_email",
            "phone",
            "whatsapp",
            "wechat",
            "telegram",
            "linkedin",
            "outreach_ref",
        )

        for field_name in forbidden_fields:
            with self.subTest(field_name=field_name):
                with self.assertRaisesRegex(CrawlBoundaryError, "public_field_forbidden"):
                    replace(policy, allowed_fields=("organization_name", field_name))

    def test_policy_bypass_contact_field_is_audited_and_zero_network(self) -> None:
        contact_page = self.contact_page()
        audit = InMemoryAuditLog(now=self.clock)
        port = FakeCrawlPort(
            pages={contact_page["url"]: contact_page},
            audit_log=audit,
            now=self.clock,
        )
        bad_policy = self.forged_policy_with_allowed_fields(
            "organization_name",
            "contact_email",
        )

        with self.assertRaisesRegex(CrawlBoundaryError, "public_field_forbidden"):
            port.fetch_snapshot(contact_page["url"], bad_policy)

        self.assertEqual(port.external_fetch_count, 0)
        self.assertEqual(len(audit.events), 1)
        event = audit.events[-1]
        self.assertEqual(event.event_kind, "crawl_policy_denied")
        self.assertEqual(event.result_code, "public_field_forbidden")
        self.assertEqual(event.metadata["external_fetch_count"], 0)
        rendered = json.dumps(event.safe_summary(), sort_keys=True).lower()
        self.assertNotIn("contact_email", rendered)
        self.assertNotIn("person@example.invalid", rendered)
        self.assertNotIn("crm", rendered)
        self.assertNotIn("outreach", rendered)

    def test_extract_rejects_contact_field_when_policy_is_bypassed(self) -> None:
        contact_page = self.contact_page()
        audit = InMemoryAuditLog(now=self.clock)
        port = FakeCrawlPort(
            pages={contact_page["url"]: contact_page},
            audit_log=audit,
            now=self.clock,
        )
        safe_policy = self.approved_policy()
        snapshot = port.fetch_snapshot(contact_page["url"], safe_policy)
        bad_policy = self.forged_policy_with_allowed_fields(
            "organization_name",
            "contact_email",
        )

        with self.assertRaisesRegex(CrawlBoundaryError, "public_field_forbidden"):
            port.extract_public_fields(snapshot.snapshot_ref, bad_policy)

        self.assertEqual(port.external_fetch_count, 0)
        event = audit.events[-1]
        self.assertEqual(event.event_kind, "crawl_field_denied")
        self.assertEqual(event.result_code, "public_field_forbidden")
        rendered = json.dumps(
            {
                "audit": [item.safe_summary() for item in audit.events],
            },
            sort_keys=True,
        ).lower()
        self.assertNotIn("contact_email", rendered)
        self.assertNotIn("person@example.invalid", rendered)
        self.assertNotIn("crm", rendered)
        self.assertNotIn("outreach", rendered)

    def test_login_and_private_sources_are_blocked_with_zero_network(self) -> None:
        policy = self.approved_policy()
        denial_cases = (
            (replace(policy, login_required=True), "login_required_source_forbidden"),
            (replace(policy, captcha_required=True), "captcha_source_forbidden"),
            (replace(policy, private_source=True), "private_source_forbidden"),
            (replace(policy, authentication_required=True), "authentication_source_forbidden"),
        )

        for denied_policy, error_code in denial_cases:
            with self.subTest(error_code=error_code):
                self.assert_denied_with_audit(denied_policy, error_code)

    def test_approved_synthetic_source_creates_traceable_snapshot_and_evidence(self) -> None:
        policy = self.approved_policy()
        snapshot = self.port.fetch_snapshot(self.page["url"], policy)
        candidates = self.port.extract_public_fields(snapshot.snapshot_ref, policy)

        self.assertEqual(self.port.external_fetch_count, 0)
        self.assertEqual(snapshot.http_policy_result, "synthetic_zero_network")
        self.assertEqual(snapshot.content_hash, sha256(self.page["html"].encode("utf-8")).hexdigest())
        self.assertTrue(snapshot.snapshot_ref.startswith("snapshot:"))
        self.assertFalse(hasattr(snapshot, "html"))
        self.assertFalse(hasattr(snapshot, "content"))
        self.assertEqual(snapshot.data_state, DataState.FIXTURE)
        self.assertTrue(snapshot.is_synthetic)
        self.assertFalse(snapshot.external_execution_allowed)
        self.assertFalse(snapshot.business_external_ready)

        self.assertEqual([candidate.field_name for candidate in candidates], ["organization_name", "category", "region"])
        for candidate in candidates:
            self.assertEqual(candidate.scope, SCOPE)
            self.assertEqual(candidate.snapshot_ref, snapshot.snapshot_ref)
            self.assertTrue(candidate.evidence.selector_hash)
            self.assertFalse(hasattr(candidate, "value"))
            self.assertNotEqual(candidate.value_hash, "")

        rendered = json.dumps(
            {
                "snapshot": snapshot.safe_summary(),
                "candidates": [candidate.safe_summary() for candidate in candidates],
                "audit": [event.safe_summary() for event in self.audit.events],
            },
            sort_keys=True,
        )
        self.assertNotIn(self.page["url"], rendered)
        self.assertNotIn("Synthetic Trade House", rendered)
        self.assertTrue(self.audit.verify_chain())

    def test_same_snapshot_hash_cannot_be_reused_across_business_line(self) -> None:
        policy = self.approved_policy()
        first = self.port.fetch_snapshot(self.page["url"], policy)
        other_scope = replace(
            SCOPE,
            business_line_id=UUID(int=SCOPE.business_line_id.int + 1),
            correlation_id="p05_01_other_line",
        )
        other_policy = replace(policy, scope=other_scope, owner_ref="owner.otherline")
        other = self.port.fetch_snapshot(self.page["url"], other_policy)

        self.assertEqual(first.content_hash, other.content_hash)
        self.assertNotEqual(first.snapshot_ref, other.snapshot_ref)
        with self.assertRaisesRegex(CrawlBoundaryError, "cross_scope_forbidden"):
            self.port.extract_public_fields(first.snapshot_ref, other_policy)
        self.assertEqual(self.port.external_fetch_count, 0)

    def test_external_export_is_refused_and_audited_without_raw_payload(self) -> None:
        policy = self.approved_policy()
        snapshot = self.port.fetch_snapshot(self.page["url"], policy)

        with self.assertRaisesRegex(CrawlBoundaryError, "external_export_forbidden"):
            self.port.export_external_snapshot(snapshot.snapshot_ref, policy)

        self.assertEqual(self.port.external_fetch_count, 0)
        event = self.audit.events[-1]
        self.assertEqual(event.event_kind, "crawl_export_denied")
        self.assertEqual(event.result_code, "external_export_forbidden")
        rendered = json.dumps([item.safe_summary() for item in self.audit.events], sort_keys=True)
        self.assertNotIn(self.page["url"], rendered)
        self.assertNotIn("Synthetic Trade House", rendered)


if __name__ == "__main__":
    unittest.main()
