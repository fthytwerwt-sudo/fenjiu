"""Application approval coordinator for P05-03 outreach drafts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone

from core.contracts import DataState
from core.security.action_policy import (
    ActionApprovalRequest,
    ActionApprovalService,
    ActionName,
    ApprovalAction,
    ApprovalState,
    Environment,
    PolicyActor,
    PolicyPhase,
    PolicyRequest,
)
from core.security.isolation import disabled_feature_flag_snapshot
from modules.crm.outreach import OutreachBoundaryError, OutreachDraft, OutreachDraftState
from modules.crm.domain import DncRegistry


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _boundary(code: str) -> OutreachBoundaryError:
    return OutreachBoundaryError(code)


class OutreachDraftApprovalCoordinator:
    """Bind draft approval to P04 policy without adding any send surface."""

    __slots__ = ("_dnc", "_now")

    def __init__(
        self,
        *,
        dnc_registry: DncRegistry,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._dnc = dnc_registry
        self._now = now or _now_utc

    def request_approval(
        self,
        draft: OutreachDraft,
        *,
        approval_service: ActionApprovalService,
        creator: PolicyActor,
        expires_at: datetime,
        idempotency_key: str,
    ) -> ActionApprovalRequest:
        if not isinstance(draft, OutreachDraft):
            raise _boundary("draft_required")
        if draft.state is not OutreachDraftState.DRAFT_ONLY:
            raise _boundary("draft_state_required")
        return approval_service.request_approval(
            self._policy_request(
                draft,
                actor=creator,
                phase=PolicyPhase.REQUEST,
                approval_state=ApprovalState.PENDING,
                evaluated_at=self._now(),
            ),
            idempotency_key=idempotency_key,
            creator_actor_ref=creator.actor_ref,
            expires_at=expires_at,
        )

    def approve_draft(
        self,
        draft: OutreachDraft,
        *,
        approval_service: ActionApprovalService,
        request_id: str,
        reviewer: PolicyActor,
        evidence_ref: str,
        idempotency_key: str,
    ) -> OutreachDraft:
        if not isinstance(draft, OutreachDraft):
            raise _boundary("draft_required")
        decision = approval_service.decide(
            request_id,
            action=ApprovalAction.APPROVE,
            reviewer=reviewer,
            evidence_ref=evidence_ref,
            idempotency_key=idempotency_key,
        )
        recheck = approval_service.pre_execution_recheck(
            request_id,
            self._policy_request(
                draft,
                actor=reviewer,
                phase=PolicyPhase.EXECUTION,
                approval_state=ApprovalState.APPROVED,
                evaluated_at=self._now(),
            ),
        )
        if not recheck.allowed:
            raise _boundary(recheck.error_code or "policy_denied")
        return replace(
            draft,
            state=OutreachDraftState.APPROVED_INTERNAL,
            approval_request_ref=request_id,
            approval_decision_ref=decision.id,
        )

    def _policy_request(
        self,
        draft: OutreachDraft,
        *,
        actor: PolicyActor,
        phase: PolicyPhase,
        approval_state: ApprovalState,
        evaluated_at: datetime,
    ) -> PolicyRequest:
        return PolicyRequest(
            actor=actor,
            action=ActionName.APPROVE_OUTREACH_DRAFT,
            phase=phase,
            scope=draft.scope,
            target_ref=draft.draft_ref,
            data_state=DataState.FIXTURE,
            approval_state=approval_state,
            fact_observed_at=draft.fact_observed_at,
            fact_ttl=draft.fact_expires_at - draft.fact_observed_at,
            required_evidence_refs=draft.evidence_refs,
            feature_flag_snapshot=disabled_feature_flag_snapshot(),
            dnc_blocked=self._dnc.is_blocked(draft.scope, draft.subject_hash),
            consent_granted=True,
            environment=Environment.LOCAL,
            evaluated_at=evaluated_at,
            policy_version=draft.policy_version,
            correlation_id=draft.scope.correlation_id,
            subject_version=draft.subject_version,
        )


__all__ = ["OutreachDraftApprovalCoordinator"]
