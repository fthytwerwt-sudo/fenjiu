# 项目统一入口｜PROJECT_ENTRY

本文件给第一次接手“汾酒尼泊尔”仓库的 ChatGPT、Codex、Work 或人工协作者使用。它只做导航，不替代原始业务资料。

## 30 秒定位

- **项目目标**：在不把研究结论当成商业结果的前提下，形成可核验的尼泊尔市场、合规、渠道和供应链准备体系。
- **当前阶段**：`research_and_partner_readiness`（研究与合作方准备），不是已上线或已销售状态。
- **当前最重要任务**：取得并核验当地法律/平台书面边界、当地销售主体与授权、SKU/价格/库存/履约和数据归属后，再决定是否进入任何试点。
- **默认安全动作**：资料整理、核验清单、内部草稿、受控模拟；不自动外发、不发布、不投放、不下单。

## 必读顺序

1. [AGENTS.md](AGENTS.md)
2. 本文件
3. [当前项目状态](docs/project/CURRENT_STATUS.md)
4. [事实源地图](docs/project/SOURCE_OF_TRUTH.md)
5. [范围与边界](docs/project/SCOPE_AND_BOUNDARIES.md)
6. 与当前任务直接相关的原始资料；不要用派生产物替代原始资料。

## 已确认与未知

- `CONFIRMED`：仓库中已有三份汾酒研究/执行 JSON、供应链协作文档、文档生成脚本，以及本协作系统。
- `INFERRED`：研究资料中的市场优先级、渠道建议和传播路径均只在其标注的证据日期与假设范围内成立。
- `UNKNOWN`：SKU、价格、库存、进口/销售主体、许可证、平台许可、预算、订单流程、账号归属和真实合作方确认。
- `BLOCKED`：在上述关键输入获得当前书面验证前，不得把酒类公开传播、投放、达人、直播、Shop、导流或销售写成可执行。

## 事实源与输出

- 项目状态以 `docs/project/CURRENT_STATUS.md` 为准。
- 目标和范围以 `docs/project/PROJECT_GOAL.md`、`docs/project/SCOPE_AND_BOUNDARIES.md` 为准。
- 业务原始资料的优先级见 `docs/project/SOURCE_OF_TRUTH.md`。
- 每次实质执行后，更新状态、决策（若有）、风险/下一步和 `docs/collaboration/EXECUTION_HISTORY.md`。

## 交接给新会话

先生成同步包：

```bash
python3 scripts/build_project_sync_pack.py
```

然后把 `project_sync/latest/` 或 `dist/` 中最新 ZIP 交给新会话，并附上 [docs/sync/README.md](docs/sync/README.md) 的交接 Prompt。新会话必须先复述目标、当前阶段、事实分级、任务边界和完成标准，再执行。
