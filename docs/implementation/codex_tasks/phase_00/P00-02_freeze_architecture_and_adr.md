# P00-02｜冻结目录、依赖方向与 ADR

| 元数据 | 值 |
|---|---|
| task_id / phase | `P00-02` / `phase_00` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | `P00-01` / `P00-03` |
| writes_to | `docs/implementation/`, `docs/implementation/adr/` |
| forbidden_paths | 运行时代码目录、原始资料、`.env*`、媒体、同步包生成产物 |
| estimated_risk / recommended_executor | low / GPT review + Codex 5.6 Thinking |

## Goal

将审计结果转为 Phase 1 前可执行的目录、模块 ownership、依赖方向、环境/队列/adapter 边界和 ADR；不创建任何应用代码。

## Context

采用模块化单体、PostgreSQL 真值中心、adapter-first、fixture 与正式数据隔离；治理层仍高于本技术设计。

## Constraints

只修改规划/ADR；不改变业务范围、状态、P0/P1/P2、同步包机制或 legacy 原路径；不选定未核验依赖版本。

## 六层需求确认

- 目标层：冻结可实施边界，非部署。
- 机制层：domain 不导入 adapter；外部动作 feature flag 默认 off。
- 实现设计层：`primary_route=modular monolith`；`fallback_route=延后 optional adapter`；`capability_status=planned`；`probe_required=Phase 1`。
- 流程层：GPT 审核 ADR→Codex Phase 1 实现→测试。
- 判断标准层：每个模块一个 owner/读写边界/禁止项。
- 反馈层：冲突回到 P00-01，不以新 abstraction 隐藏。

## Impact check

确认新目录不与现有脚本冲突；legacy 只包装不迁移；同步包仅提建议不扩 allowlist；海鲜仅共享 contracts。

## Must read

`P00-01` 报告、`AI_NATIVE_SALES_OS_MASTER_PLAN.md`、`ARCHITECTURE_AND_MODULE_BOUNDARIES.md`、`CORE_DATA_CONTRACTS.md`、ADR-AINOS-0001。

## Execution contract

- Capability status：planned architecture; no runtime capability。
- Probe required：yes — document/ADR consistency only。

- Primary route：完善 docs 中目录树、ports、依赖规则和 ADR follow-ups。
- Fallback route：若组件/工具不确定，标 `DEFER/NEEDS_VERIFY`，保留 port。
- Allowed Codex autonomy：文档交叉链接和 ADR 细化。
- Forbidden Codex guessing：生产部署拓扑、端口、真实 provider、资料保留期限和权限主体。
- Required inputs：P00-01 evidence、现有 plan/ADR。
- Required outputs：冻结架构地图和 Phase 1 文件级入口。
- Execution entrypoints：Markdown link check、`git diff --check`。

## Execution steps

1. 对照资产审计修正目录/legacy 表。
2. 明确 domain/application/contracts/adapters/workflows 的单向依赖。
3. 为 optional workflow/crawl/CRM/support/video 写 port 和 exit 规则。
4. 写入 Phase 1 验收与 fallback，不创建 skeleton。

## Validation commands

`rg -n 'apps/|core/|modules/|adapters/' docs/implementation`；文档非空/链接扫描；`git diff --check`。

## Done when

Phase 1 无需重新决定模块归属/是否重写 legacy；未知组件明确为 `DEFER`。

## Blocked if

资产审计缺失、要求直接引入未核验 SaaS/开源系统、或架构会改写治理/业务事实。

## Output 回报格式

ADR 变更、冻结边界、未决项、验证、Git 与 P00-03 并行影响。

## Git completion

仅 stage 规划/ADR 文件；commit/push/readback 或准确说明未完成状态。
