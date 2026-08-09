"""P05-02 lead-domain exports for the leads module boundary."""

from core.contracts.leads_crm import (
    LeadDedupeResult,
    LeadDomainError,
    LeadReview,
    LeadReviewDecision,
    SyntheticLeadCandidate,
)

__all__ = [
    "LeadDedupeResult",
    "LeadDomainError",
    "LeadReview",
    "LeadReviewDecision",
    "SyntheticLeadCandidate",
]
