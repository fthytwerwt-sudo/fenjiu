# 汾酒尼泊尔｜仓库协作规则

## 1. 项目定位

本仓库服务于汾酒在尼泊尔市场的研究、合规前置、渠道/供应链协作与执行准备。目录中也保存尼泊尔海鲜协作资料；它是独立业务线，不能被自动当成汾酒事实、客户、产品或结论。

当前资料证明“研究、方案与协作清单存在”，不证明已取得当地许可、已上线、已成交、已履约或已经由合作方确认。

## 2. 进入后的强制阅读顺序

1. `AGENTS.md`
2. `PROJECT_ENTRY.md`
3. `docs/project/CURRENT_STATUS.md`
4. `docs/project/SOURCE_OF_TRUTH.md`
5. `docs/project/SCOPE_AND_BOUNDARIES.md`
6. 与任务直接相关的原始业务文件或脚本
7. 修改前运行 `git status --short --branch`

不得跳过前四项，也不得只凭聊天记忆改变项目事实。

## 3. 角色边界

| 角色 | 负责 | 不负责 |
|---|---|---|
| 用户 | 目标判断、优先级取舍、对外授权、最终验收 | 替 Agent 猜测缺失事实 |
| ChatGPT | 外层总控、需求澄清、任务拆解、结果审查 | 代替本地读取、测试或 Git 验证 |
| Codex / Work | 读取、实现、整理、验证、Git 收尾与明确回报 | 擅自改业务目标、对外发送、把推测写成事实 |
| 外部研究/审查 Agent | 只读证据、风险和建议 | 写入正式事实、提交、推送或代替最终判断 |

## 4. 事实分级

每个状态、结论或关键字段都应使用下列标签之一：

- `CONFIRMED`：当前仓库原始资料、Git 记录或用户明确确认能够直接支持。
- `INFERRED`：由资料推断，必须附推断来源和适用边界。
- `UNKNOWN`：当前资料没有找到，需用户、合作方或权威来源补充。
- `BLOCKED`：缺少关键条件，不能安全进入下一动作。
- `SUPERSEDED`：旧结论已被新的、有来源的决定替代。

`INFERRED` 绝不能写成 `CONFIRMED`。生成文档、同步包、提交或推送均不等于业务事实已获确认。

## 5. 修改前与修改中的规则

1. 先明确 Goal、Context、Constraints、Impact check、Done when 与 Blocked if。
2. 不删除原始资料；不批量移动资料；不修改任务范围外文件。
3. `research_channels.json`、`.env`、凭据、Cookie、私人联系方式和账号恢复信息不得提交或打入同步包。
4. 不复制参考仓库的业务内容、绝对路径、账号、客户资料、结论或秘密；只能复用机制思路。
5. `outputs/`、`qa/`、`_qa*/`、媒体和渲染物是派生材料，不能在未回读源文件时充当唯一事实源。
6. 酒类合规、平台可用性、账号权限、SKU、价格、库存、订单、付款与履约必须依赖当前书面证据；缺失即标为 `UNKNOWN` 或 `BLOCKED`。
7. 禁止在没有用户明确授权和必要合规条件时外发、触达客户、发布、投放、下单或处理真实付款。
8. 文档生成后须实际打开或进行相应渲染检查；代码修改后须运行相关检查。

## 6. 任务执行标准

每个可执行任务至少应含以下栏目：

```text
Goal｜目标
Context｜上下文
Constraints｜边界
Impact check｜影响面检查
Execution steps｜执行步骤
Done when｜完成标准
Blocked if｜阻断条件
Output｜回报格式
```

使用 `docs/collaboration/TASK_HANDOFF_TEMPLATE.md` 或 `SESSION_HANDOFF_TEMPLATE.md`。范围、事实源或阻断条件不清时，先停在澄清/审计层，而不是用更多实现掩盖不确定性。

## 7. 状态、决策和交接

实质任务完成后，检查并按需更新：

- `docs/project/CURRENT_STATUS.md`
- `docs/project/DECISIONS.md`
- `docs/project/OPEN_QUESTIONS.md`
- `docs/project/RISKS_AND_BLOCKERS.md`
- `docs/project/NEXT_ACTIONS.md`
- `docs/collaboration/EXECUTION_HISTORY.md`
- 项目同步包（运行 `python3 scripts/build_project_sync_pack.py`）

只有有来源、日期、影响和状态的取舍才进入 `DECISIONS.md`。执行日志只记录实际读取、修改、命令、验证、阻断与下一步。

## 8. Git 与同步包规则

- 不直接在默认分支做破坏性修改；优先独立分支。
- 先查看 `git status` 与完整 diff；只 `git add` 明确路径，禁止用 `git add .` 掩盖范围。
- 提交信息说明为何变更，并遵循本仓库适用的 Lore trailers。
- 推送前执行适当验证；推送后回读远端分支/commit。
- 不提交缓存、临时文件、视频、渲染物、未审核线索库或秘密信息。
- 每个重要节点运行同步包脚本；同步包只包含 allowlist 中的轻量上下文文件，ZIP 默认留在本地 `dist/`。

## 9. 完成与回报

不可仅因“文件生成成功”宣称完成。至少报告：实际修改、验证命令与结果、未验证项、事实分级、分支、commit、推送状态、剩余阻断和下一步。使用 `docs/collaboration/EXECUTION_REPORT_TEMPLATE.md`。
