# 汾酒尼泊尔项目

这是汾酒在尼泊尔 TikTok 线上销售准备的协作仓库。当前工作重点是供应链启动资料收集与首批商品上线准备；不代表已获许可、已上线、已成交、已收款或已履约。

## 先读什么

新会话先读用户本轮输入和 [AGENTS.md](AGENTS.md)，再读 [GPT Project 配合机制包](GPT项目资料同步包_gpt_project_mechanism_sync/00_GPT_Project上传说明_readme.md) 与 [PROJECT_ENTRY.md](PROJECT_ENTRY.md)。业务现状见 [BUSINESS_STATUS.md](docs/project/BUSINESS_STATUS.md)，仓库与交接机制现状见 [COLLABORATION_STATUS.md](docs/collaboration/COLLABORATION_STATUS.md)。

## 当前边界

- 汾酒当前主渠道仅为尼泊尔 TikTok。
- WhatsApp Business、Meta、Instagram、网站等仅作辅助资产或待确认基础设施，不自动成为独立营销主渠道。
- 供应链需实际提供产品、价格、库存、合规、账户、收款和履约资料；在此之前，它们仍是 UNKNOWN 或 BLOCKED。
- 尼泊尔海鲜是独立业务线，不能直接用于汾酒结论。
- 旧 B2B、多平台和 90 天研究作为历史背景保留，不是当前执行指令。

## 主要目录

| 位置 | 用途 | 默认是否进入同步包 |
|---|---|---|
| docs/project | 业务目标、状态、事实源、边界、决策与下一步 | 是 |
| docs/collaboration | 协作规则、交接模板、执行与机制状态 | 是 |
| GPT项目资料同步包_gpt_project_mechanism_sync | 给 GPT Project 手动上传的长期配合机制包 | 是 |
| scripts | 文档与同步包生成脚本 | 仅同步包构建脚本 |
| project_sync/latest | 当前可交接的轻量同步包 | 是 |
| research_*.json | 历史研究源数据，按事实源地图定向使用 | 否 |
| 原始供应链文档 | 任务相关的原始业务资料 | 否 |
| outputs、qa、媒体、缓存 | 派生产物与检查材料 | 否 |

## 生成同步包

    python3 scripts/build_project_sync_pack.py

ZIP 仅留在本地 dist。完整约束、验证规则和状态回读要求见 [AGENTS.md](AGENTS.md)。

## GPT Project 机制包

GPT Project 上传包位于 `GPT项目资料同步包_gpt_project_mechanism_sync/`。`01_汾酒项目系统提示词_fenjiu_project_system_prompt.md` 复制到 Project Instructions，其余 Markdown 上传为 Project Knowledge。当前状态必须保持：`package_ready_for_manual_upload = true`、`user_uploaded_to_gpt_project_ui = false`，直到用户在 ChatGPT UI 手动上传并验证。
