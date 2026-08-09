"""P04-03 audit, retry, DLQ, metrics, and redaction contract probes."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import json
import unittest

from core.application.retry import (
    LocalDeadLetterQueue,
    QueueDeliveryState,
    RetryClass,
    RetryClassifier,
    RetryEffect,
)
from core.contracts import synthetic_scope
from core.security.audit import (
    AuditBoundaryError,
    AuditRequiredCommandExecutor,
    InMemoryAuditLog,
)
from observability.json_logging import JsonLogEvent, render_json_log
from observability.metrics import (
    LocalMetricsRegistry,
    MetricName,
    record_retry_metrics,
    render_metrics_snapshot,
)


NOW = datetime(2040, 6, 7, tzinfo=timezone.utc)
SCOPE = synthetic_scope()


class Clock:
    def __init__(self) -> None:
        self.current = NOW

    def __call__(self) -> datetime:
        result = self.current
        self.current = self.current + timedelta(seconds=1)
        return result


def audit_log(clock: Clock | None = None) -> InMemoryAuditLog:
    return InMemoryAuditLog(now=clock or Clock())


class FailingAuditLog:
    def record(self, **_: object) -> object:
        raise AuditBoundaryError("audit_persistence_required")


class SecondWriteFailingAuditLog:
    def __init__(self) -> None:
        self.calls = 0
        self.delegate = audit_log()

    def record(self, **kwargs: object) -> object:
        self.calls += 1
        if self.calls == 2:
            raise AuditBoundaryError("audit_persistence_required")
        return self.delegate.record(**kwargs)


class AuditMetricsRetryDeadLetterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = Clock()
        self.audit = audit_log(self.clock)

    def test_audit_events_are_append_only_chained_and_value_free(self) -> None:
        first = self.audit.record(
            event_kind="command_started",
            actor_ref="system_worker",
            scope=SCOPE,
            command_ref="workflow.synthetic.mutate",
            target_ref="target_ref_1",
            policy_version="audit_policy_v1",
            subject_version=1,
            result_code="started",
            before_version_hash="a" * 64,
            after_version_hash="b" * 64,
            metadata={"attempt": 1, "retryable": True},
        )
        second = self.audit.record(
            event_kind="command_succeeded",
            actor_ref="system_worker",
            scope=SCOPE,
            command_ref="workflow.synthetic.mutate",
            target_ref="target_ref_1",
            policy_version="audit_policy_v1",
            subject_version=1,
            result_code="succeeded",
            before_version_hash="b" * 64,
            after_version_hash="c" * 64,
            metadata={"attempt": 1, "retryable": False},
        )

        self.assertEqual([event.sequence for event in self.audit.events], [1, 2])
        self.assertEqual(first.previous_chain_hash, "0" * 64)
        self.assertEqual(second.previous_chain_hash, first.chain_hash)
        self.assertTrue(self.audit.verify_chain())
        self.assertEqual(first.correlation_id, SCOPE.correlation_id)

        with self.assertRaises(FrozenInstanceError):
            first.actor_ref = "changed"
        self.assertFalse(hasattr(self.audit, "update"))
        self.assertFalse(hasattr(self.audit, "delete"))

        rendered = json.dumps([event.safe_summary() for event in self.audit.events], sort_keys=True)
        for forbidden in (
            "/" + "Users" + "/",
            "/" + "Volumes" + "/",
            "raw_content",
            "message_body",
            "personal_email",
            "cookie",
            "token",
            "secret",
        ):
            self.assertNotIn(forbidden, rendered.lower())

    def test_audit_rejects_sensitive_metadata_before_partial_records(self) -> None:
        before = self.audit.snapshot_counts()
        private_segment = "priv" + "ate"
        unsafe_metadata = (
            {"raw_content": "ref:unsafe:raw"},
            {"safe_ref": "/" + "Users" + f"/example/{private_segment}.csv"},
            {"safe_ref": "sk-" + "syntheticsecret123"},
            {"contact": "person@example.invalid"},
        )

        for metadata in unsafe_metadata:
            with self.subTest(metadata=metadata):
                with self.assertRaisesRegex(AuditBoundaryError, "audit_payload_forbidden"):
                    self.audit.record(
                        event_kind="command_started",
                        actor_ref="system_worker",
                        scope=SCOPE,
                        command_ref="workflow.synthetic.mutate",
                        target_ref="target_ref_sensitive",
                        policy_version="audit_policy_v1",
                        subject_version=1,
                        result_code="started",
                        metadata=metadata,
                    )

        self.assertEqual(self.audit.snapshot_counts(), before)

    def test_mutating_command_fails_closed_when_audit_cannot_be_written(self) -> None:
        calls: list[str] = []
        executor = AuditRequiredCommandExecutor(
            audit_log=FailingAuditLog(),
            actor_ref="system_worker",
            scope=SCOPE,
            command_ref="workflow.synthetic.mutate",
            target_ref="target_ref_1",
            policy_version="audit_policy_v1",
            subject_version=1,
        )

        with self.assertRaisesRegex(AuditBoundaryError, "audit_persistence_required"):
            executor.run(lambda: calls.append("mutated"), result_code="succeeded")

        self.assertEqual(calls, [])

    def test_staged_mutation_is_not_committed_when_success_audit_fails(self) -> None:
        committed: list[str] = []
        prepared: list[str] = []
        executor = AuditRequiredCommandExecutor(
            audit_log=SecondWriteFailingAuditLog(),
            actor_ref="system_worker",
            scope=SCOPE,
            command_ref="workflow.synthetic.mutate",
            target_ref="target_ref_1",
            policy_version="audit_policy_v1",
            subject_version=1,
        )

        def stage_effect():
            prepared.append("prepared")
            return executor.stage_effect(
                commit=lambda: committed.append("mutated"),
                rollback=lambda: prepared.append("rolled_back"),
            )

        with self.assertRaisesRegex(AuditBoundaryError, "audit_persistence_required"):
            executor.run(stage_effect, result_code="succeeded")

        self.assertEqual(prepared, ["prepared", "rolled_back"])
        self.assertEqual(committed, [])

    def test_retry_classification_keeps_external_and_unknown_effects_manual(self) -> None:
        classifier = RetryClassifier()

        retry = classifier.classify(
            scope=SCOPE,
            source_ref="ref:workflow_run:safe_retry",
            checkpoint_ref="ref:checkpoint:safe_retry",
            effect=RetryEffect.INTERNAL_TRANSIENT,
            attempt=1,
            max_attempts=2,
            error_code="timeout",
        )
        self.assertEqual(retry.retry_class, RetryClass.AUTO_RETRY)
        self.assertEqual(retry.delivery_state, QueueDeliveryState.RETRY_SCHEDULED)
        self.assertTrue(retry.may_auto_retry)

        dlq = classifier.classify(
            scope=SCOPE,
            source_ref="ref:workflow_run:safe_retry",
            checkpoint_ref="ref:checkpoint:safe_retry",
            effect=RetryEffect.INTERNAL_TRANSIENT,
            attempt=2,
            max_attempts=2,
            error_code="timeout",
        )
        self.assertEqual(dlq.retry_class, RetryClass.NO_RETRY)
        self.assertEqual(dlq.delivery_state, QueueDeliveryState.DEAD_LETTERED)
        self.assertFalse(dlq.may_auto_retry)

        manual_cases = (
            (RetryEffect.EXTERNAL_SIDE_EFFECT, QueueDeliveryState.MANUAL_QUEUE),
            (RetryEffect.UNKNOWN_SIDE_EFFECT, QueueDeliveryState.MANUAL_QUEUE),
            (RetryEffect.BROKER_UNAVAILABLE, QueueDeliveryState.PENDING_MANUAL),
        )
        for effect, state in manual_cases:
            with self.subTest(effect=effect.value):
                decision = classifier.classify(
                    scope=SCOPE,
                    source_ref="ref:workflow_run:manual",
                    checkpoint_ref="ref:checkpoint:manual",
                    effect=effect,
                    attempt=1,
                    max_attempts=3,
                    error_code="adapter_unavailable",
                )
                self.assertEqual(decision.retry_class, RetryClass.MANUAL_REVIEW)
                self.assertEqual(decision.delivery_state, state)
                self.assertTrue(decision.manual_required)
                self.assertFalse(decision.may_auto_retry)

    def test_dead_letter_queue_retains_safe_source_and_correlation_only(self) -> None:
        classifier = RetryClassifier()
        queue = LocalDeadLetterQueue()
        decision = classifier.classify(
            scope=SCOPE,
            source_ref="ref:workflow_run:dead_letter_source",
            checkpoint_ref="ref:checkpoint:dead_letter_source",
            effect=RetryEffect.INTERNAL_TRANSIENT,
            attempt=3,
            max_attempts=3,
            error_code="timeout",
        )

        item = queue.enqueue(decision)

        self.assertEqual(item.source_ref, "ref:workflow_run:dead_letter_source")
        self.assertEqual(item.correlation_id, SCOPE.correlation_id)
        self.assertEqual(item.error_code, "timeout")
        self.assertEqual(queue.items, (item,))
        rendered = json.dumps(item.safe_summary(), sort_keys=True)
        for forbidden in ("payload", "raw", "message", "/" + "Users" + "/", "token", "cookie", "secret"):
            self.assertNotIn(forbidden, rendered.lower())

    def test_metrics_and_logs_preserve_correlation_without_sensitive_values(self) -> None:
        classifier = RetryClassifier()
        registry = LocalMetricsRegistry()
        decision = classifier.classify(
            scope=SCOPE,
            source_ref="ref:workflow_run:metrics_source",
            checkpoint_ref="ref:checkpoint:metrics_source",
            effect=RetryEffect.INTERNAL_TRANSIENT,
            attempt=3,
            max_attempts=3,
            error_code="timeout",
        )

        record_retry_metrics(registry, decision)
        private_segment = "priv" + "ate"
        unsafe_metric_value = "/" + "Volumes" + f"/{private_segment}/local.txt"
        registry.increment(
            MetricName.AUDIT_EVENT_TOTAL,
            labels={
                "correlation_id": SCOPE.correlation_id,
                "result_code": "succeeded",
                "unsafe_label": unsafe_metric_value,
            },
        )
        metrics_payload = json.loads(render_metrics_snapshot(registry))
        metric_rendered = json.dumps(metrics_payload, sort_keys=True)

        self.assertIn(SCOPE.correlation_id, metric_rendered)
        self.assertNotIn(unsafe_metric_value, metric_rendered)
        self.assertIn("redacted_identifier", metric_rendered)

        log_rendered = render_json_log(
            JsonLogEvent(
                correlation_id=SCOPE.correlation_id,
                component="worker",
                event="retry.dead_lettered",
                result="blocked",
                metadata={
                    "error_code": "timeout",
                    "source_ref": "ref:workflow_run:metrics_source",
                    "detail": "bearer " + "synthetic_sensitive_value",
                },
            )
        )
        self.assertIn(SCOPE.correlation_id, log_rendered)
        for forbidden in (
            "synthetic_sensitive_value",
            "/" + "Users" + "/",
            "/" + "Volumes" + "/",
        ):
            self.assertNotIn(forbidden, log_rendered)


if __name__ == "__main__":
    unittest.main()
