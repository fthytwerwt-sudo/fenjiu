"""Local fake extraction adapters with no object-store or parser client."""

from adapters.storage.fake_extractors import (
    CsvFakeExtractor,
    DocxFakeExtractor,
    FolderFakeExtractor,
    ImageFakeExtractor,
    JsonExportFakeExtractor,
    PdfFakeExtractor,
    XlsxFakeExtractor,
    fake_extractor_registry,
)

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
