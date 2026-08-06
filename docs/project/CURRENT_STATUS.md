# 当前项目总览｜CURRENT_STATUS

- **最近更新**：2026-08-05
- **用途**：本页只提供业务与协作的短摘要和路由；详细事实以链接文件为准。

## 业务状态摘要

- **CONFIRMED**：汾酒当前正式范围为尼泊尔 TikTok 线上销售准备，阶段为供应链启动资料收集与首批商品上线准备。
- **UNKNOWN**：供应链尚未在当前资料中实际提供 SKU、价格、库存、补货、主体/资质、品牌授权、账号权限、收款、仓储配送、售后及负责人确认。
- **当前最重要任务**：先补齐商品单、价格规则和库存，再确认首批可上架 SKU，并补齐账号、资质、收款和履约资料。
- **P0 阻断**：在上述资料及 TikTok 当前酒类内容/广告边界获得书面确认前，不能进入公开发布、广告、真实销售、收款、订单或履约。

详情：[BUSINESS_STATUS.md](BUSINESS_STATUS.md)｜[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)｜[RISKS_AND_BLOCKERS.md](RISKS_AND_BLOCKERS.md)｜[NEXT_ACTIONS.md](NEXT_ACTIONS.md)

## 协作机制状态摘要

- **CONFIRMED**：固定入口、事实分级、任务交接、执行记录和同步包机制已建立。
- **CONFIRMED**：GPT Project 配合机制包已在仓库内生成并通过本地验证；包内 AGENTS 镜像与根 AGENTS SHA-256 一致。
- **部分成立**：V2 正在将公开历史脱敏、干净 main、远端默认分支、visibility 和新同步包验证收口；这些事项必须以最终远端回读为准。
- **最近远端验证**：待 V2 最终阶段回读，不能用本文件编辑或本地 commit 替代。

## 工程规划状态摘要

- **CONFIRMED（规划层）**：`docs/implementation/` 已形成 AI Native Sales OS 的 Phase 0–8 分阶段蓝图、机器可读依赖图和每阶段 3 张 Codex 任务卡；该规划承接 GPT Project / GitHub / Codex 治理机制，不替代它。
- **未实施**：本摘要不表示已创建运行时工程、数据库、队列、CRM、客服、视频服务或真实资料导入；技术实施须按 `docs/implementation/CODEX_EXECUTION_INDEX.md` 一次一张任务卡推进。
- **CONFIRMED（工程 Phase 0）**：P00-01、P00-02 与 P00-03 已完成远端回读；P00-03 在干净独立 task worktree 通过 12 项回归和两种扫描模式。外置盘根目录存在既有 ignored 禁入路径，故不得在该根目录运行回归；Phase 1 只可在新建、干净的独立 task worktree 中启动。
- **BLOCKED（外部业务）**：该规划不解除 SKU、价格、库存、主体/资质、账号、收款、履约或 TikTok 酒类边界的业务闸门；公开发布、报价、收款、下单和履约仍保持停止。

详情：[COLLABORATION_STATUS.md](../collaboration/COLLABORATION_STATUS.md)｜[SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md)

## 范围提醒

旧 B2B、多平台与 90 天研究已作为历史输入保留，且仅在当前执行范围层面被替代；海鲜资料线独立，不自动进入汾酒任务。
