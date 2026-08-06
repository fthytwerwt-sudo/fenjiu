"""Port contract for value-free synthetic extraction fakes."""

from __future__ import annotations

from typing import Protocol, Tuple

from modules.ingestion.contracts import (
    SourceFileRecord,
    SourceKind,
    SyntheticFieldDescriptor,
)


class ExtractorPort(Protocol):
    source_kind: SourceKind
    extractor_version: str

    def extract(
        self,
        source_file: SourceFileRecord,
        fields: Tuple[SyntheticFieldDescriptor, ...],
    ) -> Tuple[SyntheticFieldDescriptor, ...]:
        """Return value-free descriptors or raise a stable boundary error."""


__all__ = ["ExtractorPort"]
