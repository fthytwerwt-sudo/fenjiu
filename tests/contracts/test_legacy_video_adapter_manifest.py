"""P07-02 legacy video manifest and fake provider contract probes."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import unittest
from uuid import UUID

from adapters.video import (
    FakeVideoProvider,
    LegacyCapability,
    LegacyProbeState,
    LegacyVideoAdapterSpec,
    LegacyVideoOperation,
    ProviderRunState,
    QualityControlState,
    VideoManifest,
    VideoPortBoundaryError,
    build_legacy_probe_baseline,
)
from core.contracts import synthetic_scope
from modules.content_video import VideoTask, VideoTaskState


NOW = datetime(2040, 8, 9, tzinfo=timezone.utc)
SCOPE = synthetic_scope()
LOCAL_USER_MARKER = "/" + "Users" + "/"


def uuid_tail(value: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{value:012d}")


def video_task() -> VideoTask:
    return VideoTask(
        id=uuid_tail(7701),
        scope=SCOPE,
        content_task_id=uuid_tail(7201),
        locked_fact_versions=(uuid_tail(7101),),
        locked_asset_versions=(uuid_tail(7202),),
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


def legacy_spec(
    *,
    operation: LegacyVideoOperation = LegacyVideoOperation.SHOT_GENERATION,
    no_auto_retry: bool = True,
) -> LegacyVideoAdapterSpec:
    return LegacyVideoAdapterSpec(
        provider_alias="happyhorse_dashscope_legacy_fake",
        operation=operation,
        capability=LegacyCapability.HAPPYHORSE_DASHSCOPE,
        legacy_script="generate_happyhorse_shots.py",
        legacy_input_refs=("manifest:locked_prompt_hash", "asset_hash:synthetic_demo"),
        legacy_output_ref="artifact_ref:synthetic_provider_output",
        no_auto_retry=no_auto_retry,
        is_synthetic=True,
        external_execution_allowed=False,
    )


def manifest(
    *,
    operation: LegacyVideoOperation = LegacyVideoOperation.SHOT_GENERATION,
    no_auto_retry: bool = True,
) -> VideoManifest:
    return VideoManifest.from_video_task(
        manifest_id=uuid_tail(7801),
        video_task=video_task(),
        manifest_version=1,
        idempotency_key="idem.p07_02.synthetic.video",
        prompt_hash="a" * 64,
        input_asset_hashes=("b" * 64,),
        cost_approval_ref="cost_approval.synthetic.p07_02",
        legacy_adapter=legacy_spec(
            operation=operation,
            no_auto_retry=no_auto_retry,
        ),
        created_at=NOW,
    )


class LegacyVideoAdapterManifestTests(unittest.TestCase):
    def test_versioned_manifest_locks_video_task_without_payload_or_external_flags(self) -> None:
        item = manifest()

        self.assertEqual(item.schema_version, "video_manifest.v1")
        self.assertEqual(item.manifest_version, 1)
        self.assertEqual(item.video_task_id, video_task().id)
        self.assertEqual(item.locked_fact_versions, video_task().locked_fact_versions)
        self.assertEqual(item.locked_asset_versions, video_task().locked_asset_versions)
        self.assertFalse(item.external_execution_allowed)
        self.assertFalse(item.provider_call_requested)
        self.assertFalse(item.internal_export_allowed)
        self.assertFalse(item.public_publish_allowed)

        rendered = json.dumps(item.safe_summary(), sort_keys=True)
        self.assertIn("prompt_hash", rendered)
        self.assertNotIn("prompt_text", rendered)
        self.assertNotIn("DashScope", rendered)
        self.assertNotIn("api_key", rendered.lower())
        self.assertNotIn(LOCAL_USER_MARKER, rendered)
        self.assertNotIn("outputs/", rendered)

    def test_fake_provider_submit_poll_download_and_qc_are_reference_only(self) -> None:
        provider = FakeVideoProvider(now=lambda: NOW)
        item = manifest()

        submission = provider.submit(item)
        running = provider.poll(submission.provider_task_ref)
        artifact = provider.download_artifact_ref(submission.provider_task_ref)
        qc = provider.create_qc_ref(artifact.artifact_ref)

        self.assertEqual(provider.external_call_count, 0)
        self.assertEqual(submission.state, ProviderRunState.SUBMITTED)
        self.assertEqual(running.state, ProviderRunState.RUNNING)
        self.assertEqual(artifact.state, ProviderRunState.DOWNLOADED)
        self.assertEqual(qc.state, QualityControlState.MANUAL_REVIEW_REQUIRED)
        self.assertFalse(qc.quality_approved)
        self.assertTrue(qc.manual_review_required)

        rendered = json.dumps(
            {
                "submission": submission.safe_summary(),
                "artifact": artifact.safe_summary(),
                "qc": qc.safe_summary(),
            },
            sort_keys=True,
        )
        self.assertNotIn(LOCAL_USER_MARKER, rendered)
        self.assertNotIn("outputs/", rendered)
        self.assertNotIn(".mp4", rendered)
        self.assertNotIn("provider_raw_id", rendered)

    def test_video_edit_requires_no_auto_retry_and_uncertainty_does_not_resubmit(self) -> None:
        with self.assertRaisesRegex(
            VideoPortBoundaryError,
            "video_edit_no_auto_retry_required",
        ):
            manifest(
                operation=LegacyVideoOperation.VIDEO_EDIT,
                no_auto_retry=False,
            )

        provider = FakeVideoProvider(now=lambda: NOW)
        edit_manifest = manifest(operation=LegacyVideoOperation.VIDEO_EDIT)
        uncertainty = provider.record_provider_uncertainty(
            edit_manifest,
            error_code="provider_uncertain",
        )

        self.assertEqual(provider.external_call_count, 0)
        self.assertEqual(provider.submission_count, 0)
        self.assertEqual(uncertainty.state, ProviderRunState.MANUAL_REVIEW_REQUIRED)
        self.assertFalse(uncertainty.may_auto_retry)
        self.assertTrue(uncertainty.manual_review_required)

    def test_legacy_baseline_keeps_unlocated_video_scripts_blocked_without_env_or_execution(self) -> None:
        probes = build_legacy_probe_baseline(git_files=("scripts/build_project_sync_pack.py",))
        by_name = {probe.script_name: probe for probe in probes}

        for script_name in (
            "generate_happyhorse_shots.py",
            "generate_happyhorse_video_edit_once.py",
            "prepare_video_assets.py",
            "assemble_final_video.py",
            "build_video_execution_report.py",
        ):
            with self.subTest(script_name=script_name):
                probe = by_name[script_name]
                self.assertEqual(probe.state, LegacyProbeState.BLOCKED_NOT_LOCATED)
                self.assertEqual(probe.sha256, "UNKNOWN")
                self.assertFalse(probe.cli_help_checked)
                self.assertFalse(probe.execution_allowed)
                self.assertFalse(probe.env_read_allowed)
                self.assertFalse(probe.output_write_allowed)

        rendered = json.dumps([probe.safe_summary() for probe in probes], sort_keys=True)
        self.assertNotIn(".env", rendered)
        self.assertNotIn(LOCAL_USER_MARKER, rendered)
        self.assertNotIn("token", rendered.lower())

    def test_manifest_rejects_paths_credentials_payloads_and_external_flags(self) -> None:
        local_video_path = LOCAL_USER_MARKER + "fan/video.mp4"
        cases = (
            ("video_input_ref_forbidden", {"input_asset_hashes": (local_video_path,)}),
            ("video_input_ref_forbidden", {"input_asset_hashes": ("outputs/generated.mp4",)}),
            ("video_input_ref_forbidden", {"input_asset_hashes": ("secret_token_ref",)}),
            ("external_execution_forbidden", {"external_execution_allowed": True}),
            ("video_call_forbidden", {"provider_call_requested": True}),
        )

        base = manifest()
        for code, overrides in cases:
            with self.subTest(code=code):
                with self.assertRaisesRegex(VideoPortBoundaryError, code):
                    VideoManifest(
                        schema_version=base.schema_version,
                        manifest_id=base.manifest_id,
                        scope=base.scope,
                        video_task_id=base.video_task_id,
                        content_task_id=base.content_task_id,
                        locked_fact_versions=base.locked_fact_versions,
                        locked_asset_versions=base.locked_asset_versions,
                        policy_version=base.policy_version,
                        manifest_version=base.manifest_version,
                        idempotency_key=base.idempotency_key,
                        prompt_hash=base.prompt_hash,
                        input_asset_hashes=overrides.get(
                            "input_asset_hashes",
                            base.input_asset_hashes,
                        ),
                        cost_approval_ref=base.cost_approval_ref,
                        legacy_adapter=base.legacy_adapter,
                        created_at=base.created_at,
                        is_synthetic=True,
                        external_execution_allowed=overrides.get(
                            "external_execution_allowed",
                            False,
                        ),
                        provider_call_requested=overrides.get(
                            "provider_call_requested",
                            False,
                        ),
                        internal_export_allowed=False,
                        public_publish_allowed=False,
                    )


if __name__ == "__main__":
    unittest.main()
