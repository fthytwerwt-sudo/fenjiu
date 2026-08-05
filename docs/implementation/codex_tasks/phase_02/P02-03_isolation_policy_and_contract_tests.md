# P02-03｜业务线隔离、fixture 防护与合同测试

| 元数据 | 值 |
|---|---|
| task_id / phase | `P02-03` / `phase_02` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | `P02-02` / 无 |
| writes_to | `core/security/`、repositories、fixtures、tests、docs |
| forbidden_paths | 原始资料、任何 external send/publish adapter、legacy、`.env*` |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking + security/GPT review |

## Goal

把 tenant/project/business-line isolation、fixture production separation、sensitivity 和 policy denial 锁进 repository/command 层与 regression tests。

## Context

UI filter/prompt 不是隔离；fixture-first 只能用于内部模拟，绝不能成为 real fallback。

## Constraints

无跨线 service account、无 wildcard default scope、无可将 fixture 改为 real 的 command；所有拒绝记录 audit intent。

## 六层需求确认

- 目标层：执行硬隔离，不开业务能力。
- 机制层：scope/fixture violation fail closed。
- 实现设计层：`primary_route=scope context+DB/repository guard`；`fallback_route=deny all unscoped`；`capability_status=local`；`probe_required=adversarial tests`。
- 流程层：command receives scope→policy→repository→audit.
- 判断标准层：cross-line/fixture external attempts all fail.
- 反馈层：泄漏为 P0 security blocker，冻结下游。

## Impact check

验证 Phase 3 import、P05 CRM、P06 messages、P07 videos 将完整传递 scope；不改变业务状态/资料。

## Must read

`CORE_DATA_CONTRACTS.md`、`TEST_ACCEPTANCE_ROLLBACK_MATRIX.md`、`WORKFLOW_APPROVAL_AUDIT_DESIGN.md`、P02-01/02 output。

## Execution contract

- Capability status：synthetic isolation enforcement only。
- Probe required：yes — adversarial cross-scope/fixture probe。

- Primary route：scope context, permission hooks, fixture guard, adversarial contract tests.
- Fallback route：不支持的 adapter 默认 disabled/deny.
- Allowed Codex autonomy：security module/tests/fixture metadata。
- Forbidden Codex guessing：tenant roles/owners, legal retention, real data classifications.
- Required inputs：scope entities/truth models.
- Required outputs：isolation/fixture policy evidence and stable error codes.
- Execution entrypoints：test suite and policy denial reports。

## Execution steps

1. 实现 scope propagation/validation。
2. 实现 fixture `external_execution_allowed=false` enforcement。
3. 测试 cross tenant/project/business line、unscoped、candidate/expired truth。
4. 记录 audit/policy result contract。

## Validation commands

adversarial tests；fixture external-action denial suite；sensitive/path scan；`make regression`。

## Done when

下游只能在正确 scope 和 approved data 内工作，且 Phase 3 可安全写入 staging。

## Blocked if

任一 cross scope path 可通、fixture leak、或 policy 无法记录拒绝。

## Output 回报格式

attack cases、拒绝证据、覆盖率、Git/remaining risk、Phase 3 readiness。

## Git completion

只 stage security/repository/tests/docs；严格 diff、commit/push/readback。
