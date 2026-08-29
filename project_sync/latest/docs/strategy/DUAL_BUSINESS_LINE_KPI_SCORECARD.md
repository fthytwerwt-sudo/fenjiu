# Dual Business Line KPI Scorecard｜双业务线阶段指标与决策计分表

> **指标三分法：** `Output Metric` = 团队做了什么；`Funnel Metric` = 客户发生了什么；`Decision Metric` = 下一步是否继续。
> **数据诚实规则：** 以下数字都是 `RECOMMENDED_INITIAL_TEST_THRESHOLD` 或 `MINIMUM_TEST_SAMPLE`，不是历史 baseline、销量预测或商业承诺。真实第一轮数据出现后必须重新校准。

## 1. 通用指标定义

| 指标类别 | 例子 | 不能被替代为 |
|---|---|---|
| Output | Offer 资料完成、内容发布、人工回复、到期跟进、公司审核 | 文件存在、AI 生成、抓取页数。 |
| Funnel | reach、profile visit、DM、inquiry、qualified inquiry、conversation、offer request、offer、order、fulfilment、repeat | 播放、点赞、页面/公司数量。 |
| Decision | Offer 是否 READY？渠道 Keep/Improve/Stop？AI 是否净收益？是否进入下一阶段？ | 单次感觉、单一好评、系统完成度。 |

**共同数据字段：** `business_line`、`stage`、`channel_source`、`content_or_campaign_ref`、`product_or_offer_ref`、`inquiry_at`、`customer_type`、`owner`、`next_action_at`、`outcome_ref`、`lost_reason`。真实电话、邮箱、消息正文、付款与个人资料不进入 Git、文档示例、日志或测试 fixture。

## 2. Fenjiu Scorecard

| Stage | Output Metric | Funnel Metric | Decision Metric | Initial test threshold | Stop line |
|---|---|---|---|---|---|
| FJ-1 | 每项 Offer gate 有来源/日期/owner/有效期 | 不适用 | `business_ready` 是否成立 | 1 个完整 Offer 包 | 任一 SKU/价格/库存/合规/履约/渠道字段未知。 |
| FJ-2 | 已记录人工回复、资格问题、next action | inquiry、qualified inquiry、conversation | 一个入口+owner 是否可运行 | 10 个已记录询盘或一个观察窗口，以先到者为准 | 事实/政策/授权/owner 失效。 |
| FJ-3 | 6 条有 `content_id` 且同一 CTA 的内容，或一个观察窗口 | qualified inquiry rate、conversation rate | C1 = Keep / Improve / Stop | 6 内容样本 | 合格询盘为零、归因缺失或政策问题。 |
| FJ-4 | 每条内容有 pillar/hook/CTA/结果 | content→inquiry→conversation | 哪个变量继续测试 | 1 个变量/周期 | 只看 views 或无法连接下游。 |
| FJ-5 | 到期 next action、失单原因、DNC 升级 | follow-up completion、missed follow-up、stage aging | 轻量 CRM 是否仍足够 | 2 个连续周人工记录 | 无真实压力或无处理依据。 |
| FJ-6 | 已审核企业、单次接触批准 | qualified B2B conversation、need confirmed | B2B 是否有价值 | 10 家已审核企业 | 来源、DNC、处理依据、Offer 或授权缺失。 |
| FJ-7 | 新渠道的独立 content/source/entry ID | incremental qualified inquiry | C2 是否有增量 | 1 个完整 C2 周期 | 无增量/无法归因。 |
| FJ-8 | AI 前后任务时间/QC 记录 | reply acceptance、漏项变化或下游内容质量 | AI Keep/Improve/Stop | 1 个重复任务的 before/after 对照 | 无净收益、事实失真或人工风险上升。 |
| FJ-9 | 稳定 SOP、异常/回退记录 | order handoff、fulfilment、repeat（若合法记录） | 是否可扩张 | 连续稳定窗口由用户/供应链定义 | 任一合规、履约、投诉或质量异常。 |

## 3. Seafood Dual Workstream Scorecard

### Supplier Workstream

| Stage | Output Metric | Funnel Metric | Decision Metric | Initial threshold | Stop line |
|---|---|---|---|---|---|
| SF-S1 | Product/food/import/price/stock/cold-chain/local owner evidence；Lead ACK 与 outcome feedback | accepted→offered→won/lost→fulfilled | `Can supplier accept and close this Lead?` | 1 Online Offer Pack input + 1 supplier owner；真实 SLA 待确认 | 任一事实缺失/过期、无 owner、无结果反馈；“正在做”不等于 READY。 |

### User Online Acquisition Workstream

| Stage | Output Metric | Funnel Metric | Decision Metric | RECOMMENDED_INITIAL_TEST_THRESHOLD | Stop line |
|---|---|---|---|---|---|
| SF-U0 | 职责、handoff、feedback 文档 | 不适用 | `role_boundary_clear` | 当前主线角色冲突 0 命中 | 本地销售仍分配给用户。 |
| SF-U1 | Online Offer Pack 完整字段 | 不适用 | `safe_for_lead_generation?` | 1 个 `ONLINE_ACQUISITION_READY` Product Pack | 产品/规格/素材权/询盘接受/owner 缺失。 |
| SF-U2 | 1 Product + 1 ICP + 1 Region + 1 Route test brief | 不适用 | `first_test_authorizable?` | 1 个完整 brief | 多 ICP、多 Route、无 supplier owner。 |
| SF-U3 | 20 observations、site verified、ICP-qualified、approved path candidates | reply、qualified lead、supplier accepted | Primary Route Keep/Improve/Stop | 10 business days；≤180 human minutes；目标 12 site-verified、8 ICP-qualified、5 path candidates；联系指标仅在另获授权后启用 | 来源/处理/DNC/授权缺失；<8 ICP-qualified 先改 ICP/source。 |
| SF-U4 | qualified records、handoffs、supplier ACK | supplier_accept_rate、lead_to_supplier_conversation | `handoff_stable?` | 前 3 个 Qualified Lead 100% 有接收状态；ACK 1 business day 为建议 | 无 owner、ACK、basis，或私人资料要进入 Git。 |
| SF-U5 | complete attribution、weekly review、cost record | lead_to_offer、lead_to_order、lost reason | best ICP/Route/Content | 前 5 个 supplier decisions；feedback completeness ≥80% 为建议 | `attribution_incomplete`，不扩量。 |
| SF-U6 | 独立 second-route IDs 与成本 | incremental qualified/supplier-accepted leads | Second Route K/I/S | 1 个与 Primary 同口径完整窗口 | 无增量、无法归因、supplier capacity 不稳。 |
| SF-U7 | before/after time、human decision、fact error | qualified lead quality 不劣化 | AI K/I/S | 20 units 或 2 完整批次 | 错误增加、节省很少、人工审核不可控。 |
| SF-U8 | automation runs、override/fallback、capacity record | accepted lead 与 sales outcome | scale / rollback | 连续 2 个稳定周期 | ICP/Offer/Route/handoff/feedback 任一失稳。 |

海鲜用户 KPI：`target_accounts_found`、`qualified_accounts`、`leads`、`qualified_leads`、`supplier_accept_rate`、`lead_to_offer_rate`、`cost_per_qualified_lead`、`cost_per_supplier_accepted_lead`。`won/revenue/fulfilled` 是联合结果，不能全部压成用户个人成交责任。

## 4. 指标使用规则

1. 观察到 `views/reach` 只能说明内容被看到；不等于兴趣、询盘、采购或订单。
2. `qualified_inquiry` 必须有已定义客户类型、合规范围、owner 和下一步；只有 DM 不等于合格。
3. `order` 只能在用户同意、供应链确认付款/库存/履约交接且可合规记录时填写；草稿、意向和请求均不是订单。
4. `gross_margin`、真实价格、库存、付款或个人数据在没有受控、合法来源时填 `UNKNOWN`，不进入本仓库。
5. 每周只选一个 Decision Metric 并做 `Keep / Improve / Stop`；若没有足够样本，结论是 `continue_measuring`，不是“成功”。
