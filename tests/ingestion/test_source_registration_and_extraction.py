"""P03-01 fail-closed source registration and fake extraction probes."""

from __future__ import annotations

import ast
from dataclasses import fields as dataclass_fields
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest
from uuid import UUID

from adapters.storage import fake_extractor_registry
from core.contracts import ContractValidationError, DataState, ScopeRef
import modules.ingestion as ingestion_api
from modules.ingestion import (
    ExtractionResultRecord,
    FieldLocator,
    InMemoryIngestionStore,
    IngestionOutcomeState,
    IngestionPipeline,
    RegisterSourceCommand,
    SourceKind,
    SourceFileRecord,
    StagingCandidateRecord,
    SyntheticFieldDescriptor,
)


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 6, tzinfo=timezone.utc)
SCOPE = ScopeRef(
    tenant_id=UUID(int=71_001),
    project_id=UUID(int=71_101),
    business_line_id=UUID(int=71_201),
    correlation_id="p03_01_fixture",
)


def command_for(
    profile: dict[str, object],
    *,
    scope: ScopeRef = SCOPE,
    parser_version: str = "parser_v1",
    storage_locator: object | None = None,
    declared_mime: object | None = None,
) -> RegisterSourceCommand:
    return RegisterSourceCommand(
        scope=scope,
        storage_locator=(
            profile["storage_locator"]
            if storage_locator is None
            else storage_locator
        ),
        storage_locator_version="locator_v1",
        declared_mime=profile["mime"] if declared_mime is None else declared_mime,
        parser_version=parser_version,
        mapping_profile_version="unmapped_v0",
        received_at=NOW,
        received_by="synthetic_receiver",
        idempotency_key="synthetic_ingestion",
        is_synthetic=True,
        external_execution_allowed=False,
        business_external_ready=False,
    )


def locator_from(payload: dict[str, object]) -> FieldLocator:
    bbox = payload.get("bbox")
    return FieldLocator(
        page=payload.get("page"),
        sheet=payload.get("sheet"),
        row=payload.get("row"),
        cell=payload.get("cell"),
        bbox=tuple(bbox) if isinstance(bbox, list) else None,
        export_record=payload.get("export_record"),
        member_relative_path=payload.get("member_relative_path"),
    )


def field_for(profile: dict[str, object], seed: int) -> SyntheticFieldDescriptor:
    locator = profile["locator"]
    assert isinstance(locator, dict)
    return SyntheticFieldDescriptor(
        field_name=profile["field_name"],
        value_hash=f"{seed:064x}",
        locator=locator_from(locator),
        confidence_basis="synthetic_fixture",
    )


class SourceRegistrationAndExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(
            (ROOT / "fixtures/ingestion/synthetic_source_profiles.json").read_text(
                encoding="utf-8"
            )
        )

    def setUp(self) -> None:
        self.store = InMemoryIngestionStore()
        self.pipeline = IngestionPipeline(
            store=self.store,
            extractors=fake_extractor_registry(),
            max_source_bytes=128,
        )

    def test_all_synthetic_source_types_stage_only_located_candidates(self) -> None:
        self.assertTrue(self.fixture["is_synthetic"])
        self.assertFalse(self.fixture["external_execution_allowed"])
        self.assertFalse(self.fixture["business_external_ready"])

        for seed, profile in enumerate(self.fixture["profiles"], start=1):
            with self.subTest(source_kind=profile["source_kind"]):
                outcome = self.pipeline.ingest(
                    command_for(profile),
                    bytes([seed]) * 32,
                    (field_for(profile, seed),),
                )

                self.assertEqual(outcome.state, IngestionOutcomeState.STAGED)
                self.assertEqual(outcome.source_file.source_kind.value, profile["source_kind"])
                self.assertEqual(outcome.source_file.data_state, DataState.FIXTURE)
                self.assertEqual(outcome.ingestion_job.data_state, DataState.FIXTURE)
                self.assertEqual(len(outcome.extraction_results), 1)
                self.assertEqual(len(outcome.staging_candidates), 1)
                candidate = outcome.staging_candidates[0]
                self.assertEqual(candidate.workflow_state.value, "staged")
                self.assertEqual(candidate.data_state, DataState.FIXTURE)
                self.assertTrue(candidate.is_synthetic)
                self.assertFalse(candidate.external_execution_allowed)
                self.assertFalse(candidate.business_external_ready)
                self.assertTrue(candidate.locator.has_traceable_location)
                self.assertFalse(hasattr(candidate, "value"))
                self.assertFalse(hasattr(outcome.source_file, "body"))

        self.assertEqual(
            {kind.value for kind in SourceKind},
            {"xlsx", "csv", "docx", "pdf", "image", "folder", "json_export"},
        )

    def test_hash_rerun_is_idempotent_and_parser_version_creates_new_job(self) -> None:
        profile = self.fixture["profiles"][0]
        payload = bytes(range(32))
        field = field_for(profile, 101)

        first = self.pipeline.ingest(command_for(profile), payload, (field,))
        rerun = self.pipeline.ingest(command_for(profile), payload, (field,))
        changed_parser = self.pipeline.ingest(
            command_for(profile, parser_version="parser_v2"),
            payload,
            (field,),
        )

        self.assertEqual(first.source_file.id, rerun.source_file.id)
        self.assertEqual(first.ingestion_job.id, rerun.ingestion_job.id)
        self.assertEqual(first.extraction_results, rerun.extraction_results)
        self.assertEqual(first.staging_candidates, rerun.staging_candidates)
        self.assertEqual(first.source_file.id, changed_parser.source_file.id)
        self.assertNotEqual(first.ingestion_job.id, changed_parser.ingestion_job.id)
        self.assertNotEqual(first.extraction_results, changed_parser.extraction_results)
        self.assertNotEqual(first.staging_candidates, changed_parser.staging_candidates)
        self.assertEqual(len(self.store.source_files), 1)
        self.assertEqual(len(self.store.ingestion_jobs), 2)

    def test_same_hash_and_locator_version_accepts_private_locator_alias(self) -> None:
        profile = self.fixture["profiles"][0]
        payload = bytes([14]) * 16
        field = field_for(profile, 114)
        first = self.pipeline.ingest(command_for(profile), payload, (field,))
        alias = self.pipeline.ingest(
            command_for(
                profile,
                storage_locator="private/fixture/source-01-alias.xlsx",
            ),
            payload,
            (field,),
        )

        self.assertEqual(alias.state, IngestionOutcomeState.STAGED)
        self.assertEqual(first.source_file.id, alias.source_file.id)
        self.assertEqual(first.ingestion_job.id, alias.ingestion_job.id)
        self.assertEqual(len(self.store.source_files), 1)

    def test_same_hash_cannot_reuse_records_across_scope(self) -> None:
        profile = self.fixture["profiles"][1]
        payload = bytes([9]) * 16
        field = field_for(profile, 102)
        other_scope = replace(
            SCOPE,
            business_line_id=UUID(int=SCOPE.business_line_id.int + 1),
            correlation_id="p03_01_other_scope",
        )

        first = self.pipeline.ingest(command_for(profile), payload, (field,))
        other = self.pipeline.ingest(
            command_for(profile, scope=other_scope),
            payload,
            (field,),
        )

        self.assertNotEqual(first.source_file.id, other.source_file.id)
        self.assertNotEqual(first.ingestion_job.id, other.ingestion_job.id)
        with self.assertRaisesRegex(ContractValidationError, "cross_scope_forbidden"):
            self.store.get_source(other_scope, first.source_file.id)
        forged = replace(first.extraction_results[0], scope=other_scope)
        forged_candidate = replace(first.staging_candidates[0], scope=other_scope)
        with self.assertRaisesRegex(ContractValidationError, "cross_scope_forbidden"):
            self.store.append_staging_batch((forged,), (forged_candidate,))

    def test_runtime_store_exposes_only_atomic_staging_write(self) -> None:
        self.assertIn("InMemoryIngestionStore", ingestion_api.__all__)
        self.assertFalse(hasattr(InMemoryIngestionStore, "append_result"))
        self.assertFalse(hasattr(InMemoryIngestionStore, "append_candidate"))
        self.assertTrue(hasattr(InMemoryIngestionStore, "append_staging_batch"))
        self.assertFalse(hasattr(ingestion_api, "append_result"))
        self.assertFalse(hasattr(ingestion_api, "append_candidate"))

        profile = self.fixture["profiles"][0]
        outcome = self.pipeline.ingest(
            command_for(profile),
            bytes([16]) * 16,
            (field_for(profile, 116),),
        )
        results_before = self.store.extraction_results
        candidates_before = self.store.staging_candidates

        pending_result = replace(
            outcome.extraction_results[0],
            id=UUID(int=71_301),
        )
        mismatched_candidate = replace(
            outcome.staging_candidates[0],
            id=UUID(int=71_302),
            extraction_result_id=pending_result.id,
            field_name="mismatched_field",
        )
        with self.assertRaisesRegex(
            ContractValidationError,
            "staging_result_mismatch",
        ):
            self.store.append_staging_batch(
                (pending_result,),
                (mismatched_candidate,),
            )
        self.assertEqual(self.store.extraction_results, results_before)
        self.assertEqual(self.store.staging_candidates, candidates_before)

        with self.assertRaisesRegex(
            ContractValidationError,
            "staging_batch_atomicity_required",
        ):
            self.store.append_staging_batch(outcome.extraction_results, ())
        self.assertEqual(self.store.extraction_results, results_before)
        self.assertEqual(self.store.staging_candidates, candidates_before)

        with self.assertRaisesRegex(
            ContractValidationError,
            "staging_batch_atomicity_required",
        ):
            self.store.append_staging_batch((), outcome.staging_candidates)
        self.assertEqual(self.store.extraction_results, results_before)
        self.assertEqual(self.store.staging_candidates, candidates_before)

    def test_unknown_mime_oversize_and_unsafe_locator_quarantine_fail_closed(self) -> None:
        profile = self.fixture["profiles"][2]
        cases = (
            (
                command_for(profile, declared_mime="application/x-unknown"),
                bytes([3]) * 16,
                "unsupported_mime",
            ),
            (command_for(profile), bytes(129), "source_oversize"),
            (command_for(profile), b"", "source_empty"),
            (
                command_for(profile, storage_locator=".." + "/" + "private/source.bin"),
                bytes([4]) * 16,
                "storage_locator_unsafe",
            ),
            (
                command_for(profile, storage_locator="/" + "private/source.bin"),
                bytes([5]) * 16,
                "storage_locator_unsafe",
            ),
        )

        for command, payload, code in cases:
            with self.subTest(code=code):
                outcome = self.pipeline.ingest(command, payload, ())
                self.assertIn(
                    outcome.state,
                    {IngestionOutcomeState.QUARANTINED, IngestionOutcomeState.BLOCKED_MANUAL},
                )
                self.assertEqual(outcome.failure.error_code, code)
                self.assertEqual(str(outcome.failure.error), code)
                self.assertFalse(outcome.extraction_results)
                self.assertFalse(outcome.staging_candidates)
                self.assertIn(outcome.failure, self.store.failures)

    def test_folder_member_traversal_is_blocked_before_staging(self) -> None:
        profile = self.fixture["profiles"][5]
        field = SyntheticFieldDescriptor(
            field_name="field_unsafe_member",
            value_hash=f"{109:064x}",
            locator=FieldLocator(
                member_relative_path=".." + "/member.json",
                export_record="record_1",
            ),
            confidence_basis="synthetic_fixture",
        )

        outcome = self.pipeline.ingest(
            command_for(profile),
            bytes([13]) * 16,
            (field,),
        )

        self.assertEqual(outcome.state, IngestionOutcomeState.BLOCKED_MANUAL)
        self.assertEqual(outcome.failure.error_code, "field_locator_invalid")
        self.assertFalse(self.store.extraction_results)
        self.assertFalse(self.store.staging_candidates)

    def test_unlocated_field_is_retained_for_manual_review_without_candidate(self) -> None:
        profile = self.fixture["profiles"][0]
        located = field_for(profile, 110)
        unlocated = SyntheticFieldDescriptor(
            field_name="field_unlocated",
            value_hash=f"{111:064x}",
            locator=None,
            confidence_basis="synthetic_fixture",
        )

        outcome = self.pipeline.ingest(
            command_for(profile),
            bytes([6]) * 16,
            (located, unlocated),
        )

        self.assertEqual(outcome.state, IngestionOutcomeState.BLOCKED_MANUAL)
        self.assertEqual(outcome.failure.error_code, "field_locator_required")
        self.assertEqual(outcome.ingestion_job.workflow_state.value, "blocked_manual")
        self.assertFalse(outcome.extraction_results)
        self.assertFalse(outcome.staging_candidates)
        self.assertFalse(self.store.extraction_results)
        self.assertFalse(self.store.staging_candidates)

    def test_failed_rerun_is_idempotent_and_retains_one_failure_record(self) -> None:
        profile = self.fixture["profiles"][0]
        invalid_locator = FieldLocator(sheet="Sheet_1", row=0, cell="A0")
        field = SyntheticFieldDescriptor(
            field_name="field_invalid_locator",
            value_hash=f"{112:064x}",
            locator=invalid_locator,
            confidence_basis="synthetic_fixture",
        )

        first = self.pipeline.ingest(command_for(profile), bytes([12]) * 16, (field,))
        rerun = self.pipeline.ingest(command_for(profile), bytes([12]) * 16, (field,))

        self.assertEqual(first.failure.id, rerun.failure.id)
        self.assertEqual(first.failure.error_code, "field_locator_invalid")
        self.assertEqual(len(self.store.failures), 1)
        self.assertFalse(self.store.extraction_results)
        self.assertFalse(self.store.staging_candidates)

    def test_parse_and_ocr_failures_are_retained_without_guessed_text(self) -> None:
        pdf_profile = self.fixture["profiles"][3]
        image_profile = self.fixture["profiles"][4]
        store = InMemoryIngestionStore()
        pipeline = IngestionPipeline(
            store=store,
            extractors=fake_extractor_registry(
                failure_by_kind={
                    SourceKind.PDF: "parse_failed",
                    SourceKind.IMAGE: "ocr_failed",
                }
            ),
            max_source_bytes=128,
        )

        for seed, profile, code in (
            (7, pdf_profile, "parse_failed"),
            (8, image_profile, "ocr_failed"),
        ):
            with self.subTest(code=code):
                outcome = pipeline.ingest(
                    command_for(profile),
                    bytes([seed]) * 16,
                    (field_for(profile, 200 + seed),),
                )
                self.assertEqual(outcome.state, IngestionOutcomeState.BLOCKED_MANUAL)
                self.assertEqual(outcome.failure.error_code, code)
                self.assertEqual(outcome.ingestion_job.workflow_state.value, "blocked_manual")
                self.assertFalse(outcome.extraction_results)
                self.assertFalse(outcome.staging_candidates)
                self.assertIn(outcome.failure, store.failures)
                self.assertFalse(hasattr(outcome.failure, "guessed_text"))

    def test_records_and_errors_never_retain_body_absolute_path_or_secret(self) -> None:
        profile = self.fixture["profiles"][5]
        body_marker = "".join(("runtime", "-body-marker"))
        secret_marker = "".join(("runtime", "-private-marker"))
        absolute_locator = "/" + "U" + "sers/synthetic-private/" + secret_marker
        payload = body_marker.encode("ascii") + bytes([10]) * 16

        staged = self.pipeline.ingest(
            command_for(profile),
            payload,
            (field_for(profile, 113),),
        )

        outcome = self.pipeline.ingest(
            command_for(profile, storage_locator=absolute_locator),
            payload,
            (),
        )

        rendered = repr(
            (
                staged,
                outcome,
                self.store.records,
                staged.safe_summary(),
                outcome.safe_summary(),
            )
        )
        self.assertEqual(staged.state, IngestionOutcomeState.STAGED)
        self.assertEqual(outcome.failure.error_code, "storage_locator_unsafe")
        self.assertNotIn(body_marker, rendered)
        self.assertNotIn(secret_marker, rendered)
        self.assertNotIn(absolute_locator, rendered)
        self.assertNotIn("payload", outcome.safe_summary())
        self.assertNotIn("storage_locator", outcome.safe_summary())

        forbidden_record_fields = {
            "body",
            "payload",
            "raw_text",
            "text",
            "value",
            "secret",
            "absolute_path",
        }
        for record_type in (
            SourceFileRecord,
            ExtractionResultRecord,
            StagingCandidateRecord,
        ):
            with self.subTest(record_type=record_type.__name__):
                names = {field.name for field in dataclass_fields(record_type)}
                self.assertFalse(names & forbidden_record_fields)

    def test_implementation_has_no_file_network_process_or_database_clients(self) -> None:
        banned_import_roots = {
            "boto3",
            "http",
            "openai",
            "psycopg",
            "requests",
            "socket",
            "sqlalchemy",
            "sqlite3",
            "subprocess",
            "urllib",
        }
        banned_calls = {"open", "read_bytes", "read_text", "urlopen"}
        source_paths = tuple(
            path
            for directory in (
                ROOT / "modules/ingestion",
                ROOT / "adapters/storage",
            )
            for path in directory.glob("*.py")
            if not path.name.startswith("._")
        )

        for path in source_paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported_roots: set[str] = set()
            called_names: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(
                        alias.name.split(".", 1)[0] for alias in node.names
                    )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".", 1)[0])
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        called_names.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        called_names.add(node.func.attr)
            with self.subTest(path=path.name):
                self.assertFalse(imported_roots & banned_import_roots)
                self.assertFalse(called_names & banned_calls)

    def test_real_or_external_flags_are_rejected_before_extraction(self) -> None:
        profile = self.fixture["profiles"][6]
        invalid_commands = (
            replace(command_for(profile), **{"is_" + "synthetic": False}),
            replace(command_for(profile), external_execution_allowed=True),
            replace(command_for(profile), business_external_ready=True),
        )

        for command in invalid_commands:
            with self.subTest(command=command):
                outcome = self.pipeline.ingest(command, bytes([11]) * 16, ())
                self.assertEqual(outcome.state, IngestionOutcomeState.BLOCKED_MANUAL)
                self.assertIn(
                    outcome.failure.error_code,
                    {
                        "synthetic_input_required",
                        "external_execution_forbidden",
                        "business_external_ready_forbidden",
                    },
                )
                self.assertFalse(outcome.staging_candidates)

    def test_secret_like_metadata_fails_closed_without_retention(self) -> None:
        profile = self.fixture["profiles"][6]
        first_marker = "".join(("sk", "-live-demo"))
        second_marker = "".join(("secret", "-token-123"))
        cases = (
            ("received_by", replace(command_for(profile), received_by=first_marker)),
            ("idempotency", replace(command_for(profile), idempotency_key=second_marker)),
            (
                "mime",
                replace(
                    command_for(profile),
                    declared_mime="application/" + second_marker,
                ),
            ),
            ("locator", replace(
                command_for(profile),
                storage_locator="private/fixture/" + second_marker + ".json",
            )),
            ("correlation", replace(
                command_for(profile),
                scope=replace(SCOPE, correlation_id=second_marker),
            )),
        )

        for label, command in cases:
            with self.subTest(field=label):
                store = InMemoryIngestionStore()
                pipeline = IngestionPipeline(
                    store=store,
                    extractors=fake_extractor_registry(),
                    max_source_bytes=128,
                )
                outcome = pipeline.ingest(command, bytes([15]) * 16, ())
                rendered = repr((outcome, store.records, outcome.safe_summary()))
                self.assertEqual(outcome.state, IngestionOutcomeState.BLOCKED_MANUAL)
                self.assertEqual(
                    outcome.failure.error_code,
                    "sensitive_metadata_forbidden",
                )
                self.assertNotIn(first_marker, rendered)
                self.assertNotIn(second_marker, rendered)
                self.assertFalse(store.source_files)
                self.assertFalse(store.ingestion_jobs)
                self.assertFalse(store.staging_candidates)


if __name__ == "__main__":
    unittest.main()
