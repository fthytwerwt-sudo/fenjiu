# workflows

Thin orchestration boundary.

Phase 4 adds a local simple runner contract for workflow state, checkpoint,
idempotency, retry/DLQ, pause/resume, and recovery probes.

Workflows must call application ports and must not become a source of approved
facts, audit truth, provider memory, or external actions. LangGraph remains an
optional adapter probe only; the simple runner is the primary and fallback path
until the same contract suite proves an adapter can be swapped in.
