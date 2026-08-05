# P04-01｜Workflow state、checkpoint 与恢复

| 元数据 | 值 |
|---|---|
| task_id / phase | `P04-01` / `phase_04` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | Phase 03 / 无 |
| writes_to | `workflows/`、application/queue port、contracts/tests |
| forbidden_paths | real external adapters, production accounts, truth schemas, legacy scripts |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking |

## Goal

实现可替换 workflow runner 的 run state、checkpoint、idempotency、pause/resume/retry/DLQ 合同，并比较 LangGraph adapter 与 simple runner。

## Context

Phase 3 已有 approval/truth；workflow 只能协调 command，不拥有 business data/approval/audit truth。

## Constraints

任何可能外部副作用的步骤都需 approval/idempotency；不接真实 provider，LangGraph 只在 probe 通过后引入。

## 六层需求确认

- 目标层：可靠内部 orchestration。
- 机制层：resume never duplicates side effect; checkpoint no secrets.
- 实现设计层：`primary_route=simple DB state runner`；`fallback_route=remain simple`；`capability_status=probe`；`probe_required=LangGraph contract comparison`。
- 流程层：command→run→checkpoint→approval→resume→audit.
- 判断标准层：retry timeout/DLQ/recovery test pass.
- 反馈层：state mismatch/unknown effect sends to manual queue.

## Impact check

保持 queue port/DB truth 分离；没有实现 external sends；检查 P05/P06/P07 都能用相同 workflow contract。

## Must read

`WORKFLOW_APPROVAL_AUDIT_DESIGN.md`、open-source strategy、P03-03 E2E、test matrix。

## Execution contract

- Capability status：local workflow runner; no external side effect。
- Probe required：yes — simple runner versus optional LangGraph contract probe。

- Primary route：workflow run/checkpoint/idempotency/outbox fake/simple runner。
- Fallback route：defer LangGraph and document reason。
- Allowed Codex autonomy：workflow code/fake/tests。
- Forbidden Codex guessing：provider retry safety, production concurrency, human SLA.
- Required inputs：approved command/approval contracts.
- Required outputs：run/recovery/DLQ semantics and probes.
- Execution entrypoints：workflow integration suite, `make regression`。

## Execution steps

1. 创建 workflow/run state contracts.
2. 实现 checkpoint/resume and safe retry classes.
3. build simple runner and optional LangGraph adapter probe.
4. test crash/replay/timeout/DLQ no duplication.

## Validation commands

workflow E2E with fake side effect; idempotency/DLQ tests; sensitive log scan.

## Done when

same fixture produces same state/audit in simple and optional adapter; unknown side effect stops manual.

## Blocked if

checkpoint contains secrets/PII, repeat safety cannot be proven, or framework becomes truth owner.

## Output 回报格式

runner decision/probe, recovery proofs, test/Git, input to P04-02.

## Git completion

stage workflows/ports/tests/docs only; commit/push/readback.
