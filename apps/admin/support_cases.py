"""Minimal admin facade for P06-03 support review cases."""

from __future__ import annotations

from dataclasses import dataclass

from core.application import SupportTakeoverWorkflow
from modules.customer_service import HumanDecision, SupportReviewCase


@dataclass(frozen=True)
class SupportAdminDecisionCommand:
    case_ref: str
    action: HumanDecision
    actor_ref: str
    evidence_ref: str
    idempotency_key: str
    revision_ref: str | None = None


@dataclass(frozen=True)
class SupportAdminResumeCommand:
    case_ref: str
    actor_ref: str
    evidence_ref: str
    idempotency_key: str


class SupportAdminConsole:
    """Local-only admin shell for review decisions; no channel or sender access."""

    def list_cases(self, workflow: SupportTakeoverWorkflow) -> tuple[dict[str, object], ...]:
        return workflow.safe_case_summaries()

    def apply_decision(
        self,
        workflow: SupportTakeoverWorkflow,
        command: SupportAdminDecisionCommand,
    ) -> SupportReviewCase:
        return workflow.apply_human_decision(
            command.case_ref,
            action=command.action,
            actor_ref=command.actor_ref,
            evidence_ref=command.evidence_ref,
            idempotency_key=command.idempotency_key,
            revision_ref=command.revision_ref,
        )

    def resume_case(
        self,
        workflow: SupportTakeoverWorkflow,
        command: SupportAdminResumeCommand,
    ) -> SupportReviewCase:
        return workflow.resume_case(
            command.case_ref,
            actor_ref=command.actor_ref,
            evidence_ref=command.evidence_ref,
            idempotency_key=command.idempotency_key,
        )


__all__ = ["SupportAdminConsole", "SupportAdminDecisionCommand", "SupportAdminResumeCommand"]
