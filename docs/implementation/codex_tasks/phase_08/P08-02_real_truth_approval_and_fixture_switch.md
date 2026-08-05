# P08-02｜真实真值审批、版本发布与 fixture 切换

| 元数据 | 值 |
|---|---|
| task_id / phase | `P08-02` / `phase_08` |
| depends_on / can_run_in_parallel_with | `P08-01`，所有关键缺口/冲突已由书面资料解决 | 无 |
| writes_to | 私有数据库的 approval/data-version/feature configuration/audit；脱敏 run report |
| forbidden_paths | Git fixtures replacement, raw files, external send/publish/quote/payment/order adapters |
| estimated_risk / recommended_executor | high / Work + Codex 5.6 Thinking + GPT review |

## Goal

由授权 reviewer 对真实 candidate 的事实版本逐项批准/拒绝/修订，写入 approved truth，严格把 fixture 留在测试环境并对下游执行 safe refresh。

## Context

真实数据可使用不等于外部执行允许；价格、库存、资质、账号/收款/履约和素材权利都要各自 evidence/有效期/批准。

## Constraints

AI 不可批准；禁止 `fixture → real` 原地转换；不得删除旧版本/审计；feature flags 仍默认 external off。

## 六层需求确认

- 目标层：data_usable candidate, not business launch.
- 机制层：separate reviewer, evidence, current policy/freshness, conflict none.
- 实现设计层：`primary_route=approval command+versioned publish`；`fallback_route=remain staging/manual`；`capability_status=requires human approval`；`probe_required=version/invalidation tests`。
- 流程层：reviewer decision→approved facts→TruthFactsChanged→downstream recheck.
- 判断标准层：only approved/fresh facts available; fixture rejected in real config.
- 反馈层：misapproval→revoke/supersede + flags off, never delete.

## Impact check

re-evaluate CS/CRM/content/video fact locks, cache/draft invalidation, roles/audit, data_origin and no Phase 9 action leak.

## Must read

runbook, core contracts, workflow approval design, P08-01 reports, current project facts and Phase 9 gate list.

## Execution contract

- Capability status：human-approved internal real-data reads only。
- Probe required：yes — approval/freshness/fixture-isolation probe。

- Primary route：`make approve-ingestion JOB_ID=<id>` with human reviewers, then internal refresh.
- Fallback route：partial approval keeps only allowable modules internal/disabled.
- Allowed Codex autonomy：execute approved command, invalidation/regression; report results.
- Forbidden Codex guessing：approval decision, permit validity, price/stock correctness, external authorization.
- Required inputs：quality-passed candidates, reviewer/evidence, no unresolved critical conflicts.
- Required outputs：approved fact versions, decision/audit, fixture isolation status, module enablement matrix.
- Execution entrypoints：approve command, internal fact query/invalidation checks.

## Execution steps

1. Verify reviewer role/evidence/freshness/conflict status per fact.
2. Record decision and create immutable approved/superseding versions.
3. Invalidate stale drafts/cache/tasks; test fixture rejection in real scope.
4. Enable only documented internal read modules that have complete facts.

## Validation commands

approval/audit query; fact freshness/fixture isolation/cross-scope tests; downstream invalidation tests; no external action counters.

## Done when

data_usable may be true for named internal capabilities, fixture remains test-only, external_execution_allowed remains false.

## Blocked if

reviewer/evidence unavailable, any required fact missing/conflict/expired, policy/feature flags fail, or external action would be needed.

## Output 回报格式

approved/rejected/blocked fact counts, effective versions, module matrix, flags, rollback reference and Git result.

## Git completion

No real facts in Git. Only sanitized code/docs/report metadata may be staged/pushed/read back.
