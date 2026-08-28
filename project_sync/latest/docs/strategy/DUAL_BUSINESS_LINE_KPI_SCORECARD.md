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

## 3. Seafood Scorecard

| Stage | Output Metric | Funnel Metric | Decision Metric | Initial test threshold | Stop line |
|---|---|---|---|---|---|
| SF-1 | 一个 SKU 的标签/批次/食品/冷链/商业/履约证据 | 不适用 | `food_cold_chain_ready` 是否成立 | 1 个 `SM-*` 的完整 Offer 包 | 任一食品、冷链、价格、库存、付款或交接字段未知。 |
| SF-2 | 采购资格问题、fact recheck、owner/next action | qualified procurement conversation | B2B 手工采购路径是否可运行 | 5 个合格采购对话或观察窗口 | 食品/冷链/授权或数据依据失效。 |
| SF-3 | 单一渠道/转介的可审计触点 | qualified procurement conversation rate | B2B 渠道 Keep/Improve/Stop | 10 次可审计触点 | 无合格对话、无法归因或来源不允许。 |
| SF-4 | 规格/菜单/收货内容的单一变量记录 | content→procurement inquiry | 哪种信息促进采购对话 | 1 变量/周期 | 只有播放、没有采购对话。 |
| SF-5 | next action、样品/报价前核验、lost reason | follow-up completion、stage aging | 是否需轻量 CRM | 2 个连续周记录 | 没有真实负担/数据依据。 |
| SF-6 | 已批准 B2C 产品卡、交接 SOP、人工回复 | qualified household inquiry、safe handoff | B2C 是否能安全履约 | 10 个合格询盘或一个观察窗口 | 温控、食品、支付、配送、投诉/退款异常。 |
| SF-7 | 第二渠道或新客群独立归因记录 | incremental qualified inquiry/conversation | 是否有增量 | 1 个完整测试周期 | 无增量/交接负载超限。 |
| SF-8 | AI 前后时间、修改率、QC/跟进数据 | 事实通过率、missed follow-up 变化 | AI Keep/Improve/Stop | 1 个明确定义重复任务 | AI 伪造/遗漏事实或没有净收益。 |
| SF-9 | SKU/区域扩展的事实与异常记录 | handoff、fulfilment、repeat、complaints | 是否稳定规模化 | 连续稳定窗口待真实 baseline 设定 | 食品、冷链、质量、回款或合规事故。 |

## 4. 指标使用规则

1. 观察到 `views/reach` 只能说明内容被看到；不等于兴趣、询盘、采购或订单。
2. `qualified_inquiry` 必须有已定义客户类型、合规范围、owner 和下一步；只有 DM 不等于合格。
3. `order` 只能在用户同意、供应链确认付款/库存/履约交接且可合规记录时填写；草稿、意向和请求均不是订单。
4. `gross_margin`、真实价格、库存、付款或个人数据在没有受控、合法来源时填 `UNKNOWN`，不进入本仓库。
5. 每周只选一个 Decision Metric 并做 `Keep / Improve / Stop`；若没有足够样本，结论是 `continue_measuring`，不是“成功”。
