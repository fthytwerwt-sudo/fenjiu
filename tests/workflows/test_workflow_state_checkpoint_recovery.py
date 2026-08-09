"""P04-01 workflow state, checkpoint, and recovery contract probes."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import unittest

from core.contracts import synthetic_scope
from workflows.runner import (
    CommandEffect,
    InMemoryWorkflowStore,
    SimpleWorkflowRunner,
    TerminalResult,
    WorkflowBoundaryError,
    WorkflowCheckpoint,
    WorkflowCommand,
    WorkflowCrash,
    WorkflowRunState,
    probe_optional_langgraph_adapter,
)


NOW = datetime(2040, 2, 3, tzinfo=timezone.utc)
SCOPE = synthetic_scope()


class Clock:
    def __init__(self) -> None:
        self.current = NOW

    def __call__(self) -> datetime:
        result = self.current
        self.current = self.current + timedelta(seconds=1)
        return result


def command(
    *,
    key: str = "workflow_key_1",
    command_type: str = "workflow.synthetic.fake_effect",
    input_hash: str = "a" * 64,
    effect: CommandEffect = CommandEffect.FAKE_INTERNAL,
    actor: str = "system_worker",
    max_attempts: int = 3,
) -> WorkflowCommand:
    return WorkflowCommand(
        scope=SCOPE,
        command_type=command_type,
        input_hash=input_hash,
        policy_version="workflow_policy_v1",
        idempotency_key=key,
        actor=actor,
        effect=effect,
        max_attempts=max_attempts,
    )


class WorkflowStateCheckpointRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = Clock()
        self.store = InMemoryWorkflowStore()
        self.runner = SimpleWorkflowRunner(store=self.store, now=self.clock)

    def test_run_records_required_metadata_and_safe_checkpoint_refs_only(self) -> None:
        run = self.runner.start(command(effect=CommandEffect.NONE))

        self.assertTrue(run.workflow_run_id)
        self.assertEqual(run.scope, SCOPE)
        self.assertEqual(run.correlation_id, SCOPE.correlation_id)
        self.assertEqual(run.command_type, "workflow.synthetic.fake_effect")
        self.assertEqual(run.input_hash, "a" * 64)
        self.assertEqual(run.policy_version, "workflow_policy_v1")
        self.assertEqual(run.idempotency_key, "workflow_key_1")
        self.assertEqual(run.attempt, 1)
        self.assertTrue(run.checkpoint_ref)
        self.assertEqual(run.actor, "system_worker")
        self.assertLessEqual(run.created_at, run.updated_at)
        self.assertEqual(run.state, WorkflowRunState.SUCCEEDED)
        self.assertEqual(run.terminal_result, TerminalResult.SUCCEEDED)

        checkpoint = self.store.checkpoint(run.checkpoint_ref)
        self.assertEqual(checkpoint.workflow_run_id, run.workflow_run_id)
        self.assertEqual(checkpoint.scope, SCOPE)
        self.assertEqual(checkpoint.correlation_id, SCOPE.correlation_id)
        self.assertEqual(checkpoint.payload_hash, "a" * 64)
        self.assertEqual(checkpoint.safe_resume_state["phase"], "succeeded")

        rendered = json.dumps(run.safe_summary(), sort_keys=True)
        for forbidden in ("secret", "token", "cookie", "/" + "Users" + "/", "raw_text", "private_data"):
            self.assertNotIn(forbidden, rendered.lower())

    def test_checkpoint_rejects_secret_tokens_free_text_and_absolute_paths(self) -> None:
        safe = WorkflowCheckpoint.create(
            workflow_run_id="run_safe",
            scope=SCOPE,
            correlation_id=SCOPE.correlation_id,
            command_type="workflow.synthetic.safe",
            payload_hash="b" * 64,
            safe_resume_state={"phase": "queued", "source_ref": "ref:workflow:queued"},
            created_at=NOW,
        )
        self.assertEqual(safe.safe_resume_state["phase"], "queued")

        unsafe_payloads = (
            {"phase": "queued", "token_ref": "ref:workflow:queued"},
            {"phase": "queued", "source_ref": "/" + "Users" + "/fan/private.csv"},
            {"phase": "queued", "free_text": "hello world"},
            {"phase": "queued", "private_data": "ref:workflow:queued"},
        )
        for payload in unsafe_payloads:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(WorkflowBoundaryError, "checkpoint_payload_forbidden"):
                    WorkflowCheckpoint.create(
                        workflow_run_id="run_unsafe",
                        scope=SCOPE,
                        correlation_id=SCOPE.correlation_id,
                        command_type="workflow.synthetic.safe",
                        payload_hash="b" * 64,
                        safe_resume_state=payload,
                        created_at=NOW,
                    )

    def test_pause_resume_crash_replay_never_duplicates_fake_side_effect(self) -> None:
        run = self.runner.start(command())
        self.assertEqual(run.state, WorkflowRunState.WAITING_FOR_APPROVAL)
        self.runner.approve(
            run.workflow_run_id,
            actor="data_reviewer",
            approval_ref="approval_ref_1",
        )

        with self.assertRaises(WorkflowCrash):
            self.runner.resume(run.workflow_run_id, crash_after_effect=True)

        replay_runner = SimpleWorkflowRunner(store=self.store, now=self.clock)
        recovered = replay_runner.resume(run.workflow_run_id)

        self.assertEqual(recovered.state, WorkflowRunState.SUCCEEDED)
        self.assertEqual(recovered.terminal_result, TerminalResult.SUCCEEDED)
        self.assertEqual(self.store.effect_commit_count("workflow_key_1"), 1)
        self.assertEqual(len(self.store.dead_letter_queue), 0)
        self.assertGreaterEqual(len(self.store.run_events_for(run.workflow_run_id)), 5)
        self.assertEqual(
            [event.sequence for event in self.store.run_events_for(run.workflow_run_id)],
            list(range(1, len(self.store.run_events_for(run.workflow_run_id)) + 1)),
        )

    def test_retry_timeout_and_dlq_are_stable_and_atomic(self) -> None:
        run = self.runner.start(
            command(
                key="timeout_key_1",
                command_type="workflow.synthetic.timeout",
                effect=CommandEffect.TIMEOUT,
                max_attempts=2,
            )
        )
        self.assertEqual(run.state, WorkflowRunState.RETRY_SCHEDULED)
        self.assertEqual(run.terminal_result, TerminalResult.RETRY_SCHEDULED)
        self.assertEqual(run.attempt, 1)
        before = self.store.snapshot_counts()

        dlq = self.runner.retry(run.workflow_run_id)

        self.assertEqual(dlq.state, WorkflowRunState.DEAD_LETTERED)
        self.assertEqual(dlq.terminal_result, TerminalResult.DEAD_LETTERED)
        self.assertEqual(dlq.attempt, 2)
        self.assertEqual(len(self.store.dead_letter_queue), 1)
        self.assertEqual(self.store.effect_commit_count("timeout_key_1"), 0)
        after = self.store.snapshot_counts()
        self.assertEqual(after["runs"], before["runs"])
        self.assertEqual(after["dead_lettered"], before["dead_lettered"] + 1)

    def test_duplicate_idempotency_key_reruns_same_run_and_conflicts_on_changed_payload(self) -> None:
        first = self.runner.start(command(effect=CommandEffect.NONE))
        rerun = self.runner.start(command(effect=CommandEffect.NONE))

        self.assertEqual(first.workflow_run_id, rerun.workflow_run_id)
        self.assertEqual(self.store.snapshot_counts()["runs"], 1)

        with self.assertRaisesRegex(WorkflowBoundaryError, "idempotency_conflict"):
            self.runner.start(
                command(
                    input_hash="c" * 64,
                    effect=CommandEffect.NONE,
                )
            )

    def test_external_and_unknown_effects_stop_without_provider_calls(self) -> None:
        denied = self.runner.start(
            command(
                key="external_key_1",
                command_type="workflow.synthetic.external_publish",
                effect=CommandEffect.EXTERNAL_FORBIDDEN,
            )
        )
        self.assertEqual(denied.state, WorkflowRunState.POLICY_DENIED)
        self.assertEqual(denied.terminal_result, TerminalResult.POLICY_DENIED)
        self.assertEqual(self.store.effect_commit_count("external_key_1"), 0)

        unknown = self.runner.start(
            command(
                key="unknown_key_1",
                command_type="workflow.synthetic.unknown_effect",
                effect=CommandEffect.UNKNOWN,
            )
        )
        self.assertEqual(unknown.state, WorkflowRunState.MANUAL_QUEUE)
        self.assertEqual(unknown.terminal_result, TerminalResult.MANUAL_REQUIRED)
        self.assertEqual(self.store.manual_queue[-1].workflow_run_id, unknown.workflow_run_id)
        self.assertEqual(self.store.effect_commit_count("unknown_key_1"), 0)

    def test_scope_correlation_mismatch_fails_before_partial_records(self) -> None:
        bad_scope = replace(SCOPE, correlation_id="other_correlation")
        before = self.store.snapshot_counts()

        with self.assertRaisesRegex(WorkflowBoundaryError, "correlation_mismatch"):
            WorkflowCommand(
                scope=bad_scope,
                command_type="workflow.synthetic.fake_effect",
                input_hash="a" * 64,
                policy_version="workflow_policy_v1",
                idempotency_key="bad_scope_key",
                actor="system_worker",
                effect=CommandEffect.NONE,
                correlation_id=SCOPE.correlation_id,
            )

        self.assertEqual(self.store.snapshot_counts(), before)

    def test_optional_langgraph_probe_is_non_blocking_and_simple_runner_remains_primary(self) -> None:
        simple_run = self.runner.start(command(key="probe_key_1", effect=CommandEffect.NONE))

        probe = probe_optional_langgraph_adapter(simple_run)

        self.assertEqual(probe.primary_runner, "simple")
        self.assertEqual(probe.fallback_runner, "simple")
        self.assertEqual(probe.capability_status, "probe")
        self.assertIn(probe.langgraph_status, {"available", "deferred"})
        if probe.langgraph_status == "deferred":
            self.assertIn("langgraph", probe.reason)
        self.assertEqual(probe.simple_terminal_result, TerminalResult.SUCCEEDED.value)


if __name__ == "__main__":
    unittest.main()
