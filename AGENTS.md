# 汾酒尼泊尔｜仓库协作规则

## 1. 项目定位与当前范围

本仓库保存汾酒尼泊尔主线与尼泊尔海鲜独立资料线。2026-08-28 起，汾酒当前正式方向为 `Sales-First`：先满足供应链业务闸门，形成可售 Offer，再通过受控渠道触点、统一询盘承接、人工销售推进、订单交接和反馈验证销售闭环。TikTok 是候选内容触点而非唯一长期中心；多渠道不是自动执行范围。当前阶段为 `SR-1 Sellable Offer Ready` 的资料准备。它不是已上线、已成交、已履约或已获当地许可的证明。

海鲜可作为独立 B2B/B2C 业务线处理，但产品、客户、价格、资质、履约和业务结论不得与汾酒互推。没有明确任务时，默认只处理汾酒主线。

## 2. 进入后的强制阅读顺序

1. 用户本轮明确输入，即 `P0（用户本轮明确输入）`。
2. AGENTS.md。
3. `GPT项目资料同步包_gpt_project_mechanism_sync/` 中的配合机制文件；至少读上传说明、Manifest、系统提示词、事实源边界、P0/P1/P2、六层需求确认和 Codex 执行单模板。
4. PROJECT_ENTRY.md。
5. docs/project/BUSINESS_STATUS.md。
6. docs/project/CURRENT_STATUS.md。
7. docs/project/SOURCE_OF_TRUTH.md。
8. docs/project/SCOPE_AND_BOUNDARIES.md。
9. docs/collaboration/COLLABORATION_STATUS.md。
10. 当前任务直接相关的原始业务文件、脚本或报告。
11. 执行日志、决策、风险、验证记录，以及当前 commit、push 和 remote HEAD 证据。
12. 修改前运行 git status --short --branch。

不得跳过前八项，也不得只凭聊天记忆、派生产物、旧同步包或参考仓库改变项目事实。

## 3. 角色边界

| 角色 | 负责 | 不负责 |
|---|---|---|
| 用户 | 业务目标、优先级、线上销售执行、对外授权与最终验收 | 补猜合作方未提供的事实 |
| 供应链 | 当地合法销售、产品与履约所需资料及本地支持 | 代替用户运营线上销售 |
| ChatGPT | 外层总控、任务拆解与结果审查 | 代替本地读取、测试或 Git 远端验证 |
| Codex / Work | 读取、实现、整理、验证、Git 收尾与明确回报 | 擅自变更业务范围、对外发送或把推测写成事实 |
| 外部研究/审查 Agent | 只读证据、风险与建议 | 写入正式事实、提交、推送或代替最终判断 |

## 3A. 四层协作结构

| 层级 | 负责 | 边界 |
|---|---|---|
| 账号记忆 | 跨项目长期偏好、状态词、Git 安全习惯 | 不保存汾酒实时业务事实 |
| GPT Project | 汾酒项目配合机制、判断顺序、Codex 下发和复审规则 | 不保存实时价格、库存、密码、账号或执行结果 |
| GitHub `main` | 当前项目事实、状态、决策、风险、脚本、报告和同步证据 | 不代表 GPT Project UI 已上传 |
| Codex / Work | 本地读取、实现、验证、落库、commit、push 和远端回读 | 不替代用户授权、供应链确认、平台合规或真实外部执行 |

GPT Project 机制包与 GitHub 当前事实冲突时：机制以 GPT Project 包为参考，项目事实以 GitHub `main` 当前文件为准。用户本轮明确输入可指导本轮，但若形成长期事实，必须落库到 GitHub 后才成为下一轮默认事实。

## 3B. P0 / P1 / P2 来源优先级

- `P0 = 用户本轮明确输入`。
- `P1 = GitHub main 当前事实、当前书面证据和当前验证证据`，包括供应链当前书面资料、commit / push / remote HEAD 和可回读业务证据。
- `P2 = 历史聊天、账号记忆、旧项目机制、外部资料和通用建议`。

冲突时固定执行：`P0 > P1 > P2`。P2 只能提供机制、候选问题或背景，不得冒充当前汾酒项目事实。

P0/P1/P2 只表示信息来源和冲突优先级，不表示业务重要程度、风险级别或供应链缺口等级。商品、价格、库存、资质、账号、收款、履约和合规前置统一称为 `business_gates（业务闸门）`；绝对禁止违反的边界统一称为 `hard_constraints（硬约束）`。

## 3C. GPT Project 机制包边界

`GPT项目资料同步包_gpt_project_mechanism_sync/` 是 GPT Project 配合机制上传包，用户可手动上传到 ChatGPT GPT Project。`project_sync/latest/` 是 GitHub 项目事实交接包，用于新会话或 Codex 读取当前状态快照。两者不能互相替代。

如果 GPT Project 机制包中的以下文件缺失或不可读：上传说明、Manifest、项目系统提示词、事实源边界、P0/P1/P2、六层需求确认、Codex 执行单模板，复杂项目任务和 Codex 下发任务必须标记：

```text
blocked_gpt_project_mechanism_missing
```

简单事实读取可在明确标记缺口后保守进行，但不得修改机制、项目核心边界或业务状态。

GPT Project 包中的 `project_entry/AGENTS.md` 是根目录 `AGENTS.md` 的生成时只读镜像。GitHub `main` 根目录当前 `AGENTS.md` 始终是最新权威版本；两者冲突时以 GitHub 当前文件为准。

## 4. 事实分级

- **CONFIRMED**：当前仓库原始资料、Git 记录或用户明确确认直接支持。
- **INFERRED**：由资料推断，必须写明来源和适用边界。
- **UNKNOWN**：当前资料未找到，需用户、合作方或权威来源补充。
- **BLOCKED**：缺少关键条件，不能安全进入下一动作。
- **SUPERSEDED**：旧结论已被新的、有来源的决定替代；若仅当前执行范围被替代，必须明确写出该边界，原始资料仍保留。

生成文档、同步包、提交或推送均不等于业务事实、合规资格、合作确认、上线、销售或履约已成立。

## 4A. 六层需求确认与实现设计闸门

复杂任务、方向不清、机制修改、Codex 下发、外部资料桥接、用户反馈“不对”或新旧机制冲突时，先检查六层：

1. 目标层：本轮真正达成什么，本轮不做什么。
2. 机制层：触发条件、禁止条件、降级条件和阻断线。
3. 实现设计层：`primary_route`、`fallback_route`、`capability_status`、`probe_required`、`allowed_codex_autonomy`、`forbidden_codex_guessing`、`required_inputs`、`required_outputs`、`execution_entrypoints`、`validation_commands`、`blocked_if_missing`。
4. 流程层：GPT 判断什么，Codex 执行什么，用户确认什么。
5. 判断标准层：技术通过、内容通过、业务通过、Git 通过和用户使用通过分别是什么。
6. 反馈层：失败后回目标、机制、实现设计、流程、事实源、合规还是用户授权。

缺实现设计层时必须标记：

```text
blocked_need_implementation_design_layer
```

不得用更长 prompt 代替实现设计层，不得让 Codex 在执行中补猜核心路线。

## 5. 修改规则

1. 先写清 Goal、Context、Constraints、Impact check、Must read、Execution steps、Validation commands、Done when 与 Blocked if；使用 docs/collaboration/TASK_HANDOFF_TEMPLATE.md 或 SESSION_HANDOFF_TEMPLATE.md。
2. 不删除、批量移动或改写原始业务资料；不把海鲜资料写入汾酒事实。
3. 凭据、Cookie、账号恢复信息、私人联系方式、未审核线索、本地环境配置和大体积派生产物不得提交或打入同步包。
4. 不复制参考仓库的业务内容、绝对路径、账号、客户资料、结论或秘密；只能复用经审计的机制思路。
5. outputs、qa、渲染、媒体和截图只能作线索，不能在未回读源文件时充当唯一事实源。
6. SKU、价格、库存、主体、资质、账号权限、收款、订单、配送、售后和酒类合规前置属于 `business_gates（业务闸门）`，必须依赖当前书面证据；缺失时标记 UNKNOWN 或 BLOCKED。
7. 未获用户明确授权和必要合规条件时，不外发、触达、发布、投放、下单、收款或处理真实付款。
8. 文档生成后实际打开或渲染检查；代码变更后运行相关检查。
9. `AGENTS.md`、系统提示词、P0/P1/P2、六层需求确认、Codex 下发规则或 Git 完成闸门发生机制变化时，必须同时检查并更新 GPT Project 配合机制同步包、Manifest、AGENTS 镜像和验证脚本。

## 6. 状态、决策与交接

实质任务完成后，按影响更新 BUSINESS_STATUS、CURRENT_STATUS、SOURCE_OF_TRUTH、DECISIONS、OPEN_QUESTIONS、RISKS_AND_BLOCKERS、NEXT_ACTIONS、COLLABORATION_STATUS 与 EXECUTION_HISTORY。涉及北极星、渠道边界、AI 优先级或 Codex 判断规则时，同步检查 `docs/strategy/`、GPT Project 机制包、Manifest 与 AGENTS 镜像。

业务状态与协作机制状态必须分开写：前者不因脚本、文档或 Git 成功而升级；后者不替代供应链、平台或合规事实。决策须有来源、日期、影响和状态。

## 7. Git 与同步包

- Codex 执行前必须检查：

```text
pwd
git rev-parse --show-toplevel
git branch --show-current
git remote -v
git status --short --branch
```

- 当前唯一允许写入和 push 的远端为 `fthytwerwt-sudo/fenjiu`；remote 不正确时标 `blocked_wrong_remote`。
- 当前授权工作区为本仓库根目录；不在用户授权工作区时标 `blocked_wrong_workspace_root`。
- 优先在独立分支进行可逆修改；不直接在默认分支做破坏性操作。
- 先查看完整 diff 和 Git 状态；只暂存明确路径，禁止使用 git add .。
- 提交说明为何改变，并遵循仓库适用的 Lore trailers。
- 推送后回读远端 branch、commit、default branch 与 visibility；未回读即为待验证。
- 同步包只包含 allowlist 的轻量上下文，ZIP 默认仅留在本地 dist；其 source_commit 是生成时的基线，不等于随后提交同步包目录的 commit。
- 仓库文件改动只有同时满足 commit 已创建、push 已成功、remote HEAD 已验证、远端关键文件已回读时，才可写 completed。否则使用 `local_only_not_completed`、`blocked_push_failed` 或 `no_file_change_completed_readonly`。

## 8. 回报

不可仅因文件生成成功宣称完成。至少报告：实际修改、验证命令和结果、未验证项、事实分级、分支、commit、推送/远端回读、剩余阻断与下一步。使用 docs/collaboration/EXECUTION_REPORT_TEMPLATE.md。
