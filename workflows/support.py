"""Thin P06-03 support workflow facade."""

from __future__ import annotations

from core.application import SupportTakeoverWorkflow


def safe_support_case_summaries(workflow: SupportTakeoverWorkflow) -> tuple[dict[str, object], ...]:
    """Return admin-safe support case summaries without raw customer text."""

    return workflow.safe_case_summaries()


__all__ = ["safe_support_case_summaries"]
