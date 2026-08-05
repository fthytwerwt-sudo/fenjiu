# GitHub 事实源读取机制

## 何时必须读 GitHub

以下场景必须读取 GitHub `main` 当前文件：

- 用户问当前项目状态、下一步、阻断、是否能上线。
- 需要判断 SKU、价格、库存、资质、账号、收款或履约。
- 要给 Codex 下发仓库写入任务。
- GPT Project 机制包与用户记忆、旧同步包或聊天内容冲突。
- Codex 回报完成，需要复审 commit、push、remote readback。

## 默认读取顺序

1. `AGENTS.md`
2. `PROJECT_ENTRY.md`
3. `docs/project/BUSINESS_STATUS.md`
4. `docs/project/CURRENT_STATUS.md`
5. `docs/project/SOURCE_OF_TRUTH.md`
6. `docs/project/SCOPE_AND_BOUNDARIES.md`
7. `docs/collaboration/COLLABORATION_STATUS.md`
8. 当前任务直接相关的业务文件、脚本或报告

## 读取后必须复述

给用户或 Codex 继续执行前，至少复述：

- 当前主线和阶段。
- 用户与供应链职责边界。
- 当前 `UNKNOWN` / `BLOCKED` 项。
- 本轮任务属于业务事实、机制同步、文档导出还是仓库落库。
- 是否会影响业务状态、协作状态、执行历史或 Git 远端事实。

## 禁止

- 禁止只凭 GPT Project Knowledge 回答动态项目事实。
- 禁止用 `project_sync/latest` 旧快照覆盖 GitHub 当前文件。
- 禁止把生成脚本输出当作唯一事实源。
- 禁止把外部研究、聊天摘要或参考仓库结论写成汾酒 `已确认`。

## GitHub 无法读取时

标记 `BLOCKED / github_fact_source_unreadable`，说明缺哪份文件、影响什么判断、最小解锁动作是什么。可以继续讲机制，但不能声称当前事实已确认。
