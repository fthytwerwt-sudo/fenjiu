# P02-01｜Scope 合同与 migration 基线

| 元数据 | 值 |
|---|---|
| task_id / phase | `P02-01` / `phase_02` |
| depends_on / can_run_in_parallel_with | Phase 01 / 无 |
| writes_to | `core/contracts/`、`migrations/`、database adapter、tests/fixtures |
| forbidden_paths | 真实数据/文件、legacy/outputs、external adapters、业务状态 docs |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking + GPT review |

## Goal

实现 tenant/project/business_line、base metadata、data states、source/version/sensitivity 的可迁移合同与数据库约束。

## Context

汾酒/海鲜共享代码但事实隔离；当前只装载 synthetic fixture，PostgreSQL 是唯一业务真值。

## Constraints

所有业务记录 scope non-null；migration 可重放/可测试；不创建真实 tenant/SKU/价格，不让 ORM default scope 代替数据库约束。

## 六层需求确认

- 目标层：基础合同，非供应链导入。
- 机制层：scope/source/version/state 任一缺失 fail closed。
- 实现设计层：`primary_route=Postgres constraints+migrations+Pydantic`；`fallback_route=contract tests before optional RLS`；`capability_status=local`；`probe_required=disposable DB`。
- 流程层：migration→schema test→fixture load。
- 判断标准层：up/down/upgrade、cross scope invalid 全失败。
- 反馈层：migration 风险停止并采用 expand/contract plan。

## Impact check

不能影响 legacy 或 project_sync；检查 compound foreign/unique constraints、future adapter compatibility、fixture marker。

## Must read

`CORE_DATA_CONTRACTS.md`、`ARCHITECTURE_AND_MODULE_BOUNDARIES.md`、`TEST_ACCEPTANCE_ROLLBACK_MATRIX.md`、P01 config。

## Execution contract

- Capability status：local schema contract only。
- Probe required：yes — disposable database migration probe。

- Primary route：scope/base/audit metadata/schema enums/migrations/tests。
- Fallback route：RLS/advanced encryption `DEFER` but leave port/design.
- Allowed Codex autonomy：新增 contracts/migrations/fixtures/tests。
- Forbidden Codex guessing：data retention length、legal region、真实 business scopes。
- Required inputs：core contract table、local DB entrypoint。
- Required outputs：valid/invalid fixture schema and migration proof。
- Execution entrypoints：`make migrate`、database integration tests。

## Execution steps

1. 建 scope/base entity/data-state contracts。
2. 用 DB constraint 实现 key/foreign rules。
3. 写 migration replay/negative tests。
4. 仅加载 synthetic scope fixture。

## Validation commands

`make migrate` on disposable DB；migration upgrade tests；scope/state contract tests；`make regression`。

## Done when

所有下游实体能继承强制 scope/source/version/state；跨线/fixture漏标记失败。

## Blocked if

schema 与核心合同冲突、migration 需要改原资料/生产库、或 DB 不可隔离。

## Output 回报格式

migration graph、约束/negative proof、fixture scope、Git/rollback and P02-02.

## Git completion

仅 stage contracts/migrations/tests；不 stage DB dumps/real data。
