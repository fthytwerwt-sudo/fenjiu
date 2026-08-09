"""P04-02 scoped RBAC, approval, and action-policy contract probes."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import json
import unittest
from uuid import UUID

from core.contracts import DataState, synthetic_scope
from core.security import FeatureFlagName, disabled_feature_flag_snapshot
from core.security.action_policy import (
    ActionApprovalService,
    ActionName,
    ActionPolicy,
    ActionPolicyError,
    ActorRole,
    ApprovalAction,
    ApprovalState,
    Environment,
    PolicyActor,
    PolicyPhase,
    PolicyRequest,
)


NOW = datetime(2040, 4, 5, tzinfo=timezone.utc)
SCOPE = synthetic_scope()


class Clock:
    def __init__(self) -> None:
        self.current = NOW

    def __call__(self) -> datetime:
        result = self.current
        self.current = self.current + timedelta(seconds=1)
        return result


def actor(
    role: ActorRole | str,
    *,
    actor_ref: str = "actor_data_reviewer",
    scope=SCOPE,
) -> PolicyActor:
    return PolicyActor(actor_ref=actor_ref, role=role, scope=scope)


def flags_with(flag: FeatureFlagName) -> tuple[tuple[str, bool], ...]:
    values = dict(disabled_feature_flag_snapshot())
    values[flag.value] = True
    return tuple(sorted(values.items()))


def policy_request(
    *,
    action: ActionName = ActionName.EXPORT_CONTENT_INTERNAL,
    phase: PolicyPhase = PolicyPhase.EXECUTION,
    actor_ref: PolicyActor | None = None,
    scope=SCOPE,
    data_state: DataState = DataState.APPROVED,
    approval_state: ApprovalState = ApprovalState.APPROVED,
    fact_observed_at: datetime | None = None,
    required_evidence_refs: tuple[str, ...] = ("evidence_ref_1",),
    feature_flag_snapshot: tuple[tuple[str, bool], ...] | None = None,
    dnc_blocked: bool = False,
    consent_granted: bool = True,
    environment: Environment = Environment.LOCAL,
    policy_version: str = "action_policy_v1",
    target_ref: str = "target_ref_1",
) -> PolicyRequest:
    return PolicyRequest(
        actor=actor_ref or actor(ActorRole.CONTENT_REVIEWER, actor_ref="content_reviewer_1"),
        action=action,
        phase=phase,
        scope=scope,
        target_ref=target_ref,
        data_state=data_state,
        approval_state=approval_state,
        fact_observed_at=fact_observed_at or (NOW - timedelta(minutes=5)),
        fact_ttl=timedelta(hours=1),
        required_evidence_refs=required_evidence_refs,
        feature_flag_snapshot=feature_flag_snapshot or disabled_feature_flag_snapshot(),
        dnc_blocked=dnc_blocked,
        consent_granted=consent_granted,
        environment=environment,
        evaluated_at=NOW,
        policy_version=policy_version,
        correlation_id=scope.correlation_id,
        subject_version=1,
    )


class ActionPolicyRbacApprovalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = ActionPolicy()
        self.clock = Clock()
        self.service = ActionApprovalService(policy=self.policy, now=self.clock)

    def assert_denied(self, request_or_decision: PolicyRequest, code: str):
        if hasattr(request_or_decision, "allowed") and hasattr(request_or_decision, "error_code"):
            decision = request_or_decision
        else:
            decision = self.policy.evaluate(request_or_decision)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, code)
        self.assertEqual(decision.policy_result, "denied")
        return decision

    def test_role_action_matrix_covers_required_roles_and_forbidden_actions(self) -> None:
        matrix = self.policy.role_action_matrix()

        self.assertEqual(
            set(matrix),
            {
                ActorRole.SYSTEM_WORKER.value,
                ActorRole.DATA_REVIEWER.value,
                ActorRole.CONTENT_REVIEWER.value,
                ActorRole.SUPPORT_AGENT.value,
                ActorRole.PROJECT_OWNER.value,
                ActorRole.AUDITOR.value,
            },
        )
        self.assertIn(ActionName.RUN_INTERNAL_WORKFLOW.value, matrix[ActorRole.SYSTEM_WORKER.value])
        self.assertNotIn(ActionName.APPROVE_DATA_CANDIDATE.value, matrix[ActorRole.SYSTEM_WORKER.value])
        self.assertEqual(matrix[ActorRole.AUDITOR.value], (ActionName.READ_AUDIT.value,))

        for forbidden in (
            ActionName.EXTERNAL_SEND,
            ActionName.CONTENT_PUBLISH,
            ActionName.PRICE_QUOTE,
            ActionName.PAYMENT,
            ActionName.ORDER,
            ActionName.REFUND,
            ActionName.INVENTORY_WRITE,
        ):
            with self.subTest(action=forbidden.value):
                decision = self.assert_denied(
                    policy_request(
                        action=forbidden,
                        actor_ref=actor(ActorRole.PROJECT_OWNER, actor_ref="project_owner_1"),
                    ),
                    "external_action_forbidden",
                )
                self.assertTrue(decision.external_execution_attempted)

    def test_policy_denies_unknown_role_cross_scope_insufficient_role_and_missing_evidence(self) -> None:
        self.assert_denied(
            policy_request(actor_ref=actor("unknown_role", actor_ref="unknown_actor")),
            "actor_role_unknown",
        )

        other_scope = replace(
            SCOPE,
            business_line_id=UUID(int=SCOPE.business_line_id.int + 1),
            correlation_id="other_scope_correlation",
        )
        self.assert_denied(
            policy_request(
                actor_ref=actor(ActorRole.CONTENT_REVIEWER, scope=other_scope),
            ),
            "cross_scope_forbidden",
        )

        self.assert_denied(
            policy_request(actor_ref=actor(ActorRole.AUDITOR, actor_ref="auditor_1")),
            "role_not_permitted",
        )

        self.assert_denied(
            policy_request(required_evidence_refs=()),
            "required_evidence_missing",
        )

    def test_policy_denies_state_freshness_dnc_consent_flag_and_environment_failures(self) -> None:
        self.assert_denied(
            policy_request(data_state=DataState.STAGING),
            "data_state_not_approved",
        )
        self.assert_denied(
            policy_request(fact_observed_at=NOW - timedelta(hours=2)),
            "fact_stale",
        )
        self.assert_denied(
            policy_request(
                action=ActionName.APPLY_SUPPORT_DRAFT,
                actor_ref=actor(ActorRole.SUPPORT_AGENT, actor_ref="support_agent_1"),
                dnc_blocked=True,
            ),
            "dnc_blocked",
        )
        self.assert_denied(
            policy_request(
                action=ActionName.APPLY_SUPPORT_DRAFT,
                actor_ref=actor(ActorRole.SUPPORT_AGENT, actor_ref="support_agent_1"),
                consent_granted=False,
            ),
            "consent_required",
        )
        self.assert_denied(
            policy_request(
                action=ActionName.APPLY_SUPPORT_DRAFT,
                actor_ref=actor(ActorRole.SUPPORT_AGENT, actor_ref="support_agent_1"),
            ),
            "feature_flag_disabled",
        )
        self.assert_denied(
            policy_request(environment=Environment.PRODUCTION),
            "environment_forbidden",
        )

    def test_high_risk_approval_flow_requires_separate_reviewer_and_execution_recheck(self) -> None:
        creator = actor(
            ActorRole.CONTENT_REVIEWER,
            actor_ref="content_creator_1",
        )
        request = self.service.request_approval(
            policy_request(
                phase=PolicyPhase.REQUEST,
                actor_ref=creator,
                approval_state=ApprovalState.PENDING,
                target_ref="content_task_ref_1",
            ),
            idempotency_key="approval_request_key_1",
            creator_actor_ref=creator.actor_ref,
            expires_at=NOW + timedelta(days=1),
        )
        self.assertEqual(request.state, ApprovalState.PENDING)
        self.assertEqual(request.creator_actor_ref, "content_creator_1")

        with self.assertRaisesRegex(ActionPolicyError, "self_approval_forbidden"):
            self.service.decide(
                request.id,
                action=ApprovalAction.APPROVE,
                reviewer=creator,
                evidence_ref="review_evidence_ref_1",
                idempotency_key="decision_self_key_1",
            )

        reviewer = actor(ActorRole.CONTENT_REVIEWER, actor_ref="content_reviewer_2")
        decision = self.service.decide(
            request.id,
            action=ApprovalAction.APPROVE,
            reviewer=reviewer,
            evidence_ref="review_evidence_ref_1",
            idempotency_key="decision_approve_key_1",
        )
        self.assertEqual(decision.action, ApprovalAction.APPROVE)
        self.assertEqual(self.service.request_state(request.id), ApprovalState.APPROVED)
        self.assertEqual(len(self.service.decisions), 1)

        allowed = self.service.pre_execution_recheck(
            request.id,
            policy_request(
                target_ref="content_task_ref_1",
                actor_ref=reviewer,
                approval_state=ApprovalState.APPROVED,
            ),
        )
        self.assertTrue(allowed.allowed)
        self.assertIsNone(allowed.error_code)

        self.assert_denied(
            self.service.pre_execution_recheck(
                request.id,
                policy_request(
                    target_ref="content_task_ref_1",
                    actor_ref=reviewer,
                    approval_state=ApprovalState.APPROVED,
                    data_state=DataState.EXPIRED,
                ),
            ),
            "data_state_not_approved",
        )
        self.assert_denied(
            self.service.pre_execution_recheck(
                request.id,
                policy_request(
                    target_ref="content_task_ref_1",
                    actor_ref=reviewer,
                    approval_state=ApprovalState.APPROVED,
                    fact_observed_at=NOW - timedelta(hours=2),
                ),
            ),
            "fact_stale",
        )

        support_creator = actor(
            ActorRole.SUPPORT_AGENT,
            actor_ref="support_creator_1",
        )
        support_request = self.service.request_approval(
            policy_request(
                action=ActionName.APPLY_SUPPORT_DRAFT,
                phase=PolicyPhase.REQUEST,
                actor_ref=support_creator,
                approval_state=ApprovalState.PENDING,
                target_ref="support_draft_ref_1",
                feature_flag_snapshot=flags_with(FeatureFlagName.EXTERNAL_SEND),
            ),
            idempotency_key="approval_request_key_support",
            creator_actor_ref=support_creator.actor_ref,
            expires_at=self.clock.current + timedelta(days=1),
        )
        support_reviewer = actor(
            ActorRole.SUPPORT_AGENT,
            actor_ref="support_reviewer_2",
        )
        self.service.decide(
            support_request.id,
            action=ApprovalAction.APPROVE,
            reviewer=support_reviewer,
            evidence_ref="support_review_evidence_ref",
            idempotency_key="decision_support_approve_key",
        )
        self.assertTrue(
            self.service.pre_execution_recheck(
                support_request.id,
                policy_request(
                    action=ActionName.APPLY_SUPPORT_DRAFT,
                    target_ref="support_draft_ref_1",
                    actor_ref=support_reviewer,
                    approval_state=ApprovalState.APPROVED,
                    feature_flag_snapshot=flags_with(FeatureFlagName.EXTERNAL_SEND),
                ),
            ).allowed
        )
        self.assert_denied(
            self.service.pre_execution_recheck(
                support_request.id,
                policy_request(
                    action=ActionName.APPLY_SUPPORT_DRAFT,
                    target_ref="support_draft_ref_1",
                    actor_ref=support_reviewer,
                    approval_state=ApprovalState.APPROVED,
                    feature_flag_snapshot=disabled_feature_flag_snapshot(),
                ),
            ),
            "feature_flag_disabled",
        )

    def test_reject_revise_expire_duplicate_terminal_and_append_only_records(self) -> None:
        reviewer = actor(ActorRole.DATA_REVIEWER, actor_ref="data_reviewer_2")
        rejected = self.service.request_approval(
            policy_request(
                action=ActionName.APPROVE_DATA_CANDIDATE,
                phase=PolicyPhase.REQUEST,
                actor_ref=actor(ActorRole.SYSTEM_WORKER, actor_ref="system_worker_1"),
                data_state=DataState.STAGING,
                approval_state=ApprovalState.PENDING,
                target_ref="candidate_ref_reject",
            ),
            idempotency_key="request_reject_key",
            creator_actor_ref="system_worker_1",
            expires_at=NOW + timedelta(days=1),
        )
        reject_decision = self.service.decide(
            rejected.id,
            action=ApprovalAction.REJECT,
            reviewer=reviewer,
            evidence_ref="reject_evidence_ref",
            idempotency_key="decision_reject_key",
        )

        revised = self.service.request_approval(
            policy_request(
                action=ActionName.APPROVE_DATA_CANDIDATE,
                phase=PolicyPhase.REQUEST,
                actor_ref=actor(ActorRole.SYSTEM_WORKER, actor_ref="system_worker_2"),
                data_state=DataState.STAGING,
                approval_state=ApprovalState.PENDING,
                target_ref="candidate_ref_revise",
            ),
            idempotency_key="request_revise_key",
            creator_actor_ref="system_worker_2",
            expires_at=NOW + timedelta(days=1),
        )
        revise_decision = self.service.decide(
            revised.id,
            action=ApprovalAction.REVISE,
            reviewer=reviewer,
            evidence_ref="revise_evidence_ref",
            idempotency_key="decision_revise_key",
            revision_ref="revision_ref_1",
        )

        expiring = self.service.request_approval(
            policy_request(
                action=ActionName.APPROVE_DATA_CANDIDATE,
                phase=PolicyPhase.REQUEST,
                actor_ref=actor(ActorRole.SYSTEM_WORKER, actor_ref="system_worker_3"),
                data_state=DataState.STAGING,
                approval_state=ApprovalState.PENDING,
                target_ref="candidate_ref_expire",
            ),
            idempotency_key="request_expire_key",
            creator_actor_ref="system_worker_3",
            expires_at=self.clock.current + timedelta(seconds=1),
        )
        self.clock.current = NOW + timedelta(minutes=5)
        expire_decision = self.service.expire(
            expiring.id,
            actor_ref="expiry_worker",
            idempotency_key="decision_expire_key",
        )

        self.assertEqual(reject_decision.action, ApprovalAction.REJECT)
        self.assertEqual(revise_decision.action, ApprovalAction.REVISE)
        self.assertEqual(expire_decision.action, ApprovalAction.EXPIRE)
        self.assertEqual(self.service.request_state(rejected.id), ApprovalState.REJECTED)
        self.assertEqual(self.service.request_state(revised.id), ApprovalState.REVISED)
        self.assertEqual(self.service.request_state(expiring.id), ApprovalState.EXPIRED)

        with self.assertRaisesRegex(ActionPolicyError, "duplicate_decision"):
            self.service.decide(
                rejected.id,
                action=ApprovalAction.APPROVE,
                reviewer=reviewer,
                evidence_ref="late_evidence_ref",
                idempotency_key="decision_late_key",
            )
        with self.assertRaisesRegex(ActionPolicyError, "revision_ref_required"):
            pending = self.service.request_approval(
                policy_request(
                    action=ActionName.APPROVE_DATA_CANDIDATE,
                    phase=PolicyPhase.REQUEST,
                    actor_ref=actor(ActorRole.SYSTEM_WORKER, actor_ref="system_worker_4"),
                    data_state=DataState.STAGING,
                    approval_state=ApprovalState.PENDING,
                    target_ref="candidate_ref_revise_missing",
                ),
                idempotency_key="request_revise_missing_key",
                creator_actor_ref="system_worker_4",
                expires_at=NOW + timedelta(days=1),
            )
            self.service.decide(
                pending.id,
                action=ApprovalAction.REVISE,
                reviewer=reviewer,
                evidence_ref="revise_missing_evidence_ref",
                idempotency_key="decision_revise_missing_key",
            )

        self.assertEqual(
            [decision.action for decision in self.service.decisions[:3]],
            [ApprovalAction.REJECT, ApprovalAction.REVISE, ApprovalAction.EXPIRE],
        )
        self.assertEqual(
            [event.sequence for event in self.service.audit_events],
            list(range(1, len(self.service.audit_events) + 1)),
        )
        with self.assertRaises(FrozenInstanceError):
            self.service.decisions[0].evidence_ref = "changed"
        self.assertFalse(hasattr(self.service, "update"))
        self.assertFalse(hasattr(self.service, "delete"))

    def test_public_helpers_cannot_bypass_policy_approval_or_audit_safety(self) -> None:
        reviewer = actor(ActorRole.CONTENT_REVIEWER, actor_ref="content_reviewer_3")
        request = self.service.request_approval(
            policy_request(
                phase=PolicyPhase.REQUEST,
                actor_ref=actor(ActorRole.SYSTEM_WORKER, actor_ref="system_worker_5"),
                approval_state=ApprovalState.PENDING,
                target_ref="content_task_ref_bypass",
            ),
            idempotency_key="request_bypass_key",
            creator_actor_ref="system_worker_5",
            expires_at=NOW + timedelta(days=1),
        )
        with self.assertRaisesRegex(ActionPolicyError, "approval_not_approved"):
            self.service.pre_execution_recheck(
                request.id,
                policy_request(
                    actor_ref=reviewer,
                    approval_state=ApprovalState.APPROVED,
                    target_ref="content_task_ref_bypass",
                ),
            )

        self.assertFalse(hasattr(self.service, "approve_without_policy"))
        self.assertFalse(hasattr(self.service, "record_decision"))
        rendered = json.dumps(
            {
                "requests": [item.safe_summary() for item in self.service.requests],
                "decisions": [item.safe_summary() for item in self.service.decisions],
                "audit": [item.safe_summary() for item in self.service.audit_events],
            },
            sort_keys=True,
        )
        for forbidden in (
            "/" + "Users" + "/",
            "raw_text",
            "body",
            "contact",
            "price",
            "inventory",
            "cookie",
            "token",
            "secret",
        ):
            self.assertNotIn(forbidden, rendered.lower())


if __name__ == "__main__":
    unittest.main()
