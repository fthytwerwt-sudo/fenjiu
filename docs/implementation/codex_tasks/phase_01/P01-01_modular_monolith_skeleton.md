# P01-01｜模块化单体工程骨架

| 元数据 | 值 |
|---|---|
| task_id / phase | `P01-01` / `phase_01` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | Phase 00 / 无 |
| writes_to | `apps/ core/ modules/ adapters/ workflows/ fixtures/ migrations/ tests/`、项目配置 |
| forbidden_paths | 顶层 legacy 脚本、原始资料、`.env*`、`outputs/`、同步包 |
| estimated_risk / recommended_executor | medium / Codex 5.6 Thinking |

## Goal

创建可测试但不含业务逻辑的 Python 模块化单体 skeleton，固定 import dependency boundary 和 package ownership。

## Context

Phase 0 已冻结目录；系统真值未来在 PostgreSQL，所有第三方都在 adapters/workflows；当前无真实资料。

## Constraints

不新建微服务、不接数据库/模型/网络、不改 legacy；依赖以现有环境和官方文档最小选择，新增依赖必须在任务报告说明。

## 六层需求确认

- 目标层：空骨架，不实现产品/CRM/客服。
- 机制层：domain/modules 禁止导入 adapters/provider SDK。
- 实现设计层：`primary_route=src layout per architecture doc`；`fallback_route=defer optional package`；`capability_status=implementation`；`probe_required=import/test`。
- 流程层：Codex 创建→boundary tests→GPT review。
- 判断标准层：空 import 可运行、反向 import 必失败。
- 反馈层：命名/依赖冲突回 Phase 0 ADR。

## Impact check

确保 `.gitignore` allowlist 不吞新源码；不遮蔽顶层脚本名称、不同业务线或 project_sync 路径。

## Must read

`P00-01..03` 报告、`ARCHITECTURE_AND_MODULE_BOUNDARIES.md`、`CORE_DATA_CONTRACTS.md`、`TEST_ACCEPTANCE_ROLLBACK_MATRIX.md`。

## Execution contract

- Capability status：local skeleton only。
- Probe required：yes — import and dependency-boundary probe。

- Primary route：创建 architecture doc 中的 packages、typed base errors/interfaces、dependency tests。
- Fallback route：对尚无明确 owner 的模块只建 placeholder/README，不建抽象层。
- Allowed Codex autonomy：可创建指定空包、tests、项目配置。
- Forbidden Codex guessing：业务字段、环境端口、真实 tenant/price/SKU、provider credentials。
- Required inputs：冻结目录树、Python toolchain 决定。
- Required outputs：importable skeleton、dependency test、目录说明。
- Execution entrypoints：项目 test runner、`python -m compileall`。

## Execution steps

1. 确认 clean branch/status 和 Phase 0 证据。
2. 建 packages 与单向 import contract。
3. 为 domain/application/contracts/adapters/workflows 添加 ownership README 或 module docstrings。
4. 跑 import/architecture tests 和敏感扫描。

## Validation commands

`python -m compileall`（新代码）；test runner 的 boundary suite；`rg` 检查 forbidden imports；敏感/路径扫描。

## Done when

骨架可 import、无外部 adapter 调用、no business fact、legacy hash 未变、架构测试绿。

## Blocked if

需先决定 ORM/框架版本、发现 ignore/legacy 名冲突、或新增依赖未获允许。

## Output 回报格式

目录/依赖、测试、依赖新增、legacy/业务状态影响、Git、下一张 P01-02。

## Git completion

只 stage 新 skeleton/config/tests；commit/push/remote readback 依仓库规则执行。
