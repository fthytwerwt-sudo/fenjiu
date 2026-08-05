# P04-03｜审计、指标、重试与死信队列

| 元数据 | 值 |
|---|---|
| task_id / phase | `P04-03` / `phase_04` |
| depends_on / can_run_in_parallel_with | `P04-02` / 无 |
| writes_to | `observability/`、queue port、audit module、tests/docs |
| forbidden_paths | real monitoring SaaS credentials, external action adapters, raw content/PII |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking |

## Goal

实现 append-only audit events、safe retry classification、dead-letter visibility、metrics/log contract 与不泄露内容的 correlation tracing。

## Context

审计是业务/批准事实的附属证据，不是日志；PostgreSQL 保存审计，broker 只临时调度。

## Constraints

禁止普通 update/delete audit；禁止将完整文件/消息/secret/absolute path 放入 logs/metrics；禁止自动重试外部副作用。

## 六层需求确认

- 目标层：可追溯运行，不实现新业务。
- 机制层：mutating command must emit audit or fail.
- 实现设计层：`primary_route=DB audit+QueuePort metrics`；`fallback_route=local structured logs`；`capability_status=local`；`probe_required=failure injection`。
- 流程层：command→policy→audit→queue/run→result audit.
- 判断标准层：DLQ/retry/timeout/report visible and idempotent.
- 反馈层：audit persistence error stops command.

## Impact check

must support P05/P06/P07 and Phase 8 report; no vendor metrics lock, no sync package large output.

## Must read

`WORKFLOW_APPROVAL_AUDIT_DESIGN.md`、test matrix、P04-01/02 output、architecture doc。

## Execution contract

- Capability status：local audit/observability only。
- Probe required：yes — failure injection and DLQ probe。

- Primary route：audit schema/service, retry classes, DLQ fake/metrics names, redacted logging.
- Fallback route：broker unavailable→record pending/manual status, never drop audit.
- Allowed Codex autonomy：observability/queue/test/docs.
- Forbidden Codex guessing：alert thresholds, retention period, external monitor endpoint.
- Required inputs：workflow/policy events, correlation contract.
- Required outputs：audit/metrics/DLQ proof and operator queries.
- Execution entrypoints：integration failure tests and local metrics endpoint.

## Execution steps

1. Encode append-only audit event/sequence.
2. Classify retry/no-retry and DLQ behavior.
3. Add metric/log/redaction contracts.
4. Inject DB/worker failure and verify safe stop/recovery.

## Validation commands

audit mutation denial, retry/DLQ tests, redaction scan, `make regression`.

## Done when

Phase 5/6/7 have a common policy/audit/recovery substrate; metrics do not disclose data.

## Blocked if

audit cannot be atomic/enforced, DLQ drops source/correlation, or retry ambiguous side effects.

## Output 回报格式

metrics/audit schema, failure evidence, Git/rollback, Phase 5–7 parallel contract.

## Git completion

stage observability/queue/audit/tests/docs only; commit/push/readback.
