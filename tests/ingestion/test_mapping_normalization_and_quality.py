"""P03-02 synthetic-only mapping, normalization, and quality contract probes."""

from __future__ import annotations

from dataclasses import fields as dataclass_fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import unittest
from uuid import UUID

from core.contracts import synthetic_scope
from modules.ingestion.contracts import (
    ExtractionResultRecord,
    FieldLocator,
    IngestionJobRecord,
    IngestionWorkflowState,
    SourceDisposition,
    SourceFileRecord,
    StagingCandidateRecord,
)
from modules.ingestion.mapping import (
    AttributeStatus,
    MappingBatch,
    MappingEvidence,
    MappingProfile,
    MappingProfileRegistry,
    MappingRunState,
    NormalizationDescriptor,
    QualityCode,
    SyntheticMappingEngine,
    diff_replays,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "ingestion" / "synthetic_mapping_profiles.json"
NOW = datetime(2040, 1, 2, tzinfo=timezone.utc)
SCOPE = synthetic_scope()


def load_profiles() -> dict[str, MappingProfile]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    profiles: dict[str, MappingProfile] = {}
    for profile_payload in payload["profiles"]:
        profile = MappingProfile.from_mapping(profile_payload)
        key = profile.profile_id if profile.version == "v1" else f"{profile.profile_id}_{profile.version}"
        profiles[key] = profile
    return profiles


def evidence_for(
    *,
    profile: MappingProfile,
    sequence: int,
    source_field: str = "field_alpha",
    source_hash: str | None = None,
    scope=SCOPE,
    observed_at: datetime = NOW,
    descriptor: NormalizationDescriptor | None = None,
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
        idempotency_key=f"mapping_input_{sequence}",
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


def batch_for(profile: MappingProfile, *evidence: MappingEvidence) -> MappingBatch:
    return MappingBatch(
        scope=SCOPE,
        source_signature=profile.source_signature,
        evidence=tuple(evidence),
    )


def unsafe_replace_frozen(instance: object, **changes: object) -> object:
    """Construct an adversarial lifecycle object without invoking its guard."""

    forged = object.__new__(type(instance))
    for field in dataclass_fields(instance):
        object.__setattr__(forged, field.name, changes.get(field.name, getattr(instance, field.name)))
    return forged


class MappingNormalizationAndQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profiles = load_profiles()
        self.profile = self.profiles["profile_alpha"]
        self.engine = SyntheticMappingEngine(now=lambda: NOW)

    def test_profile_schema_rejects_missing_version_unknown_keys_and_generic_contract(self) -> None:
        raw = self.profile.to_mapping()

        for mutation in (
            lambda payload: payload.pop("version"),
            lambda payload: payload.update({"unexpected": "descriptor"}),
            lambda payload: payload["target_contract"].update({"fields": []}),
            lambda payload: payload["target_contract"].update({"fields": "z"}),
            lambda payload: payload["rules"][0].update({"transforms": "z"}),
            lambda payload: (
                payload["target_contract"].update({"fields": "z"}),
                payload["rules"][0].update({"target_field": "z"}),
            ),
        ):
            with self.subTest(mutation=mutation):
                candidate = json.loads(json.dumps(raw))
                mutation(candidate)
                with self.assertRaisesRegex(ValueError, "mapping_profile_schema_invalid"):
                    MappingProfile.from_mapping(candidate)

    def test_mapping_fixture_is_synthetic_only_and_value_free(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        rendered = json.dumps(payload, sort_keys=True)

        self.assertEqual(payload["fixture_kind"], "synthetic_mapping_profiles")
        self.assertTrue(payload["is_synthetic"])
        self.assertFalse(payload["external_execution_allowed"])
        self.assertFalse(payload["business_external_ready"])
        absolute_path_marker = "/" + "Users" + "/"
        for forbidden in (
            absolute_path_marker,
            "price",
            "contact",
            "secret",
            "token",
            "raw_text",
            "body",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)

    def test_mapping_is_config_first_and_retains_source_locator_rule_and_profile_lineage(self) -> None:
        report = self.engine.map(
            self.profile,
            batch_for(self.profile, evidence_for(profile=self.profile, sequence=1)),
        )

        self.assertEqual(report.state, MappingRunState.MAPPED)
        self.assertEqual(len(report.candidates), 1)
        candidate = report.candidates[0]
        self.assertEqual(candidate.source_file_id, report.input_evidence_ids[0].source_file_id)
        self.assertEqual(candidate.locator, report.input_evidence_ids[0].locator)
        self.assertEqual(candidate.rule_id, "rule_alpha")
        self.assertEqual(candidate.profile_id, self.profile.profile_id)
        self.assertEqual(candidate.profile_version, self.profile.version)
        self.assertFalse(candidate.external_execution_allowed)
        self.assertFalse(candidate.business_external_ready)
        self.assertNotEqual(candidate.normalized_value_hash, candidate.source_content_hash)

    def test_missing_profile_and_unknown_source_field_are_manual_without_implicit_mapping(self) -> None:
        evidence = evidence_for(profile=self.profile, sequence=2, source_field="field_unmapped")

        missing_profile = self.engine.map(None, batch_for(self.profile, evidence))
        unmapped = self.engine.map(self.profile, batch_for(self.profile, evidence))

        self.assertEqual(missing_profile.state, MappingRunState.BLOCKED_MANUAL)
        self.assertEqual({item.code for item in missing_profile.findings}, {QualityCode.PROFILE_MISSING})
        self.assertFalse(missing_profile.candidates)
        self.assertEqual(unmapped.state, MappingRunState.BLOCKED_MANUAL)
        self.assertIn(QualityCode.UNMAPPED_SOURCE_FIELD, {item.code for item in unmapped.findings})
        self.assertFalse(unmapped.candidates)

    def test_unknown_unit_currency_date_and_language_are_explicit_blockers(self) -> None:
        descriptor = NormalizationDescriptor(
            unit=AttributeStatus.UNKNOWN,
            currency=AttributeStatus.UNKNOWN,
            date=AttributeStatus.UNKNOWN,
            language=AttributeStatus.UNKNOWN,
        )
        report = self.engine.map(
            self.profile,
            batch_for(self.profile, evidence_for(profile=self.profile, sequence=3, descriptor=descriptor)),
        )

        self.assertEqual(report.state, MappingRunState.BLOCKED_MANUAL)
        self.assertEqual(
            {item.code for item in report.findings},
            {
                QualityCode.UNKNOWN_UNIT,
                QualityCode.UNKNOWN_CURRENCY,
                QualityCode.UNKNOWN_DATE,
                QualityCode.UNKNOWN_LANGUAGE,
            },
        )
        self.assertEqual(report.candidates[0].state, MappingRunState.BLOCKED_MANUAL)

    def test_required_missing_conflict_duplicate_and_freshness_are_stable_quality_findings(self) -> None:
        profile = self.profiles["profile_with_required_gap"]
        duplicate_hash = f"{91:064x}"
        alpha = evidence_for(
            profile=profile,
            sequence=4,
            source_hash=duplicate_hash,
            observed_at=NOW - timedelta(seconds=61),
        )
        duplicate = evidence_for(
            profile=profile,
            sequence=5,
            source_hash=duplicate_hash,
        )
        conflict = evidence_for(profile=profile, sequence=6, source_hash=f"{92:064x}")
        report = self.engine.map(profile, batch_for(profile, alpha, duplicate, conflict))

        self.assertEqual(report.state, MappingRunState.BLOCKED_MANUAL)
        self.assertIn(QualityCode.MISSING_REQUIRED, {item.code for item in report.findings})
        self.assertIn(QualityCode.DUPLICATE_CANDIDATE, {item.code for item in report.findings})
        self.assertIn(QualityCode.MAPPING_CONFLICT, {item.code for item in report.findings})
        self.assertIn(QualityCode.EXPIRED_OR_STALE, {item.code for item in report.findings})
        self.assertEqual(tuple(report.findings), tuple(sorted(report.findings, key=lambda item: item.sort_key())))

    def test_scope_and_lineage_fail_closed_as_quality_reports(self) -> None:
        evidence = evidence_for(profile=self.profile, sequence=7)
        cross_scope_evidence = replace(evidence, extraction_result=replace(evidence.extraction_result, scope=replace(SCOPE, correlation_id="other_scope")))
        report = self.engine.map(self.profile, batch_for(self.profile, cross_scope_evidence))

        self.assertEqual(report.state, MappingRunState.BLOCKED_MANUAL)
        self.assertEqual({item.code for item in report.findings}, {QualityCode.CROSS_SCOPE})
        self.assertFalse(report.candidates)

    def test_profile_signature_mismatch_and_invalid_lineage_never_map(self) -> None:
        evidence = evidence_for(profile=self.profile, sequence=8)
        signature_mismatch = MappingBatch(
            scope=SCOPE,
            source_signature=f"{999:064x}",
            evidence=(evidence,),
        )
        bad_lineage = replace(
            evidence,
            staging_candidate=replace(evidence.staging_candidate, content_hash=f"{998:064x}"),
        )

        mismatched = self.engine.map(self.profile, signature_mismatch)
        invalid = self.engine.map(self.profile, batch_for(self.profile, bad_lineage))

        self.assertEqual({item.code for item in mismatched.findings}, {QualityCode.SOURCE_SIGNATURE_MISMATCH})
        self.assertEqual({item.code for item in invalid.findings}, {QualityCode.LINEAGE_INVALID})
        self.assertFalse(mismatched.candidates)
        self.assertFalse(invalid.candidates)

    def test_non_staged_source_job_or_candidate_lifecycle_never_maps(self) -> None:
        evidence = evidence_for(profile=self.profile, sequence=12)
        quarantined_source = replace(
            evidence.source_file,
            disposition=SourceDisposition.QUARANTINED,
            quarantine_code="source_oversize",
        )
        unstarted_job = replace(
            evidence.ingestion_job,
            workflow_state=IngestionWorkflowState.REGISTERED,
        )
        unstarted_candidate = unsafe_replace_frozen(
            evidence.staging_candidate,
            workflow_state=IngestionWorkflowState.REGISTERED,
        )
        cases = (
            replace(evidence, source_file=quarantined_source),
            replace(evidence, ingestion_job=unstarted_job),
            replace(evidence, staging_candidate=unstarted_candidate),
        )

        for lifecycle_evidence in cases:
            with self.subTest(lifecycle_evidence=lifecycle_evidence):
                report = self.engine.map(
                    self.profile,
                    batch_for(self.profile, lifecycle_evidence),
                )
                self.assertEqual(report.state, MappingRunState.BLOCKED_MANUAL)
                self.assertEqual({item.code for item in report.findings}, {QualityCode.LINEAGE_INVALID})
                self.assertFalse(report.candidates)

    def test_deterministic_replay_and_profile_change_require_append_only_diff_proof(self) -> None:
        evidence = evidence_for(profile=self.profile, sequence=9)
        first = self.engine.map(self.profile, batch_for(self.profile, evidence))
        replay = self.engine.map(self.profile, batch_for(self.profile, evidence))
        changed_profile = self.profiles["profile_alpha_v2"]
        changed = self.engine.map(changed_profile, batch_for(changed_profile, evidence))
        proof = diff_replays(first, changed)
        registry = MappingProfileRegistry()

        self.assertEqual(first.run_fingerprint, replay.run_fingerprint)
        self.assertEqual(first.candidates, replay.candidates)
        registry.register(self.profile)
        with self.assertRaisesRegex(ValueError, "profile_change_replay_required"):
            registry.register(changed_profile)
        registry.register_profile_change(changed_profile, first, changed, proof)
        self.assertEqual(proof.previous_run_fingerprint, first.run_fingerprint)
        self.assertEqual(proof.current_run_fingerprint, changed.run_fingerprint)
        self.assertTrue(proof.changed_or_added_or_removed)

    def test_profile_change_rejects_forged_profile_that_does_not_match_current_replay(self) -> None:
        evidence = evidence_for(profile=self.profile, sequence=11)
        canonical = self.profiles["profile_alpha_v2"]
        previous = self.engine.map(self.profile, batch_for(self.profile, evidence))
        current = self.engine.map(canonical, batch_for(canonical, evidence))
        proof = diff_replays(previous, current)
        forged_profiles = (
            replace(
                canonical,
                rules=(
                    replace(
                        canonical.rules[0],
                        transforms=("unicode_nfkc", "trim", "casefold"),
                    ),
                ),
            ),
            replace(
                canonical,
                target_contract=replace(canonical.target_contract, fields=("target_beta",)),
                rules=(replace(canonical.rules[0], target_field="target_beta"),),
            ),
            replace(canonical, rules=(replace(canonical.rules[0], rule_id="rule_forged"),)),
            replace(canonical, source_signature=f"{1011:064x}"),
            replace(canonical, scope=replace(SCOPE, correlation_id="forged_scope")),
        )

        self.assertEqual(current.profile_fingerprint, canonical.fingerprint)
        for forged in forged_profiles:
            with self.subTest(fingerprint=forged.fingerprint):
                registry = MappingProfileRegistry()
                self.assertEqual(forged.profile_id, canonical.profile_id)
                self.assertEqual(forged.version, canonical.version)
                self.assertNotEqual(forged.fingerprint, canonical.fingerprint)
                registry.register(self.profile)
                with self.assertRaisesRegex(ValueError, "profile_report_provenance_mismatch"):
                    registry.register_profile_change(forged, previous, current, proof)
        registry = MappingProfileRegistry()
        registry.register(self.profile)
        registry.register_profile_change(canonical, previous, current, proof)

    def test_safe_reports_never_expose_values_bodies_paths_or_secrets(self) -> None:
        marker = "runtime-private-marker"
        evidence = evidence_for(profile=self.profile, sequence=10)
        report = self.engine.map(self.profile, batch_for(self.profile, evidence))
        rendered = repr((report, report.safe_summary(), report.candidates, report.findings))

        self.assertNotIn(marker, rendered)
        self.assertNotIn("storage_locator", report.safe_summary())
        self.assertNotIn("source_content_hash", report.safe_summary())
        self.assertNotIn("normalized_value_hash", report.safe_summary())


if __name__ == "__main__":
    unittest.main()
