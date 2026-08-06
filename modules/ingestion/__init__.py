"""Synthetic-only ingestion contracts and staging pipeline."""

from modules.ingestion.contracts import (
    FailureStage,
    ExtractionResultRecord,
    FieldLocator,
    IngestionBoundaryError,
    IngestionFailureRecord,
    IngestionJobRecord,
    IngestionOutcome,
    IngestionOutcomeState,
    IngestionWorkflowState,
    PrivateStorageLocator,
    RegisterSourceCommand,
    SourceDisposition,
    SourceFileRecord,
    SourceKind,
    StagingCandidateRecord,
    SyntheticFieldDescriptor,
)
from modules.ingestion.pipeline import IngestionPipeline
from modules.ingestion.ports import ExtractorPort
from modules.ingestion.store import InMemoryIngestionStore

__all__ = [
    "FailureStage",
    "ExtractionResultRecord",
    "ExtractorPort",
    "FieldLocator",
    "InMemoryIngestionStore",
    "IngestionBoundaryError",
    "IngestionFailureRecord",
    "IngestionJobRecord",
    "IngestionOutcome",
    "IngestionOutcomeState",
    "IngestionPipeline",
    "IngestionWorkflowState",
    "PrivateStorageLocator",
    "RegisterSourceCommand",
    "SourceDisposition",
    "SourceFileRecord",
    "SourceKind",
    "StagingCandidateRecord",
    "SyntheticFieldDescriptor",
]
