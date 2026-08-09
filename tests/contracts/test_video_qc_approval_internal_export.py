"""P07-03 video QC, approval, and internal-export-only contract probes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import unittest
from uuid import UUID

from adapters.video import (
    FakeVideoProvider,
    LegacyCapability,
    LegacyVideoAdapterSpec,
    LegacyVideoOperation,
    VideoManifest,
)
from core.contracts import DataState, synthetic_scope
from core.security.audit import InMemoryAuditLog
from modules.content_video import (
    AssetOrigin,
    AssetRightsState,
    AssetRightsVersionLock,
    ContentVideoBoundaryError,
    FactApprovalState,
    FactVersionLock,
    ForbiddenExpressionPolicy,
    HumanVideoDecisionAction,
    HumanVideoDecisionState,
    PolicyBoundaryState,
    PolicyVersionLock,
    ProviderQcEvidence,
    VideoArtifactEvidence,
    VideoManifestEvidence,
    VideoQcApprovalWorkflow,
    VideoQcState,
    VideoTechnicalCheck,
    VideoTask,
    VideoTaskState,
)


NOW = datetime(2040, 8, 10, tzinfo=timezone.utc)
SCOPE = synthetic_scope()
LOCAL_USER_MARKER = "/" + "Users" + "/"


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
        policy_version="content_policy_v1",
        is_synthetic=True,
        external_execution_allowed=False,
    )


def asset_lock(
    *,
    origin: AssetOrigin = AssetOrigin.AI_GENERATED,
    rights_state: AssetRightsState = AssetRightsState.AUTHORIZED,
    version_id: UUID | None = None,
    expires_at: datetime | None = None,
) -> AssetRightsVersionLock:
    return AssetRightsVersionLock(
        scope=SCOPE,
        asset_ref="asset.synthetic.demo",
        version_id=version_id or uuid_tail(7202),
        version_no=1,
        origin=origin,
        rights_state=rights_state,
        rights_version="asset_rights_v1",
        evidence_ref="asset_evidence_v1",
        observed_at=NOW - timedelta(minutes=5),
        expires_at=expires_at or (NOW + timedelta(days=1)),
        is_synthetic=True,
        external_execution_allowed=False,
    )


def forbidden_policy() -> ForbiddenExpressionPolicy:
    return ForbiddenExpressionPolicy(
        scope=SCOPE,
        version_id=uuid_tail(7401),
        policy_version="content_policy_v1",
        denied_tokens=("forbidden_claim",),
        observed_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(days=1),
        is_synthetic=True,
        external_execution_allowed=False,
    )


def policy_lock(
    *,
    boundary_state: PolicyBoundaryState = PolicyBoundaryState.APPROVED,
    expires_at: datetime | None = None,
) -> PolicyVersionLock:
    return PolicyVersionLock(
        scope=SCOPE,
        policy_version="content_policy_v1",
        boundary_state=boundary_state,
        forbidden_policy=forbidden_policy(),
        observed_at=NOW - timedelta(minutes=5),
        expires_at=expires_at or (NOW + timedelta(days=1)),
        is_synthetic=True,
        external_execution_allowed=False,
    )


def video_task() -> VideoTask:
    return VideoTask(
        id=uuid_tail(7701),
        scope=SCOPE,
        content_task_id=uuid_tail(7201),
        locked_fact_versions=(fact_lock().version_id,),
        locked_asset_versions=(asset_lock().version_id,),
        policy_version="content_policy_v1",
        state=VideoTaskState.QC_PENDING,
        created_at=NOW,
        created_by="synthetic_video_worker",
        is_synthetic=True,
        external_execution_allowed=False,
        provider_call_requested=False,
        internal_export_allowed=False,
        public_publish_allowed=False,
    )


def legacy_spec() -> LegacyVideoAdapterSpec:
    return LegacyVideoAdapterSpec(
        provider_alias="happyhorse_dashscope_legacy_fake",
        operation=LegacyVideoOperation.SHOT_GENERATION,
        capability=LegacyCapability.HAPPYHORSE_DASHSCOPE,
        legacy_script="generate_happyhorse_shots.py",
        legacy_input_refs=("manifest:locked_prompt_hash", "asset_hash:synthetic_demo"),
        legacy_output_ref="artifact_ref:synthetic_provider_output",
        no_auto_retry=True,
        is_synthetic=True,
        external_execution_allowed=False,
    )


def manifest() -> VideoManifest:
    return VideoManifest.from_video_task(
        manifest_id=uuid_tail(7801),
        video_task=video_task(),
        manifest_version=1,
        idempotency_key="idem.p07_03.synthetic.video",
        prompt_hash="a" * 64,
        input_asset_hashes=("b" * 64,),
        cost_approval_ref="cost_approval.synthetic.p07_03",
        legacy_adapter=legacy_spec(),
        created_at=NOW,
    )


def evidence_chain() -> tuple[VideoManifestEvidence, VideoArtifactEvidence, ProviderQcEvidence]:
    provider = FakeVideoProvider(now=lambda: NOW)
    item = manifest()
    submission = provider.submit(item)
    artifact = provider.download_artifact_ref(submission.provider_task_ref)
    provider_qc = provider.create_qc_ref(artifact.artifact_ref)
    return (
        VideoManifestEvidence.from_summary(item.safe_summary(), scope=item.scope),
        VideoArtifactEvidence.from_summary(artifact.safe_summary()),
        ProviderQcEvidence.from_summary(provider_qc.safe_summary()),
    )


def technical_check(
    artifact: VideoArtifactEvidence,
    *,
    decode_ok: bool = True,
    format_ok: bool = True,
    subtitle_present: bool = True,
    audio_track_present: bool = True,
    origin_label_present: bool = True,
    artifact_hash: str | None = None,
) -> VideoTechnicalCheck:
    return VideoTechnicalCheck(
        artifact_ref=artifact.artifact_ref,
        artifact_hash=artifact_hash or artifact.content_hash,
        decode_ok=decode_ok,
        format_ok=format_ok,
        aspect_ratio="9:16",
        duration_seconds=18,
        subtitle_present=subtitle_present,
        audio_track_present=audio_track_present,
        origin_label_present=origin_label_present,
        checked_at=NOW,
        is_synthetic=True,
        external_execution_allowed=False,
    )


def run_qc(
    *,
    fact: FactVersionLock | None = None,
    asset: AssetRightsVersionLock | None = None,
    policy: PolicyVersionLock | None = None,
    artifact: VideoArtifactEvidence | None = None,
    provider_qc: ProviderQcEvidence | None = None,
    technical: VideoTechnicalCheck | None = None,
    external_publish_requested: bool = False,
):
    manifest_evidence, artifact_evidence, provider_qc_evidence = evidence_chain()
    fact_item = fact or fact_lock()
    asset_item = asset or asset_lock()
    artifact_item = artifact_evidence if artifact is None else artifact
    provider_qc_item = provider_qc_evidence if provider_qc is None else provider_qc
    workflow = VideoQcApprovalWorkflow()
    return workflow.run_qc(
        manifest=manifest_evidence,
        artifact=artifact_item,
        provider_qc=provider_qc_item,
        technical_check=technical or technical_check(artifact_item),
        fact_locks=(fact_item,),
        asset_locks=(asset_item,),
        policy_lock=policy or policy_lock(),
        current_fact_versions={fact_item.fact_ref: fact_item.version_id},
        current_asset_versions={asset_item.asset_ref: asset_item.version_id},
        current_policy_version="content_policy_v1",
        checked_at=NOW,
        external_publish_requested=external_publish_requested,
    )


class VideoQcApprovalInternalExportTests(unittest.TestCase):
    def test_full_internal_chain_passes_qc_requires_human_approval_and_exports_reference_only(self) -> None:
        manifest_evidence, artifact, provider_qc = evidence_chain()
        workflow = VideoQcApprovalWorkflow()
        audit = InMemoryAuditLog(now=lambda: NOW)

        report = workflow.run_qc(
            manifest=manifest_evidence,
            artifact=artifact,
            provider_qc=provider_qc,
            technical_check=technical_check(artifact),
            fact_locks=(fact_lock(),),
            asset_locks=(asset_lock(),),
            policy_lock=policy_lock(),
            current_fact_versions={fact_lock().fact_ref: fact_lock().version_id},
            current_asset_versions={asset_lock().asset_ref: asset_lock().version_id},
            current_policy_version="content_policy_v1",
            checked_at=NOW,
        )
        audit.record(
            event_kind="video_qc_completed",
            actor_ref="synthetic_qc_worker",
            scope=SCOPE,
            command_ref=report.qc_report_ref,
            target_ref=artifact.artifact_ref,
            policy_version=report.policy_version,
            subject_version=report.manifest_version,
            result_code=report.state.value,
            metadata=report.audit_metadata(),
        )

        decision = workflow.record_human_decision(
            report=report,
            decision_ref="decision_ref:p07_03.approve",
            action=HumanVideoDecisionAction.APPROVE_INTERNAL_EXPORT,
            reviewer_ref="content_reviewer.synthetic",
            decided_at=NOW,
        )
        audit.record(
            event_kind="video_human_decision",
            actor_ref=decision.reviewer_ref,
            scope=SCOPE,
            command_ref=decision.decision_ref,
            target_ref=report.qc_report_ref,
            policy_version=decision.policy_version,
            subject_version=report.manifest_version,
            result_code=decision.state.value,
            metadata=decision.audit_metadata(),
        )

        export = workflow.create_internal_export_ref(
            report=report,
            decision=decision,
            export_ref="internal_export_ref:p07_03.demo",
            storage_ref="internal_storage_ref:p07_03.demo",
            created_at=NOW,
        )
        audit.record(
            event_kind="video_internal_export_ref_created",
            actor_ref=decision.reviewer_ref,
            scope=SCOPE,
            command_ref=export.export_ref,
            target_ref=report.qc_report_ref,
            policy_version=export.policy_version,
            subject_version=report.manifest_version,
            result_code=export.state.value,
            metadata=export.audit_metadata(),
        )

        self.assertEqual(report.state, VideoQcState.PASSED)
        self.assertEqual(report.reason_codes, ())
        self.assertEqual(decision.state, HumanVideoDecisionState.APPROVED_INTERNAL)
        self.assertEqual(export.external_publish_attempts, 0)
        self.assertFalse(export.publish_port_present)
        self.assertFalse(export.public_publish_allowed)
        self.assertTrue(export.internal_only)
        self.assertTrue(audit.verify_chain())

        rendered = json.dumps(
            {
                "report": report.safe_summary(),
                "decision": decision.safe_summary(),
                "export": export.safe_summary(),
                "audit": [event.safe_summary() for event in audit.events],
            },
            sort_keys=True,
        )
        self.assertNotIn(LOCAL_USER_MARKER, rendered)
        self.assertNotIn("outputs/", rendered)
        self.assertNotIn("media/", rendered)
        self.assertNotIn(".mp4", rendered)
        self.assertNotIn("provider_raw_id", rendered)
        self.assertNotIn("prompt_text", rendered)

    def test_qc_negative_suite_fails_closed_without_external_publish_attempts(self) -> None:
        manifest_evidence, artifact, provider_qc = evidence_chain()
        mismatched_artifact = VideoArtifactEvidence(
            artifact_ref=artifact.artifact_ref,
            provider_task_ref=artifact.provider_task_ref,
            manifest_id=uuid_tail(9999),
            state=artifact.state,
            content_hash=artifact.content_hash,
        )
        corrupted_check = technical_check(artifact, artifact_hash="c" * 64)

        cases = (
            ("artifact_missing", {"artifact": None}),
            ("artifact_manifest_mismatch", {"artifact": mismatched_artifact}),
            ("decode_failed", {"technical": technical_check(artifact, decode_ok=False)}),
            ("subtitle_missing", {"technical": technical_check(artifact, subtitle_present=False)}),
            ("artifact_hash_mismatch", {"technical": corrupted_check}),
            ("asset_origin_unknown", {"asset": asset_lock(origin=AssetOrigin.UNKNOWN)}),
            (
                "fact_lock_expired",
                {"fact": fact_lock(expires_at=NOW - timedelta(seconds=1))},
            ),
            (
                "fact_lock_not_current",
                {"fact": fact_lock(data_state=DataState.CONFLICT)},
            ),
            (
                "policy_lock_expired",
                {"policy": policy_lock(expires_at=NOW - timedelta(seconds=1))},
            ),
            ("external_publish_forbidden", {"external_publish_requested": True}),
        )

        workflow = VideoQcApprovalWorkflow()
        for code, overrides in cases:
            with self.subTest(code=code):
                artifact_override = overrides.get("artifact", artifact)
                provider_override = provider_qc
                technical_override = overrides.get("technical")
                if artifact_override is None:
                    provider_override = None
                    technical_override = None
                report = workflow.run_qc(
                    manifest=manifest_evidence,
                    artifact=artifact_override,
                    provider_qc=provider_override,
                    technical_check=technical_override
                    or (technical_check(artifact_override) if artifact_override else None),
                    fact_locks=(overrides.get("fact") or fact_lock(),),
                    asset_locks=(overrides.get("asset") or asset_lock(),),
                    policy_lock=overrides.get("policy") or policy_lock(),
                    current_fact_versions={
                        (overrides.get("fact") or fact_lock()).fact_ref: (
                            overrides.get("fact") or fact_lock()
                        ).version_id
                    },
                    current_asset_versions={
                        (overrides.get("asset") or asset_lock()).asset_ref: (
                            overrides.get("asset") or asset_lock()
                        ).version_id
                    },
                    current_policy_version="content_policy_v1",
                    checked_at=NOW,
                    external_publish_requested=bool(
                        overrides.get("external_publish_requested", False)
                    ),
                )

                self.assertIn(code, report.reason_codes)
                self.assertNotEqual(report.state, VideoQcState.PASSED)
                self.assertEqual(report.external_publish_attempts, 0)
                self.assertFalse(report.public_publish_allowed)
                with self.assertRaisesRegex(ContentVideoBoundaryError, "qc_not_passed"):
                    workflow.record_human_decision(
                        report=report,
                        decision_ref="decision_ref:p07_03.invalid_approve",
                        action=HumanVideoDecisionAction.APPROVE_INTERNAL_EXPORT,
                        reviewer_ref="content_reviewer.synthetic",
                        decided_at=NOW,
                    )

    def test_human_reject_and_revise_are_terminal_without_internal_export(self) -> None:
        report = run_qc()
        workflow = VideoQcApprovalWorkflow()

        reject = workflow.record_human_decision(
            report=report,
            decision_ref="decision_ref:p07_03.reject",
            action=HumanVideoDecisionAction.REJECT,
            reviewer_ref="content_reviewer.synthetic",
            decided_at=NOW,
        )
        revise = workflow.record_human_decision(
            report=report,
            decision_ref="decision_ref:p07_03.revise",
            action=HumanVideoDecisionAction.REVISE,
            reviewer_ref="content_reviewer.synthetic",
            decided_at=NOW,
            revision_ref="revision_ref:p07_03.copy_safe",
        )

        self.assertEqual(reject.state, HumanVideoDecisionState.REJECTED)
        self.assertEqual(revise.state, HumanVideoDecisionState.REVISION_REQUESTED)
        for decision in (reject, revise):
            with self.subTest(decision=decision.state.value):
                self.assertEqual(decision.external_publish_attempts, 0)
                self.assertFalse(decision.internal_export_approved)
                with self.assertRaisesRegex(ContentVideoBoundaryError, "human_approval_required"):
                    workflow.create_internal_export_ref(
                        report=report,
                        decision=decision,
                        export_ref="internal_export_ref:p07_03.blocked",
                        storage_ref="internal_storage_ref:p07_03.blocked",
                        created_at=NOW,
                    )

        with self.assertRaisesRegex(ContentVideoBoundaryError, "revision_ref_required"):
            workflow.record_human_decision(
                report=report,
                decision_ref="decision_ref:p07_03.bad_revise",
                action=HumanVideoDecisionAction.REVISE,
                reviewer_ref="content_reviewer.synthetic",
                decided_at=NOW,
            )

    def test_internal_export_rejects_publish_ports_paths_and_media_references(self) -> None:
        report = run_qc()
        workflow = VideoQcApprovalWorkflow()
        decision = workflow.record_human_decision(
            report=report,
            decision_ref="decision_ref:p07_03.approve",
            action=HumanVideoDecisionAction.APPROVE_INTERNAL_EXPORT,
            reviewer_ref="content_reviewer.synthetic",
            decided_at=NOW,
        )

        with self.assertRaisesRegex(ContentVideoBoundaryError, "internal_export_ref_forbidden"):
            workflow.create_internal_export_ref(
                report=report,
                decision=decision,
                export_ref="internal_export_ref:p07_03.bad",
                storage_ref="outputs/generated_media_ref",
                created_at=NOW,
            )

        with self.assertRaisesRegex(ContentVideoBoundaryError, "external_publish_forbidden"):
            workflow.create_internal_export_ref(
                report=report,
                decision=decision,
                export_ref="internal_export_ref:p07_03.bad_publish",
                storage_ref="internal_storage_ref:p07_03.demo",
                created_at=NOW,
                publish_port_present=True,
            )

    def test_manifest_evidence_rejects_any_external_flags(self) -> None:
        summary = dict(manifest().safe_summary())
        cases = (
            ("external_execution_forbidden", {"external_execution_allowed": True}),
            ("video_call_forbidden", {"provider_call_requested": True}),
            ("internal_export_forbidden", {"internal_export_allowed": True}),
            ("public_publish_forbidden", {"public_publish_allowed": True}),
            ("public_publish_forbidden", {"public_publish_allowed": "true"}),
        )

        for code, overrides in cases:
            with self.subTest(code=code):
                flagged = dict(summary)
                flagged.update(overrides)
                with self.assertRaisesRegex(ContentVideoBoundaryError, code):
                    VideoManifestEvidence.from_summary(flagged, scope=SCOPE)


if __name__ == "__main__":
    unittest.main()
