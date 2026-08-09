"""Shared P05 lead/CRM contracts that stay below module boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import re

from core.contracts.errors import ContractValidationError
from core.contracts.metadata import DataState
from core.contracts.scope import ScopeRef


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)


class LeadDomainError(ContractValidationError):
    """Stable, value-free P05-02 lead boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class LeadReviewDecision(str, Enum):
    APPROVE = "approved"
    REJECT = "rejected"
    MERGE_CANDIDATE = "merge_candidate"


def _boundary(code: str) -> LeadDomainError:
    return LeadDomainError(code)


def _reject_sensitive_text(value: object) -> None:
    if isinstance(value, str) and _SENSITIVE.search(value) is not None:
        raise _boundary("sensitive_metadata_forbidden")


def require_identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _boundary(code)
    _reject_sensitive_text(value)
    return value


def require_hash(value: object, code: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise _boundary(code)
    return value


def require_scope(value: object) -> ScopeRef:
    if not isinstance(value, ScopeRef):
        raise _boundary("scope_required")
    require_identifier(value.correlation_id, "correlation_id_required")
    return value


def require_time(value: object, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _boundary(code)
    return value


def require_synthetic_fixture_boundary(
    *,
    data_state: object,
    is_synthetic: object,
    external_execution_allowed: object,
    business_external_ready: object,
) -> None:
    if data_state is not DataState.FIXTURE:
        raise _boundary("fixture_data_state_required")
    if is_synthetic is not True:
        raise _boundary("synthetic_input_required")
    if external_execution_allowed is not False:
        raise _boundary("external_execution_forbidden")
    if business_external_ready is not False:
        raise _boundary("business_external_ready_forbidden")


def stable_ref(prefix: str, *parts: object) -> str:
    require_identifier(prefix, "ref_prefix_required")
    digest = sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    return f"{prefix}:{digest[:32]}"


@dataclass(frozen=True)
class SyntheticLeadCandidate:
    """Value-free synthetic public-business candidate from reviewed source evidence."""

    scope: ScopeRef
    lead_ref: str
    source_policy_id: str
    snapshot_ref: str
    source_url_hash: str
    organization_fingerprint: str
    field_fingerprint_hash: str
    evidence_refs: tuple[str, ...]
    observed_at: datetime
    identity_confidence: str
    data_state: DataState
    is_synthetic: bool
    external_execution_allowed: bool
    business_external_ready: bool

    def __post_init__(self) -> None:
        require_scope(self.scope)
        require_identifier(self.lead_ref, "lead_ref_required")
        require_identifier(self.source_policy_id, "source_policy_required")
        require_identifier(self.snapshot_ref, "snapshot_ref_required")
        require_hash(self.source_url_hash, "source_url_hash_required")
        require_hash(self.organization_fingerprint, "organization_fingerprint_required")
        require_hash(self.field_fingerprint_hash, "field_fingerprint_required")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise _boundary("source_evidence_required")
        for evidence_ref in self.evidence_refs:
            require_identifier(evidence_ref, "source_evidence_required")
        require_time(self.observed_at, "observed_at_required")
        require_identifier(self.identity_confidence, "identity_confidence_required")
        require_synthetic_fixture_boundary(
            data_state=self.data_state,
            is_synthetic=self.is_synthetic,
            external_execution_allowed=self.external_execution_allowed,
            business_external_ready=self.business_external_ready,
        )

    @property
    def dnc_subject_hash(self) -> str:
        return self.organization_fingerprint

    def safe_summary(self) -> dict[str, object]:
        return {
            "lead_ref": self.lead_ref,
            "source_policy_id": self.source_policy_id,
            "snapshot_ref": self.snapshot_ref,
            "source_url_hash": self.source_url_hash,
            "organization_fingerprint": self.organization_fingerprint,
            "field_fingerprint_hash": self.field_fingerprint_hash,
            "evidence_refs": self.evidence_refs,
            "observed_at": self.observed_at.isoformat(),
            "identity_confidence": self.identity_confidence,
            "data_state": self.data_state.value,
            "is_synthetic": self.is_synthetic,
            "external_execution_allowed": self.external_execution_allowed,
            "business_external_ready": self.business_external_ready,
        }


@dataclass(frozen=True)
class LeadDedupeResult:
    result: str
    reason_codes: tuple[str, ...]
    matched_ref: str | None = None

    def __post_init__(self) -> None:
        if self.result not in {"new", "duplicate", "merge_candidate"}:
            raise _boundary("dedupe_result_required")
        if not self.reason_codes:
            raise _boundary("dedupe_reason_required")
        for reason_code in self.reason_codes:
            require_identifier(reason_code, "dedupe_reason_required")
        if self.matched_ref is not None:
            require_identifier(self.matched_ref, "dedupe_match_ref_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "result": self.result,
            "reason_codes": self.reason_codes,
            "matched_ref": self.matched_ref,
        }


@dataclass(frozen=True)
class LeadReview:
    review_ref: str
    candidate: SyntheticLeadCandidate
    decision: LeadReviewDecision
    reviewer_ref: str
    review_evidence_ref: str
    dedupe_result: LeadDedupeResult
    reviewed_at: datetime

    def __post_init__(self) -> None:
        require_identifier(self.review_ref, "review_ref_required")
        if not isinstance(self.candidate, SyntheticLeadCandidate):
            raise _boundary("lead_candidate_required")
        if not isinstance(self.decision, LeadReviewDecision):
            raise _boundary("review_decision_required")
        require_identifier(self.reviewer_ref, "reviewer_ref_required")
        require_identifier(self.review_evidence_ref, "review_evidence_required")
        if not isinstance(self.dedupe_result, LeadDedupeResult):
            raise _boundary("dedupe_result_required")
        require_time(self.reviewed_at, "reviewed_at_required")

    @property
    def scope(self) -> ScopeRef:
        return self.candidate.scope

    def safe_summary(self) -> dict[str, object]:
        return {
            "review_ref": self.review_ref,
            "lead_ref": self.candidate.lead_ref,
            "decision": self.decision.value,
            "reviewer_ref": self.reviewer_ref,
            "review_evidence_ref": self.review_evidence_ref,
            "dedupe_result": self.dedupe_result.safe_summary(),
            "reviewed_at": self.reviewed_at.isoformat(),
        }


__all__ = [
    "LeadDedupeResult",
    "LeadDomainError",
    "LeadReview",
    "LeadReviewDecision",
    "SyntheticLeadCandidate",
    "require_hash",
    "require_identifier",
    "require_scope",
    "require_synthetic_fixture_boundary",
    "require_time",
    "stable_ref",
]
