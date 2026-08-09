"""P04-01 local workflow runner contracts.

The runner stores only orchestration metadata, checkpoint references, hashes,
and idempotency state. It intentionally does not own business truth, approval
truth, provider adapters, or external side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import importlib.util
import json
import re
from typing import Any, Callable, Mapping
from uuid import NAMESPACE_URL, uuid5

from core.contracts import ContractValidationError, ScopeRef


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE = re.compile(
    r"(?i)(?:^|[./_:-])(?:api[-_]?key|authorization|bearer|cookie|password|secret|token)(?:$|[./_:-])"
    r"|^(?:sk[-_]|ghp_|github_pat_|xox[baprs]-|akia|aiza)"
)
_FORBIDDEN_CHECKPOINT_KEY = re.compile(
    r"(?i)(secret|token|cookie|password|private|raw|text|body|contact|price|inventory|path|file)"
)


class WorkflowBoundaryError(ContractValidationError):
    """Stable, value-free P04-01 boundary error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class WorkflowCrash(RuntimeError):
    """Synthetic crash hook used by recovery contract tests."""


class WorkflowRunState(str, Enum):
    CREATED = "created"
    VALIDATED = "validated"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    PAUSED = "paused"
    RETRY_SCHEDULED = "retry_scheduled"
    SUCCEEDED = "succeeded"
    POLICY_DENIED = "policy_denied"
    DEAD_LETTERED = "dead_lettered"
    MANUAL_QUEUE = "manual_queue"


class TerminalResult(str, Enum):
    NONE = "none"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    RETRY_SCHEDULED = "retry_scheduled"
    SUCCEEDED = "succeeded"
    POLICY_DENIED = "policy_denied"
    DEAD_LETTERED = "dead_lettered"
    MANUAL_REQUIRED = "manual_required"


class CommandEffect(str, Enum):
    NONE = "none"
    FAKE_INTERNAL = "fake_internal"
    TIMEOUT = "timeout"
    EXTERNAL_FORBIDDEN = "external_forbidden"
    UNKNOWN = "unknown"


def _boundary(code: str) -> WorkflowBoundaryError:
    return WorkflowBoundaryError(code)


def _require_identifier(value: object, code: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise _boundary(code)
    _reject_sensitive_text(value)
    return value


def _require_hash(value: object, code: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise _boundary(code)
    return value


def _require_time(value: object, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _boundary(code)
    return value


def _require_scope(value: object) -> ScopeRef:
    if not isinstance(value, ScopeRef):
        raise _boundary("scope_required")
    _require_identifier(value.correlation_id, "correlation_id_required")
    return value


def _reject_sensitive_text(value: object) -> None:
    if not isinstance(value, str):
        return
    if _SENSITIVE.search(value) is not None:
        raise _boundary("sensitive_metadata_forbidden")


def _reject_absolute_path(value: str) -> None:
    local_user_root = "/" + "Users" + "/"
    local_volume_root = "/" + "Volumes" + "/"
    if value.startswith("/") or "\\" in value or local_user_root in value or local_volume_root in value:
        raise _boundary("checkpoint_payload_forbidden")


def _safe_checkpoint_value(value: object) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        _reject_sensitive_text(value)
        _reject_absolute_path(value)
        if _IDENTIFIER.fullmatch(value) is None and _SHA256.fullmatch(value) is None:
            raise _boundary("checkpoint_payload_forbidden")
        return value
    if isinstance(value, tuple):
        return tuple(_safe_checkpoint_value(item) for item in value)
    if isinstance(value, list):
        return [_safe_checkpoint_value(item) for item in value]
    if isinstance(value, Mapping):
        return _safe_checkpoint_payload(value)
    raise _boundary("checkpoint_payload_forbidden")


def _safe_checkpoint_payload(payload: Mapping[str, object]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in payload.items():
        if not isinstance(key, str) or _IDENTIFIER.fullmatch(key) is None:
            raise _boundary("checkpoint_payload_forbidden")
        if _FORBIDDEN_CHECKPOINT_KEY.search(key) is not None:
            raise _boundary("checkpoint_payload_forbidden")
        result[key] = _safe_checkpoint_value(value)
    return result


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _digest(*parts: object) -> str:
    return sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _id(prefix: str, *parts: object) -> str:
    return str(uuid5(NAMESPACE_URL, "|".join((prefix, *(str(part) for part in parts)))))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class WorkflowCommand:
    scope: ScopeRef
    command_type: str
    input_hash: str
    policy_version: str
    idempotency_key: str
    actor: str
    effect: CommandEffect = CommandEffect.NONE
    max_attempts: int = 3
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        scope = _require_scope(self.scope)
        _require_identifier(self.command_type, "command_type_required")
        _require_hash(self.input_hash, "input_hash_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_identifier(self.idempotency_key, "idempotency_key_required")
        _require_identifier(self.actor, "actor_required")
        if not isinstance(self.effect, CommandEffect):
            raise _boundary("command_effect_required")
        if not isinstance(self.max_attempts, int) or isinstance(self.max_attempts, bool) or self.max_attempts < 1:
            raise _boundary("max_attempts_required")
        correlation = self.correlation_id or scope.correlation_id
        _require_identifier(correlation, "correlation_id_required")
        if correlation != scope.correlation_id:
            raise _boundary("correlation_mismatch")
        object.__setattr__(self, "correlation_id", correlation)

    def fingerprint(self) -> str:
        return _digest(
            self.scope.tenant_id,
            self.scope.project_id,
            self.scope.business_line_id,
            self.correlation_id,
            self.command_type,
            self.input_hash,
            self.policy_version,
            self.idempotency_key,
            self.actor,
            self.effect.value,
            self.max_attempts,
        )


@dataclass(frozen=True)
class WorkflowCheckpoint:
    checkpoint_ref: str
    workflow_run_id: str
    scope: ScopeRef
    correlation_id: str
    command_type: str
    payload_hash: str
    safe_resume_state: Mapping[str, object]
    created_at: datetime

    def __post_init__(self) -> None:
        _require_identifier(self.checkpoint_ref, "checkpoint_ref_required")
        _require_identifier(self.workflow_run_id, "workflow_run_id_required")
        scope = _require_scope(self.scope)
        _require_identifier(self.correlation_id, "correlation_id_required")
        if self.correlation_id != scope.correlation_id:
            raise _boundary("correlation_mismatch")
        _require_identifier(self.command_type, "command_type_required")
        _require_hash(self.payload_hash, "payload_hash_required")
        _require_time(self.created_at, "checkpoint_created_at_required")
        object.__setattr__(self, "safe_resume_state", _safe_checkpoint_payload(self.safe_resume_state))

    @classmethod
    def create(
        cls,
        *,
        workflow_run_id: str,
        scope: ScopeRef,
        correlation_id: str,
        command_type: str,
        payload_hash: str,
        safe_resume_state: Mapping[str, object],
        created_at: datetime,
    ) -> "WorkflowCheckpoint":
        safe_state = _safe_checkpoint_payload(safe_resume_state)
        checkpoint_ref = "ref:workflow:" + _digest(
            workflow_run_id,
            correlation_id,
            command_type,
            payload_hash,
            _canonical_json(safe_state),
            created_at.isoformat(),
        )[:32]
        return cls(
            checkpoint_ref=checkpoint_ref,
            workflow_run_id=workflow_run_id,
            scope=scope,
            correlation_id=correlation_id,
            command_type=command_type,
            payload_hash=payload_hash,
            safe_resume_state=safe_state,
            created_at=created_at,
        )


@dataclass(frozen=True)
class WorkflowRun:
    workflow_run_id: str
    scope: ScopeRef
    correlation_id: str
    command_type: str
    input_hash: str
    policy_version: str
    idempotency_key: str
    attempt: int
    checkpoint_ref: str
    actor: str
    created_at: datetime
    updated_at: datetime
    state: WorkflowRunState
    terminal_result: TerminalResult

    def __post_init__(self) -> None:
        _require_identifier(self.workflow_run_id, "workflow_run_id_required")
        scope = _require_scope(self.scope)
        _require_identifier(self.correlation_id, "correlation_id_required")
        if self.correlation_id != scope.correlation_id:
            raise _boundary("correlation_mismatch")
        _require_identifier(self.command_type, "command_type_required")
        _require_hash(self.input_hash, "input_hash_required")
        _require_identifier(self.policy_version, "policy_version_required")
        _require_identifier(self.idempotency_key, "idempotency_key_required")
        if not isinstance(self.attempt, int) or isinstance(self.attempt, bool) or self.attempt < 0:
            raise _boundary("attempt_required")
        _require_identifier(self.checkpoint_ref, "checkpoint_ref_required")
        _require_identifier(self.actor, "actor_required")
        created = _require_time(self.created_at, "created_at_required")
        updated = _require_time(self.updated_at, "updated_at_required")
        if updated < created:
            raise _boundary("updated_at_required")
        if not isinstance(self.state, WorkflowRunState):
            raise _boundary("workflow_state_required")
        if not isinstance(self.terminal_result, TerminalResult):
            raise _boundary("terminal_result_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "workflow_run_id": self.workflow_run_id,
            "scope": {
                "tenant_id": str(self.scope.tenant_id),
                "project_id": str(self.scope.project_id),
                "business_line_id": str(self.scope.business_line_id),
            },
            "correlation_id": self.correlation_id,
            "command_type": self.command_type,
            "input_hash": self.input_hash,
            "policy_version": self.policy_version,
            "idempotency_key": self.idempotency_key,
            "attempt": self.attempt,
            "checkpoint_ref": self.checkpoint_ref,
            "actor": self.actor,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "state": self.state.value,
            "terminal_result": self.terminal_result.value,
        }


@dataclass(frozen=True)
class WorkflowRunEvent:
    sequence: int
    workflow_run_id: str
    state: WorkflowRunState
    terminal_result: TerminalResult
    checkpoint_ref: str
    correlation_id: str
    occurred_at: datetime
    event_kind: str
    actor: str

    def __post_init__(self) -> None:
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 1:
            raise _boundary("event_sequence_required")
        _require_identifier(self.workflow_run_id, "workflow_run_id_required")
        if not isinstance(self.state, WorkflowRunState):
            raise _boundary("workflow_state_required")
        if not isinstance(self.terminal_result, TerminalResult):
            raise _boundary("terminal_result_required")
        _require_identifier(self.checkpoint_ref, "checkpoint_ref_required")
        _require_identifier(self.correlation_id, "correlation_id_required")
        _require_time(self.occurred_at, "event_time_required")
        _require_identifier(self.event_kind, "event_kind_required")
        _require_identifier(self.actor, "actor_required")


@dataclass(frozen=True)
class ManualQueueItem:
    workflow_run_id: str
    reason: str
    checkpoint_ref: str
    correlation_id: str


@dataclass(frozen=True)
class DeadLetterItem:
    workflow_run_id: str
    reason: str
    checkpoint_ref: str
    correlation_id: str
    attempts: int


class InMemoryWorkflowStore:
    """In-memory workflow state store used by the local simple runner."""

    def __init__(self) -> None:
        self._runs: dict[str, WorkflowRun] = {}
        self._commands: dict[str, WorkflowCommand] = {}
        self._idempotency_to_run: dict[str, str] = {}
        self._idempotency_fingerprints: dict[str, str] = {}
        self._checkpoints: dict[str, WorkflowCheckpoint] = {}
        self._events_by_run: dict[str, list[WorkflowRunEvent]] = {}
        self._manual_queue: list[ManualQueueItem] = []
        self._dead_letter_queue: list[DeadLetterItem] = []
        self._effect_commits: dict[str, int] = {}
        self._approvals: dict[str, str] = {}

    @property
    def manual_queue(self) -> tuple[ManualQueueItem, ...]:
        return tuple(self._manual_queue)

    @property
    def dead_letter_queue(self) -> tuple[DeadLetterItem, ...]:
        return tuple(self._dead_letter_queue)

    def existing_for(self, command: WorkflowCommand) -> WorkflowRun | None:
        run_id = self._idempotency_to_run.get(command.idempotency_key)
        if run_id is None:
            return None
        if self._idempotency_fingerprints[command.idempotency_key] != command.fingerprint():
            raise _boundary("idempotency_conflict")
        return self._runs[run_id]

    def remember_command(self, run_id: str, command: WorkflowCommand) -> None:
        self._commands[run_id] = command
        self._idempotency_to_run[command.idempotency_key] = run_id
        self._idempotency_fingerprints[command.idempotency_key] = command.fingerprint()

    def command_for(self, run_id: str) -> WorkflowCommand:
        command = self._commands.get(run_id)
        if command is None:
            raise _boundary("workflow_run_not_found")
        return command

    def save_run(self, run: WorkflowRun, *, event_kind: str) -> None:
        self._runs[run.workflow_run_id] = run
        events = self._events_by_run.setdefault(run.workflow_run_id, [])
        events.append(
            WorkflowRunEvent(
                sequence=len(events) + 1,
                workflow_run_id=run.workflow_run_id,
                state=run.state,
                terminal_result=run.terminal_result,
                checkpoint_ref=run.checkpoint_ref,
                correlation_id=run.correlation_id,
                occurred_at=run.updated_at,
                event_kind=event_kind,
                actor=run.actor,
            )
        )

    def run(self, run_id: str) -> WorkflowRun:
        run = self._runs.get(run_id)
        if run is None:
            raise _boundary("workflow_run_not_found")
        return run

    def save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        self._checkpoints[checkpoint.checkpoint_ref] = checkpoint

    def checkpoint(self, checkpoint_ref: str) -> WorkflowCheckpoint:
        checkpoint = self._checkpoints.get(checkpoint_ref)
        if checkpoint is None:
            raise _boundary("checkpoint_not_found")
        return checkpoint

    def run_events_for(self, run_id: str) -> tuple[WorkflowRunEvent, ...]:
        return tuple(self._events_by_run.get(run_id, ()))

    def enqueue_manual(self, item: ManualQueueItem) -> None:
        if not any(existing.workflow_run_id == item.workflow_run_id for existing in self._manual_queue):
            self._manual_queue.append(item)

    def enqueue_dead_letter(self, item: DeadLetterItem) -> None:
        if not any(existing.workflow_run_id == item.workflow_run_id for existing in self._dead_letter_queue):
            self._dead_letter_queue.append(item)

    def commit_effect_once(self, key: str) -> bool:
        _require_identifier(key, "idempotency_key_required")
        if key in self._effect_commits:
            return False
        self._effect_commits[key] = 1
        return True

    def effect_commit_count(self, key: str) -> int:
        return self._effect_commits.get(key, 0)

    def approve(self, run_id: str, approval_ref: str) -> None:
        _require_identifier(run_id, "workflow_run_id_required")
        _require_identifier(approval_ref, "approval_ref_required")
        self._approvals[run_id] = approval_ref

    def approval_ref_for(self, run_id: str) -> str | None:
        return self._approvals.get(run_id)

    def snapshot_counts(self) -> dict[str, int]:
        return {
            "runs": len(self._runs),
            "checkpoints": len(self._checkpoints),
            "events": sum(len(events) for events in self._events_by_run.values()),
            "manual_queue": len(self._manual_queue),
            "dead_lettered": len(self._dead_letter_queue),
            "effect_commits": sum(self._effect_commits.values()),
        }


class SimpleWorkflowRunner:
    """Local replaceable state-machine runner for P04 contract probes."""

    def __init__(self, *, store: InMemoryWorkflowStore | None = None, now: Callable[[], datetime] | None = None) -> None:
        self.store = store or InMemoryWorkflowStore()
        self._now = now or _now_utc

    def start(self, command: WorkflowCommand) -> WorkflowRun:
        if not isinstance(command, WorkflowCommand):
            raise _boundary("workflow_command_required")
        existing = self.store.existing_for(command)
        if existing is not None:
            return existing

        run_id = _id("p04-01-workflow-run", command.scope, command.idempotency_key)
        created_at = self._now()
        checkpoint = self._checkpoint(
            run_id=run_id,
            command=command,
            phase="created",
            created_at=created_at,
        )
        run = WorkflowRun(
            workflow_run_id=run_id,
            scope=command.scope,
            correlation_id=command.correlation_id or command.scope.correlation_id,
            command_type=command.command_type,
            input_hash=command.input_hash,
            policy_version=command.policy_version,
            idempotency_key=command.idempotency_key,
            attempt=0,
            checkpoint_ref=checkpoint.checkpoint_ref,
            actor=command.actor,
            created_at=created_at,
            updated_at=created_at,
            state=WorkflowRunState.CREATED,
            terminal_result=TerminalResult.NONE,
        )
        self.store.remember_command(run.workflow_run_id, command)
        self.store.save_checkpoint(checkpoint)
        self.store.save_run(run, event_kind="run_created")
        run = self._transition(run, WorkflowRunState.VALIDATED, TerminalResult.NONE, "validated")
        run = self._transition(run, WorkflowRunState.QUEUED, TerminalResult.NONE, "queued")
        run = self._transition(run, WorkflowRunState.RUNNING, TerminalResult.NONE, "running", attempt=1)
        return self._execute(run, command)

    def approve(self, workflow_run_id: str, *, actor: str, approval_ref: str) -> WorkflowRun:
        run = self.store.run(_require_identifier(workflow_run_id, "workflow_run_id_required"))
        _require_identifier(actor, "actor_required")
        self.store.approve(run.workflow_run_id, approval_ref)
        return self._transition(run, WorkflowRunState.PAUSED, TerminalResult.WAITING_FOR_APPROVAL, "approval_recorded")

    def resume(self, workflow_run_id: str, *, crash_after_effect: bool = False) -> WorkflowRun:
        run = self.store.run(_require_identifier(workflow_run_id, "workflow_run_id_required"))
        command = self.store.command_for(run.workflow_run_id)
        if run.state in {
            WorkflowRunState.SUCCEEDED,
            WorkflowRunState.POLICY_DENIED,
            WorkflowRunState.DEAD_LETTERED,
            WorkflowRunState.MANUAL_QUEUE,
        }:
            return run
        if command.effect is not CommandEffect.FAKE_INTERNAL:
            return self._execute(run, command)
        if self.store.approval_ref_for(run.workflow_run_id) is None:
            raise _boundary("approval_required")
        self.store.commit_effect_once(command.idempotency_key)
        if crash_after_effect:
            self._transition(
                run,
                WorkflowRunState.PAUSED,
                TerminalResult.WAITING_FOR_APPROVAL,
                "effect_committed",
                extra={"effect_ref": "ref:workflow_effect:" + command.idempotency_key},
            )
            raise WorkflowCrash("synthetic_workflow_crash_after_effect")
        return self._transition(run, WorkflowRunState.SUCCEEDED, TerminalResult.SUCCEEDED, "succeeded")

    def retry(self, workflow_run_id: str) -> WorkflowRun:
        run = self.store.run(_require_identifier(workflow_run_id, "workflow_run_id_required"))
        if run.state is not WorkflowRunState.RETRY_SCHEDULED:
            raise _boundary("workflow_not_retryable")
        command = self.store.command_for(run.workflow_run_id)
        run = self._transition(run, WorkflowRunState.RUNNING, TerminalResult.NONE, "retry_running", attempt=run.attempt + 1)
        return self._execute(run, command)

    def _execute(self, run: WorkflowRun, command: WorkflowCommand) -> WorkflowRun:
        if command.effect is CommandEffect.NONE:
            return self._transition(run, WorkflowRunState.SUCCEEDED, TerminalResult.SUCCEEDED, "succeeded")
        if command.effect is CommandEffect.FAKE_INTERNAL:
            if self.store.approval_ref_for(run.workflow_run_id) is None:
                return self._transition(
                    run,
                    WorkflowRunState.WAITING_FOR_APPROVAL,
                    TerminalResult.WAITING_FOR_APPROVAL,
                    "waiting_for_approval",
                )
            return self.resume(run.workflow_run_id)
        if command.effect is CommandEffect.TIMEOUT:
            return self._retry_or_dlq(run, "timeout")
        if command.effect is CommandEffect.EXTERNAL_FORBIDDEN:
            return self._transition(
                run,
                WorkflowRunState.POLICY_DENIED,
                TerminalResult.POLICY_DENIED,
                "policy_denied",
                extra={"reason": "external_effect_forbidden"},
            )
        if command.effect is CommandEffect.UNKNOWN:
            manual = self._transition(
                run,
                WorkflowRunState.MANUAL_QUEUE,
                TerminalResult.MANUAL_REQUIRED,
                "manual_queue",
                extra={"reason": "unknown_effect_manual_review"},
            )
            self.store.enqueue_manual(
                ManualQueueItem(
                    workflow_run_id=manual.workflow_run_id,
                    reason="unknown_effect_manual_review",
                    checkpoint_ref=manual.checkpoint_ref,
                    correlation_id=manual.correlation_id,
                )
            )
            return manual
        raise _boundary("command_effect_required")

    def _retry_or_dlq(self, run: WorkflowRun, reason: str) -> WorkflowRun:
        command = self.store.command_for(run.workflow_run_id)
        if run.attempt >= command.max_attempts:
            dead = self._transition(
                run,
                WorkflowRunState.DEAD_LETTERED,
                TerminalResult.DEAD_LETTERED,
                "dead_lettered",
                extra={"reason": reason},
            )
            self.store.enqueue_dead_letter(
                DeadLetterItem(
                    workflow_run_id=dead.workflow_run_id,
                    reason=reason,
                    checkpoint_ref=dead.checkpoint_ref,
                    correlation_id=dead.correlation_id,
                    attempts=dead.attempt,
                )
            )
            return dead
        return self._transition(
            run,
            WorkflowRunState.RETRY_SCHEDULED,
            TerminalResult.RETRY_SCHEDULED,
            "retry_scheduled",
            extra={"reason": reason},
        )

    def _transition(
        self,
        run: WorkflowRun,
        state: WorkflowRunState,
        terminal_result: TerminalResult,
        phase: str,
        *,
        attempt: int | None = None,
        extra: Mapping[str, object] | None = None,
    ) -> WorkflowRun:
        updated_at = self._now()
        command = self.store.command_for(run.workflow_run_id)
        checkpoint = self._checkpoint(
            run_id=run.workflow_run_id,
            command=command,
            phase=phase,
            created_at=updated_at,
            extra=extra,
        )
        self.store.save_checkpoint(checkpoint)
        next_run = WorkflowRun(
            workflow_run_id=run.workflow_run_id,
            scope=run.scope,
            correlation_id=run.correlation_id,
            command_type=run.command_type,
            input_hash=run.input_hash,
            policy_version=run.policy_version,
            idempotency_key=run.idempotency_key,
            attempt=run.attempt if attempt is None else attempt,
            checkpoint_ref=checkpoint.checkpoint_ref,
            actor=run.actor,
            created_at=run.created_at,
            updated_at=updated_at,
            state=state,
            terminal_result=terminal_result,
        )
        self.store.save_run(next_run, event_kind=phase)
        return next_run

    def _checkpoint(
        self,
        *,
        run_id: str,
        command: WorkflowCommand,
        phase: str,
        created_at: datetime,
        extra: Mapping[str, object] | None = None,
    ) -> WorkflowCheckpoint:
        state: dict[str, object] = {
            "phase": phase,
            "run_ref": "ref:workflow_run:" + run_id,
            "command_ref": "ref:workflow_command:" + command.idempotency_key,
        }
        if extra:
            state.update(extra)
        return WorkflowCheckpoint.create(
            workflow_run_id=run_id,
            scope=command.scope,
            correlation_id=command.correlation_id or command.scope.correlation_id,
            command_type=command.command_type,
            payload_hash=command.input_hash,
            safe_resume_state=state,
            created_at=created_at,
        )


@dataclass(frozen=True)
class WorkflowRunnerProbe:
    primary_runner: str
    fallback_runner: str
    capability_status: str
    simple_terminal_result: str
    langgraph_status: str
    reason: str


def probe_optional_langgraph_adapter(simple_run: WorkflowRun) -> WorkflowRunnerProbe:
    """Probe LangGraph availability without installing or importing providers."""

    if not isinstance(simple_run, WorkflowRun):
        raise _boundary("workflow_run_required")
    spec = importlib.util.find_spec("langgraph")
    if spec is None:
        return WorkflowRunnerProbe(
            primary_runner="simple",
            fallback_runner="simple",
            capability_status="probe",
            simple_terminal_result=simple_run.terminal_result.value,
            langgraph_status="deferred",
            reason="langgraph_not_installed_no_dependency_added",
        )
    return WorkflowRunnerProbe(
        primary_runner="simple",
        fallback_runner="simple",
        capability_status="probe",
        simple_terminal_result=simple_run.terminal_result.value,
        langgraph_status="available",
        reason="langgraph_import_available_contract_suite_required_before_use",
    )
