"""Type-specific extraction fakes; these adapters never read source bytes."""

from __future__ import annotations

from typing import Mapping, Tuple

from modules.ingestion.contracts import (
    IngestionBoundaryError,
    SourceDisposition,
    SourceFileRecord,
    SourceKind,
    SyntheticFieldDescriptor,
)


_ALLOWED_FAILURE_CODES = frozenset({"parse_failed", "ocr_failed"})


class _SyntheticFakeExtractor:
    source_kind: SourceKind
    extractor_version: str

    def __init__(self, failure_code: str | None = None) -> None:
        if failure_code is not None and failure_code not in _ALLOWED_FAILURE_CODES:
            raise ValueError("fake_extractor_failure_code_invalid")
        self._failure_code = failure_code

    def extract(
        self,
        source_file: SourceFileRecord,
        fields: Tuple[SyntheticFieldDescriptor, ...],
    ) -> Tuple[SyntheticFieldDescriptor, ...]:
        if not isinstance(source_file, SourceFileRecord):
            raise IngestionBoundaryError("source_file_required")
        if source_file.source_kind is not self.source_kind:
            raise IngestionBoundaryError("extractor_source_kind_mismatch")
        if source_file.disposition is not SourceDisposition.REGISTERED:
            raise IngestionBoundaryError("source_quarantined")
        if (
            source_file.is_synthetic is not True
            or source_file.external_execution_allowed is not False
            or source_file.business_external_ready is not False
        ):
            raise IngestionBoundaryError("synthetic_input_required")
        if not isinstance(fields, tuple):
            raise IngestionBoundaryError("synthetic_fields_required")
        if self._failure_code is not None:
            raise IngestionBoundaryError(self._failure_code)
        return fields


class XlsxFakeExtractor(_SyntheticFakeExtractor):
    source_kind = SourceKind.XLSX
    extractor_version = "fake_xlsx_v1"


class CsvFakeExtractor(_SyntheticFakeExtractor):
    source_kind = SourceKind.CSV
    extractor_version = "fake_csv_v1"


class DocxFakeExtractor(_SyntheticFakeExtractor):
    source_kind = SourceKind.DOCX
    extractor_version = "fake_docx_v1"


class PdfFakeExtractor(_SyntheticFakeExtractor):
    source_kind = SourceKind.PDF
    extractor_version = "fake_pdf_v1"


class ImageFakeExtractor(_SyntheticFakeExtractor):
    source_kind = SourceKind.IMAGE
    extractor_version = "fake_image_v1"


class FolderFakeExtractor(_SyntheticFakeExtractor):
    source_kind = SourceKind.FOLDER
    extractor_version = "fake_folder_v1"


class JsonExportFakeExtractor(_SyntheticFakeExtractor):
    source_kind = SourceKind.JSON_EXPORT
    extractor_version = "fake_json_export_v1"


_EXTRACTOR_TYPES = {
    SourceKind.XLSX: XlsxFakeExtractor,
    SourceKind.CSV: CsvFakeExtractor,
    SourceKind.DOCX: DocxFakeExtractor,
    SourceKind.PDF: PdfFakeExtractor,
    SourceKind.IMAGE: ImageFakeExtractor,
    SourceKind.FOLDER: FolderFakeExtractor,
    SourceKind.JSON_EXPORT: JsonExportFakeExtractor,
}


def fake_extractor_registry(
    *,
    failure_by_kind: Mapping[SourceKind, str] | None = None,
) -> dict[SourceKind, _SyntheticFakeExtractor]:
    """Return all seven local fakes with optional deterministic failure probes."""

    failures = dict(failure_by_kind or {})
    unknown = set(failures) - set(_EXTRACTOR_TYPES)
    if unknown:
        raise ValueError("fake_extractor_source_kind_invalid")
    return {
        source_kind: extractor_type(failures.get(source_kind))
        for source_kind, extractor_type in _EXTRACTOR_TYPES.items()
    }


__all__ = [
    "CsvFakeExtractor",
    "DocxFakeExtractor",
    "FolderFakeExtractor",
    "ImageFakeExtractor",
    "JsonExportFakeExtractor",
    "PdfFakeExtractor",
    "XlsxFakeExtractor",
    "fake_extractor_registry",
]
