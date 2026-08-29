# 项目目标｜PROJECT_GOAL

## 北极星目标

在尼泊尔为汾酒与海鲜两条**独立**业务线分别建立以销售结果为中心、可核验、合规前置、由用户与供应链共同负责的最小线上销售闭环：只有在各自业务闸门满足后，才用受控渠道让客户发现可售商品、进入询盘、由人工推进到订单与履约交接；AI、视频、CRM、客户发现和自动化只服务于可测的漏斗改进。研究、文档、同步包或 Git 状态均不等于商业上线，也不能在两条线之间迁移产品、客户、价格、食品/酒类合规或履约结论。

## 当前阶段目标

**CONFIRMED**：2026-08-28 用户 P0 已将项目调整为双业务线 `Sales-First`。汾酒当前处于 `FJ-1 / SR-1 Sellable Offer Ready`。2026-08-29 海鲜 P0 进一步改为 Supplier `SF-S1 IN_PROGRESS_REPORTED / NOT_READY` 与 User `SF-U1 Online Offer Pack Ready` 双工作流。TikTok 不再是默认主线，而是 SF-U2 Route Matrix 中的候选内容工具；多渠道不自动启动。

**SUPERSEDED（海鲜范围，2026-08-29 P0）**：海鲜旧 `SF-2 B2B 人工采购闭环` 不再是用户主线。海鲜改为并行双 Workstream：供应链 `SF-S1` 负责商品、食品/进口、当地报价/样品/成交/收款/冷链/配送/售后；用户 `SF-U0–SF-U8` 负责 Online Acquisition、Qualified Lead、Supplier Handoff 和结果归因。供应链“正在推进”不等于任何业务闸门 READY。

## 当前成功定义

汾酒本阶段的业务准备只在以下事实有来源、日期、责任人和书面确认时成立：

1. 供应链提供真实 SKU、规格、价格与有效期、最低价、库存和补货信息；
2. 可售主体、品牌授权、产品合法可售和相关资质得到核验；
3. 账号主体与管理员权限、收款、仓储配送、退换货、质量、售后和结算责任明确；
4. 指定渠道的当前酒类内容、广告/商品展示、消息和转化边界得到书面核验；
5. 依据以上资料决定一个最小可售 Offer、受控询盘入口、人工销售 owner 和订单交接方式。

任一条件缺失时，内部准备可继续，但对应公开传播、广告、真实销售、收款、订单和履约为 **BLOCKED**。`planning_ready`、`engineering_ready`、`business_ready`、`channel_ready`、`sales_loop_validated`、`automation_ready` 与 `scale_ready` 必须分开报告。

海鲜另须为每一个 SKU 具备产品身份/标签/批次/过敏原、食品与进口责任、冷链/收货/异常、价格/库存/MOQ、收款/配送/售后与 owner 的当前书面证据；货品单本身只支持产品候选登记，不能替代这些条件。

海鲜用户成功首先以 `qualified_lead → supplier_accepted` 衡量；`offered / won / lost / fulfilled` 是供应链负责执行、双方共同归因的最终结果。没有供应链结果反馈时标 `attribution_incomplete`，不得扩 Route 或自动化。
