"""Application workflow for P06-03 support takeover cases."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from core.contracts import DataState
from core.security import disabled_feature_flag_snapshot
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
from modules.customer_service.takeover import (
    HumanDecision,
    SupportCaseQueue,
    SupportCaseReceipt,
    SupportCaseState,
    SupportReviewCase,
    SupportTakeoverBoundaryError,
    SupportZeroSendProof,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _boundary(code: str) -> SupportTakeoverBoundaryError:
    return SupportTakeoverBoundaryError(code)


class SupportTakeoverWorkflow:
    """Open support cases, record human decisions, and keep sends impossible."""

    __slots__ = ("_audit_log", "_now", "_queue")

    def __init__(
        self,
        *,
        audit_log: object,
        queue: SupportCaseQueue | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._audit_log = audit_log
        self._now = now or _now_utc
        self._queue = queue or SupportCaseQueue(now=self._now)

    @property
    def queue(self) -> SupportCaseQueue:
        return self._queue

    def open_case(self, receipt: object, outcome: object, *, actor_ref: str) -> SupportCaseReceipt:
        case_receipt = self._queue.open_case(receipt, outcome, actor_ref=actor_ref)
        if not case_receipt.replayed:
            self._record(
                event_kind="support_case_opened",
                case=case_receipt.case,
                actor_ref=actor_ref,
                result_code=case_receipt.case.state.value,
                metadata={
                    "item_count": len(case_receipt.case.fact_version_ids),
                    "reason_code": case_receipt.case.handoff_reason_code or "draft_only",
                    "send_count": 0,
                },
            )
        return case_receipt

    def apply_human_decision(
        self,
        case_ref: str,
        *,
        action: HumanDecision,
        actor_ref: str,
        evidence_ref: str,
        idempotency_key: str,
        revision_ref: str | None = None,
        approval_request_ref: str | None = None,
        approval_decision_ref: str | None = None,
    ) -> SupportReviewCase:
        case = self._queue.apply_decision(
            case_ref,
            action=action,
            actor_ref=actor_ref,
            evidence_ref=evidence_ref,
            idempotency_key=idempotency_key,
            revision_ref=revision_ref,
            approval_request_ref=approval_request_ref,
            approval_decision_ref=approval_decision_ref,
        )
        self._record(
            event_kind="support_human_decision",
            case=case,
            actor_ref=actor_ref,
            result_code=case.state.value,
            metadata={"reason_code": action.value, "send_count": 0},
        )
        return case

    def resume_case(
        self,
        case_ref: str,
        *,
        actor_ref: str,
        evidence_ref: str,
        idempotency_key: str,
    ) -> SupportReviewCase:
        case = self._queue.resume_case(
            case_ref,
            actor_ref=actor_ref,
            evidence_ref=evidence_ref,
            idempotency_key=idempotency_key,
        )
        self._record(
            event_kind="support_resume_recorded",
            case=case,
            actor_ref=actor_ref,
            result_code=case.state.value,
            metadata={"reason_code": "explicit_resume", "send_count": 0},
        )
        return case

    def invalidate_on_fact_change(
        self,
        case_ref: str,
        *,
        invalidated_version_ids: tuple[str, ...],
        current_policy_version: str,
        actor_ref: str,
    ) -> SupportReviewCase:
        before = self._case(case_ref)
        after = self._queue.invalidate_on_fact_change(
            case_ref,
            invalidated_version_ids=invalidated_version_ids,
            current_policy_version=current_policy_version,
        )
        if after != before:
            self._record(
                event_kind="support_case_invalidated",
                case=after,
                actor_ref=actor_ref,
                result_code=after.invalidation_reason or "invalidated",
                metadata={"reason_code": after.invalidation_reason or "invalidated", "send_count": 0},
            )
        return after

    def zero_send_proof(self) -> SupportZeroSendProof:
        return self._queue.zero_send_proof()

    def safe_case_summaries(self) -> tuple[dict[str, object], ...]:
        return tuple(case.safe_summary() for case in self._queue.cases)

    def _case(self, case_ref: str) -> SupportReviewCase:
        for case in self._queue.cases:
            if case.case_ref == case_ref:
                return case
        raise _boundary("support_case_not_found")

    def _record(
        self,
        *,
        event_kind: str,
        case: SupportReviewCase,
        actor_ref: str,
        result_code: str,
        metadata: dict[str, object],
    ) -> None:
        record = getattr(self._audit_log, "record", None)
        if not callable(record):
            raise _boundary("audit_persistence_required")
        record(
            event_kind=event_kind,
            actor_ref=actor_ref,
            scope=case.scope,
            command_ref="support.takeover.workflow",
            target_ref=case.case_ref,
            policy_version=case.policy_version,
            subject_version=case.subject_version,
            result_code=result_code,
            metadata=metadata,
        )


class SupportDraftApprovalCoordinator:
    """Bind human support draft approval to P04 policy without adding sending."""

    __slots__ = ("_now",)

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or _now_utc

    def request_approval(
        self,
        case: SupportReviewCase,
        *,
        approval_service: ActionApprovalService,
        creator: PolicyActor,
        expires_at: datetime,
        idempotency_key: str,
    ) -> ActionApprovalRequest:
        if not isinstance(case, SupportReviewCase):
            raise _boundary("support_case_required")
        if case.state not in {SupportCaseState.DRAFT_ONLY, SupportCaseState.HUMAN_REVISED}:
            raise _boundary("support_case_state_required")
        if case.draft_ref is None:
            raise _boundary("draft_ref_required")
        return approval_service.request_approval(
            self._policy_request(
                case,
                actor=creator,
                phase=PolicyPhase.REQUEST,
                approval_state=ApprovalState.PENDING,
                evaluated_at=self._now(),
            ),
            idempotency_key=idempotency_key,
            creator_actor_ref=creator.actor_ref,
            expires_at=expires_at,
        )

    def approve_case(
        self,
        case: SupportReviewCase,
        *,
        workflow: SupportTakeoverWorkflow,
        approval_service: ActionApprovalService,
        request_id: str,
        reviewer: PolicyActor,
        evidence_ref: str,
        idempotency_key: str,
    ) -> SupportReviewCase:
        if not isinstance(case, SupportReviewCase):
            raise _boundary("support_case_required")
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
                case,
                actor=reviewer,
                phase=PolicyPhase.EXECUTION,
                approval_state=ApprovalState.APPROVED,
                evaluated_at=self._now(),
            ),
        )
        if not recheck.allowed:
            raise _boundary(recheck.error_code or "policy_denied")
        return workflow.apply_human_decision(
            case.case_ref,
            action=HumanDecision.APPROVE,
            actor_ref=reviewer.actor_ref,
            evidence_ref=evidence_ref,
            idempotency_key="workflow:" + idempotency_key,
            approval_request_ref=request_id,
            approval_decision_ref=decision.id,
        )

    def _policy_request(
        self,
        case: SupportReviewCase,
        *,
        actor: PolicyActor,
        phase: PolicyPhase,
        approval_state: ApprovalState,
        evaluated_at: datetime,
    ) -> PolicyRequest:
        return PolicyRequest(
            actor=actor,
            action=ActionName.APPROVE_SUPPORT_DRAFT,
            phase=phase,
            scope=case.scope,
            target_ref=case.case_ref,
            data_state=DataState.FIXTURE,
            approval_state=approval_state,
            fact_observed_at=case.created_at,
            fact_ttl=timedelta(hours=1),
            required_evidence_refs=case.evidence_refs or ("support_evidence_ref",),
            feature_flag_snapshot=disabled_feature_flag_snapshot(),
            dnc_blocked=False,
            consent_granted=True,
            environment=Environment.LOCAL,
            evaluated_at=evaluated_at,
            policy_version=case.policy_version,
            correlation_id=case.scope.correlation_id,
            subject_version=case.subject_version,
        )


__all__ = [
    "SupportDraftApprovalCoordinator",
    "SupportTakeoverWorkflow",
]
