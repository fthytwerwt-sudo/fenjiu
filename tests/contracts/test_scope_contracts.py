"""P02-01 stdlib contract tests for scope and mandatory metadata."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest
from uuid import UUID

from core.contracts import (
    BaseMetadata,
    BusinessLineContract,
    ContractValidationError,
    DataState,
    DataVersionRef,
    ProjectContract,
    ScopeRef,
    Sensitivity,
    SourceRef,
    TenantContract,
    assert_metadata_lineage,
    assert_same_scope,
    synthetic_scope,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = UUID("00000000-0000-4000-8000-000000000301")
VERSION_ID = UUID("00000000-0000-4000-8000-000000000401")
ENTITY_ID = UUID("00000000-0000-4000-8000-000000000501")
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def source_contract(scope: ScopeRef | None = None) -> SourceRef:
    return SourceRef(
        id=SOURCE_ID,
        scope=scope or synthetic_scope(),
        source_kind="synthetic_fixture",
        source_version="v1",
        data_state=DataState.FIXTURE,
        sensitivity=Sensitivity.INTERNAL,
        is_synthetic=True,
    )


def version_contract(scope: ScopeRef | None = None) -> DataVersionRef:
    return DataVersionRef(
        id=VERSION_ID,
        scope=scope or synthetic_scope(),
        source_ref_id=SOURCE_ID,
        version_no=1,
        data_state=DataState.FIXTURE,
        sensitivity=Sensitivity.INTERNAL,
        is_synthetic=True,
    )


def metadata_contract(scope: ScopeRef | None = None) -> BaseMetadata:
    return BaseMetadata(
        id=ENTITY_ID,
        scope=scope or synthetic_scope(),
        data_state=DataState.FIXTURE,
        source_ref_id=SOURCE_ID,
        data_version_id=VERSION_ID,
        sensitivity=Sensitivity.INTERNAL,
        is_synthetic=True,
        external_execution_allowed=False,
        created_at=NOW,
        updated_at=NOW,
        created_by="synthetic_test",
    )


class ScopeContractTests(unittest.TestCase):
    def test_scope_anchors_and_compound_scope_are_required(self) -> None:
        scope = synthetic_scope()
        tenant = TenantContract(scope.tenant_id, "synthetic_tenant", True)
        project = ProjectContract(
            scope.project_id,
            scope.tenant_id,
            "synthetic_project",
            True,
        )
        business_line = BusinessLineContract(
            scope.business_line_id,
            scope.tenant_id,
            scope.project_id,
            "synthetic_line",
            True,
        )

        self.assertTrue(tenant.is_synthetic)
        self.assertEqual(project.tenant_id, tenant.id)
        self.assertEqual(business_line.project_id, project.id)
        self.assertFalse(business_line.external_execution_allowed)

        with self.assertRaisesRegex(ContractValidationError, "tenant_id_required"):
            ScopeRef(UUID(int=0), scope.project_id, scope.business_line_id, "corr")

    def test_source_version_and_metadata_share_scope(self) -> None:
        source = source_contract()
        version = version_contract()
        metadata = metadata_contract()

        self.assertEqual(assert_same_scope(source, version, metadata), synthetic_scope())
        self.assertEqual(metadata.data_state, DataState.FIXTURE)
        self.assertEqual(metadata.source_ref_id, source.id)
        self.assertEqual(metadata.data_version_id, version.id)
        assert_metadata_lineage(source, version, metadata)

    def test_cross_business_line_is_rejected(self) -> None:
        other_scope = replace(
            synthetic_scope(),
            business_line_id=UUID("00000000-0000-4000-8000-000000000202"),
        )

        with self.assertRaisesRegex(ContractValidationError, "cross_scope_forbidden"):
            assert_same_scope(source_contract(), version_contract(other_scope))

    def test_source_and_version_lineage_must_match(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "version_lineage_mismatch"):
            assert_metadata_lineage(
                source_contract(),
                version_contract(),
                replace(
                    metadata_contract(),
                    data_version_id=UUID("00000000-0000-4000-8000-000000000499"),
                ),
            )

    def test_missing_source_version_state_and_sensitivity_fail_closed(self) -> None:
        valid = metadata_contract()
        cases = (
            ("source_ref_id", UUID(int=0), "source_ref_id_required"),
            ("data_version_id", UUID(int=0), "data_version_id_required"),
            ("data_state", "fixture", "data_state_required"),
            ("sensitivity", "internal", "sensitivity_required"),
        )

        for field_name, invalid, code in cases:
            with self.subTest(field_name=field_name):
                with self.assertRaisesRegex(ContractValidationError, code):
                    replace(valid, **{field_name: invalid})

    def test_synthetic_contract_cannot_be_approved_or_external(self) -> None:
        valid = metadata_contract()

        with self.assertRaisesRegex(ContractValidationError, "synthetic_state_mismatch"):
            replace(valid, data_state=DataState.APPROVED)
        with self.assertRaisesRegex(ContractValidationError, "external_execution_forbidden"):
            replace(valid, external_execution_allowed=True)
        with self.assertRaisesRegex(ContractValidationError, "synthetic_state_mismatch"):
            replace(valid, is_synthetic=not True)

    def test_timestamp_and_version_number_are_validated(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "timestamp_order_invalid"):
            replace(metadata_contract(), updated_at=NOW - timedelta(seconds=1))
        with self.assertRaisesRegex(ContractValidationError, "version_number_required"):
            replace(version_contract(), version_no=0)

    def test_repository_fixture_is_synthetic_and_matches_contract(self) -> None:
        payload = json.loads(
            (ROOT / "fixtures" / "synthetic_metadata.json").read_text(encoding="utf-8")
        )
        scope_payload = payload["scope"]
        scope = ScopeRef(
            tenant_id=UUID(scope_payload["tenant_id"]),
            project_id=UUID(scope_payload["project_id"]),
            business_line_id=UUID(scope_payload["business_line_id"]),
            correlation_id=scope_payload["correlation_id"],
        )
        source = SourceRef(
            id=UUID(payload["source_ref_id"]),
            scope=scope,
            source_kind=payload["source_kind"],
            source_version=payload["source_version"],
            data_state=DataState(payload["data_state"]),
            sensitivity=Sensitivity(payload["sensitivity"]),
            is_synthetic=payload["is_synthetic"],
            external_execution_allowed=payload["external_execution_allowed"],
        )
        version = DataVersionRef(
            id=UUID(payload["data_version_id"]),
            scope=scope,
            source_ref_id=UUID(payload["source_ref_id"]),
            version_no=payload["version_no"],
            data_state=DataState(payload["data_state"]),
            sensitivity=Sensitivity(payload["sensitivity"]),
            is_synthetic=payload["is_synthetic"],
            external_execution_allowed=payload["external_execution_allowed"],
        )
        metadata = BaseMetadata(
            id=UUID(payload["entity_id"]),
            scope=scope,
            data_state=DataState(payload["data_state"]),
            source_ref_id=UUID(payload["source_ref_id"]),
            data_version_id=UUID(payload["data_version_id"]),
            sensitivity=Sensitivity(payload["sensitivity"]),
            is_synthetic=payload["is_synthetic"],
            external_execution_allowed=payload["external_execution_allowed"],
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
            created_by=payload["created_by"],
        )

        assert_metadata_lineage(source, version, metadata)
        self.assertTrue(metadata.is_synthetic)
        self.assertFalse(metadata.external_execution_allowed)


if __name__ == "__main__":
    unittest.main()
