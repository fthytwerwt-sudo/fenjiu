"""P07-01 content/video fact-lock and policy contract probes."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest
from uuid import UUID

from core.contracts import DataState, synthetic_scope
from modules.content_video.contracts import (
    AssetOrigin,
    AssetRightsState,
    AssetRightsVersionLock,
    BriefDataOrigin,
    ContentPolicySuite,
    ContentReviewState,
    ContentTask,
    ContentTaskState,
    ContentVideoBoundaryError,
    FactApprovalState,
    FactVersionLock,
    ForbiddenExpressionPolicy,
    PolicyBoundaryState,
    PolicyVersionLock,
    SyntheticBrief,
    VideoTask,
    VideoTaskState,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "content_video" / "synthetic_policy_vectors.json"
NOW = datetime(2040, 1, 2, tzinfo=timezone.utc)
SCOPE = synthetic_scope()


def load_vectors() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def uuid_tail(value: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{value:012d}")


def fact_lock(
    *,
    approval_state: FactApprovalState = FactApprovalState.APPROVED,
    data_state: DataState = DataState.FIXTURE,
    version_id: UUID | None = None,
    expires_at: datetime | None = None,
) -> FactVersionLock:
    return FactVersionLock(
        scope=SCOPE,
        fact_ref="fact.synthetic.claim",
        fact_type="synthetic_claim",
        subject_ref="subject.synthetic.demo",
        version_id=version_id or uuid_tail(7101),
        version_no=1,
        approval_state=approval_state,
        data_state=data_state,
        observed_at=NOW - timedelta(minutes=5),
        expires_at=expires_at or (NOW + timedelta(days=1)),
        source_label="approved_synthetic",
        evidence_ref="fact_evidence_v1",
        policy_version="fact_lock_policy_v1",
        is_synthetic=True,
        external_execution_allowed=False,
    )


def asset_lock(name: str = "asset.ai_generated.demo") -> AssetRightsVersionLock:
    payload = load_vectors()
    vector = next(
        item for item in payload["asset_vectors"] if item["asset_ref"] == name
    )
    return AssetRightsVersionLock(
        scope=SCOPE,
        asset_ref=vector["asset_ref"],
        version_id=UUID(vector["version_id"]),
        version_no=vector["version_no"],
        origin=AssetOrigin(vector["origin"]),
        rights_state=AssetRightsState(vector["rights_state"]),
        rights_version=vector["rights_version"],
        evidence_ref=vector["evidence_ref"],
        observed_at=NOW - timedelta(minutes=5),
        expires_at=datetime.fromisoformat(vector["expires_at"]),
        is_synthetic=True,
        external_execution_allowed=False,
    )


def forbidden_policy() -> ForbiddenExpressionPolicy:
    payload = load_vectors()["forbidden_policy"]
    return ForbiddenExpressionPolicy(
        scope=SCOPE,
        version_id=UUID(payload["version_id"]),
        policy_version=payload["policy_version"],
        denied_tokens=tuple(payload["denied_tokens"]),
        observed_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(days=1),
        is_synthetic=True,
        external_execution_allowed=False,
    )


def policy_lock(
    *,
    boundary_state: PolicyBoundaryState = PolicyBoundaryState.APPROVED,
    policy_version: str = "content_policy_v1",
    expires_at: datetime | None = None,
) -> PolicyVersionLock:
    policy = forbidden_policy()
    if policy.policy_version != policy_version:
        policy = replace(policy, policy_version=policy_version)
    if expires_at is not None:
        policy = replace(policy, expires_at=expires_at)
    return PolicyVersionLock(
        scope=SCOPE,
        policy_version=policy_version,
        boundary_state=boundary_state,
        forbidden_policy=policy,
        observed_at=NOW - timedelta(minutes=5),
        expires_at=expires_at or (NOW + timedelta(days=1)),
        is_synthetic=True,
        external_execution_allowed=False,
    )


def brief(name: str = "brief.synthetic.safe") -> SyntheticBrief:
    payload = load_vectors()
    vector = next(
        item for item in payload["brief_vectors"] if item["brief_ref"] == name
    )
    return SyntheticBrief(
        scope=SCOPE,
        brief_ref=vector["brief_ref"],
        locale=vector["locale"],
        topic_ref="topic.synthetic.internal_demo",
        tokens=tuple(vector["tokens"]),
        data_origin=BriefDataOrigin.SYNTHETIC,
        is_synthetic=True,
        external_execution_allowed=False,
    )


def task(
    *,
    facts: tuple[FactVersionLock, ...] | None = None,
    assets: tuple[AssetRightsVersionLock, ...] | None = None,
    brief_ref: SyntheticBrief | None = None,
    lock: PolicyVersionLock | None = None,
) -> ContentTask:
    return ContentTask(
        id=uuid_tail(7201),
        scope=SCOPE,
        brief=brief_ref or brief(),
        fact_locks=facts if facts is not None else (fact_lock(),),
        asset_locks=assets if assets is not None else (asset_lock(),),
        policy_lock=lock or policy_lock(),
        state=ContentTaskState.DRAFT,
        created_at=NOW,
        created_by="synthetic_content_worker",
        is_synthetic=True,
        external_execution_allowed=False,
        provider_call_requested=False,
        public_publish_allowed=False,
    )


def submit(content_task: ContentTask):
    suite = ContentPolicySuite()
    return suite.submit_for_review(
        content_task,
        checked_at=NOW,
        current_fact_versions={
            lock.fact_ref: lock.version_id for lock in content_task.fact_locks
        },
        current_asset_versions={
            lock.asset_ref: lock.version_id for lock in content_task.asset_locks
        },
        current_policy_version=content_task.policy_lock.policy_version,
    )


class ContentVideoContractTests(unittest.TestCase):
    def test_valid_synthetic_brief_reaches_review_and_video_qc_without_external_capability(self) -> None:
        content_task = task(
            assets=(
                asset_lock("asset.ai_generated.demo"),
                asset_lock("asset.supplier_authorized.demo"),
            )
        )

        review = submit(content_task)

        self.assertEqual(review.state, ContentReviewState.REVIEW_PENDING)
        self.assertFalse(review.external_execution_allowed)
        self.assertFalse(review.provider_call_requested)
        self.assertFalse(review.public_publish_allowed)
        self.assertEqual(review.locked_fact_versions, (fact_lock().version_id,))
        self.assertEqual(
            review.locked_asset_versions,
            (
                asset_lock("asset.ai_generated.demo").version_id,
                asset_lock("asset.supplier_authorized.demo").version_id,
            ),
        )

        video_task = VideoTask.from_review(
            id=uuid_tail(7301),
            review=review,
            created_at=NOW,
            created_by="synthetic_video_worker",
        )

        self.assertEqual(video_task.state, VideoTaskState.QC_PENDING)
        self.assertFalse(video_task.provider_call_requested)
        self.assertFalse(video_task.internal_export_allowed)
        self.assertFalse(video_task.public_publish_allowed)

    def test_fact_locks_fail_closed_when_missing_unapproved_or_expired(self) -> None:
        cases = (
            ("fact_lock_required", task(facts=())),
            (
                "unapproved_fact_lock",
                task(facts=(fact_lock(approval_state=FactApprovalState.PENDING),)),
            ),
            (
                "unapproved_fact_lock",
                task(facts=(fact_lock(data_state=DataState.STAGING),)),
            ),
            (
                "fact_lock_expired",
                task(facts=(fact_lock(expires_at=NOW - timedelta(seconds=1)),)),
            ),
        )

        for code, content_task in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(ContentVideoBoundaryError, code):
                    submit(content_task)

    def test_asset_rights_origin_vectors_allow_ai_and_supplier_but_block_unknown(self) -> None:
        for name in ("asset.ai_generated.demo", "asset.supplier_authorized.demo"):
            with self.subTest(name=name):
                review = submit(task(assets=(asset_lock(name),)))
                self.assertEqual(review.state, ContentReviewState.REVIEW_PENDING)

        with self.assertRaisesRegex(ContentVideoBoundaryError, "asset_rights_unknown"):
            submit(task(assets=(asset_lock("asset.unknown.demo"),)))

    def test_forbidden_expression_policy_blocks_synthetic_brief(self) -> None:
        with self.assertRaisesRegex(
            ContentVideoBoundaryError,
            "forbidden_expression_detected",
        ):
            submit(task(brief_ref=brief("brief.synthetic.forbidden")))

    def test_fact_asset_and_policy_version_changes_invalidate_existing_task(self) -> None:
        content_task = task()
        suite = ContentPolicySuite()
        base_kwargs = {
            "checked_at": NOW,
            "current_fact_versions": {"fact.synthetic.claim": fact_lock().version_id},
            "current_asset_versions": {
                "asset.ai_generated.demo": asset_lock().version_id
            },
            "current_policy_version": "content_policy_v1",
        }

        invalid_cases = (
            (
                "fact_version_invalidated",
                {
                    **base_kwargs,
                    "current_fact_versions": {
                        "fact.synthetic.claim": uuid_tail(9991)
                    },
                },
            ),
            (
                "asset_version_invalidated",
                {
                    **base_kwargs,
                    "current_asset_versions": {
                        "asset.ai_generated.demo": uuid_tail(9992)
                    },
                },
            ),
            (
                "policy_version_invalidated",
                {**base_kwargs, "current_policy_version": "content_policy_v2"},
            ),
        )

        for code, kwargs in invalid_cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(ContentVideoBoundaryError, code):
                    suite.submit_for_review(content_task, **kwargs)

    def test_unknown_or_expired_policy_fails_closed(self) -> None:
        cases = (
            (
                "policy_boundary_unknown",
                policy_lock(boundary_state=PolicyBoundaryState.UNKNOWN),
            ),
            (
                "policy_lock_expired",
                policy_lock(expires_at=NOW - timedelta(seconds=1)),
            ),
        )

        for code, lock in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(ContentVideoBoundaryError, code):
                    submit(task(lock=lock))

    def test_external_video_call_or_export_flags_are_rejected(self) -> None:
        review = submit(task())
        cases = (
            ("video_call_forbidden", {"provider_call_requested": True}),
            ("internal_export_forbidden", {"internal_export_allowed": True}),
            ("public_publish_forbidden", {"public_publish_allowed": True}),
        )

        for code, overrides in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(ContentVideoBoundaryError, code):
                    VideoTask(
                        id=uuid_tail(7302),
                        scope=SCOPE,
                        content_task_id=review.content_task_id,
                        locked_fact_versions=review.locked_fact_versions,
                        locked_asset_versions=review.locked_asset_versions,
                        policy_version=review.policy_version,
                        state=VideoTaskState.QC_PENDING,
                        created_at=NOW,
                        created_by="synthetic_video_worker",
                        is_synthetic=True,
                        external_execution_allowed=False,
                        provider_call_requested=overrides.get(
                            "provider_call_requested",
                            False,
                        ),
                        internal_export_allowed=overrides.get(
                            "internal_export_allowed",
                            False,
                        ),
                        public_publish_allowed=overrides.get(
                            "public_publish_allowed",
                            False,
                        ),
                    )

    def test_non_synthetic_brief_origin_is_rejected(self) -> None:
        with self.assertRaisesRegex(ContentVideoBoundaryError, "synthetic_brief_required"):
            replace(brief(), data_origin=BriefDataOrigin.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
