# Seafood Online Acquisition Playbook｜尼泊尔海鲜线上获客操作主手册

> **Owner：** 用户（Online Acquisition & Traffic）
> **Current stage：** `SF-U1 Online Offer Pack Ready`
> **Capability：** `planning_and_internal_execution_ready`
> **External state：** `external_acquisition_requires_route_specific_authorization`
> **一句话：** 找到正确企业，形成 Qualified Lead，交给供应链成交，再用成交结果优化获客。

## 1. 今天打开电脑先做什么

```text
只打开 1 个候选产品：SM-03
→ 检查供应链是否补了产品身份、标签/规格、素材权、接受客户类型、价格处理、MOQ/库存/区域、owner 和事实有效期
→ 更新 Online Offer Pack：READY / MISSING / CONFLICT / EXPIRED
→ 若未 ONLINE_ACQUISITION_READY：只准备内部 ICP/Route/内容，不发现或联系企业
→ 若以后 READY 且获 Route 授权：进入 SF-U2，再只锁 1 ICP + 1 Route
```

用户今天不做尼泊尔当地采购、样品、报价、谈判、收款、配送或售后。

## 2. Implementation Design｜实现设计层

```yaml
primary_route: "seafood online acquisition workstream; user owns acquisition, supplier owns local sales and fulfilment"
fallback_route: "when contact/policy/authorization evidence is missing, complete only internal ICP, source, content, lead schema and test design"
capability_status:
  planning_and_internal_execution_ready: true
  external_acquisition_requires_route_specific_authorization: true
probe_required: true
allowed_codex_autonomy:
  - audit seafood plans
  - recommend first ICP and route from current evidence
  - design stages, KPI, lead and handoff schemas
  - prepare internal research, content and templates
forbidden_codex_guessing:
  - supplier readiness
  - price or stock
  - cold-chain or food permits
  - real customer demand
  - contact processing legality
  - platform sending permission
  - external authorization or sales outcome
execution_entrypoints:
  - documentation and internal review only
  - no real crawling, sending, posting or advertising in this task
blocked_if_missing:
  - current fact source unreadable
  - user/supplier role ambiguity
  - route-specific policy, contact basis, DNC or authorization evidence missing
```

## 3. North Star Funnel｜线上获客北极星

```text
DISCOVERED → ENGAGED → LEAD → QUALIFIED_LEAD
→ SUPPLIER_HANDOFF → SUPPLIER_ACCEPTED → SUPPLIER_FOLLOW_UP
→ OFFERED → WON / LOST → FULFILLED
```

用户主责到 `QUALIFIED_LEAD → SUPPLIER_HANDOFF`；供应链主责从 `SUPPLIER_ACCEPTED` 开始。但供应链必须按 `lead_id` 回传 `OFFERED / WON / LOST / FULFILLED`，否则用户标 `attribution_incomplete` 并停止扩量。

## 4. Online Offer Pack｜SF-U1

### Ready contract

```yaml
product_ref: "SM-03"
product_name: "supplier-confirmed value required"
category: "shrimp candidate"
specification: "supplier-confirmed value required"
packaging: "supplier-confirmed value required"
target_customer_hint: "supplier input, not market fact"
approved_product_images: []
asset_usage_rights: "MISSING"
b2b_availability_status: "UNKNOWN"
b2c_availability_status: "UNKNOWN"
price_display: "NO"
price_route: "SUPPLIER_CONFIRMATION"
moq_status: "UNKNOWN"
stock_status: "UNKNOWN"
service_area: "UNKNOWN"
supplier_contact_owner: "MISSING"
claims_allowed: []
claims_prohibited: []
fact_validity: "MISSING"
acquisition_readiness: "BLOCKED"
```

只要产品身份、关键规格、素材权、供应链 owner 或“能否接真实询盘”不可判断，就不能标 `ONLINE_ACQUISITION_READY`。不公开价格不是阻断：可以使用 `price_display=NO` 与 `price_route=SUPPLIER_CONFIRMATION`。

## 5. ICP Decision｜SF-U2

### 5.1 Candidate ICP Matrix

全部评估是 `HYPOTHESIS`；`H/M/L` 是相对测试优先级，不是历史业绩。

| ICP | Product fit | Online discoverability | Contactability | Potential order size | Supplier closing ability | Repeat | Cost | Sales cycle | 当前结论 |
|---|---|---|---|---|---|---|---|---|---|
| Kathmandu Chinese / Hotpot Restaurants | H | H：OSM + 官网；REBAN manual fallback | M / 待处理依据 | M | `UNKNOWN` | M–H | L–M | Short–M（假设） | `RECOMMENDED_FIRST_ICP` |
| Kathmandu Seafood Restaurants | H | M | M / 待处理依据 | M | `UNKNOWN` | M–H | M | Short–M（假设） | 第二餐饮细分，不与 first sample 混合 |
| Hotel F&B | H | H：OSM/HAN/NTB | L–M | H | `UNKNOWN` | H | M–H | Long | 后置：采购层级和收货要求复杂 |
| Frozen Food Wholesaler / Foodservice | H | M–L | L | H | `UNKNOWN` | H | M | M–Long | 后置：冷库、分销、许可难线上证实 |
| Supermarket | M | H | M | H | `UNKNOWN` | M–H | M | Long | 后置：零售包装/标签/陈列未 READY |
| Importer / Distributor | H | L：无批准直接来源 | L | H | `UNKNOWN` | H | H | Long | `BLOCKED_NO_APPROVED_DIRECT_SOURCE` |

### 5.2 First ICP

```text
RECOMMENDED_FIRST_ICP = Kathmandu Valley Chinese / Hotpot Restaurants
FIRST_PRODUCT_CANDIDATE = SM-03 41/50 单冻虾仁，NOT_READY
REGION = Kathmandu + Lalitpur + Bhaktapur as one acquisition cluster
```

**Why this one first：** 候选货品与中餐/火锅菜单方向匹配较直接；当前批准来源能低频发现餐饮企业并回官网验证；第一轮可把公司、菜单、产品兴趣和业务入口作为线上可观察证据。

**Why not the others yet：** 酒店/批发/进口/超市分别受长销售周期、冷库/许可、批准来源或零售包装证据限制。

**Decision change evidence：** Supplier Accept 范围不含该 ICP；SM-03 无法 READY；20 个观察中少于 8 个 ICP-qualified；或另一 ICP 在独立样本的 supplier-accepted rate 更高。

## 6. Acquisition Route Matrix｜SF-U2

### 6.1 Route A–E

| Route | Time | Cost | Control | Precision | Nepal/access evidence | Contact | Manual load | Attribution | Policy risk | Supplier fit | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A Search / Web Prospecting | 快 | 低 | 高 | 高 | `PARTIAL`：OSM 低频 discovery 可用 | `BLOCKED` until basis | 中 | 高 | 中 | 高 | `PRIMARY` |
| B Business Contact Outreach | 依赖 contact | 低 | 高 | 高 | Email/form 技术存在 | `BLOCKED` | 中 | 高 | 高 | 高 | Primary 的后半步，不单独启动 |
| C Organic Content | 中–慢 | 低–中 | 中 | 中 | 平台技术候选存在，项目账号/权限未知 | inbound | 高 | 中 | 中 | 中 | `LATER / SF-U6` |
| D Paid Acquisition | 快但不确定 | 高 | 中 | 中 | 账号/市场/政策/landing 未核验 | inbound | 中 | 高 | 高 | 低–中 | `DEFER` |
| E Digital Referral / Partner | 快（若有伙伴） | 低 | 中 | 高 | 依赖 supplier/association permission | introduced | 低–中 | 高 | 低–中 | 高 | `FALLBACK` |

### 6.2 Explicit decision

```text
RECOMMENDED_PRIMARY_ACQUISITION_ROUTE = Search / Web Prospecting
FALLBACK_ROUTE = Digital Referral / Partner
LATER_ROUTE = Organic B2B Content
DEFER = Paid Ads, bulk Email, automated crawler
```

Primary 只允许：`SEA-OSM-POI-NP` 低频发现 → company-owned website verification → ICP qualification → approved business contact path candidate。它不允许自动联系人收集、CRM 写入或外联。

### 6.3 Current external evidence boundary（2026-08-29）

| 层 | 当前证据 | 支持 | 不支持 |
|---|---|---|---|
| OSM licence | [OSM Copyright / ODbL](https://www.openstreetmap.org/copyright) | 在归因与 ODbL 条件下使用开放数据 | 数据完整性、企业采购能力或联系人处理。 |
| Public Nominatim | [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/) | 低频、最多 1 request/sec、识别 User-Agent、归因 | 系统化查询、区域全部 POI、details scraping、generic no-code search service。 |
| Google Maps | [Google Maps Platform Terms](https://cloud.google.com/maps-platform/terms/) | 仅说明 Maps 服务有独立条款 | 抽取/导出/抓取 business names、addresses、reviews 作名单。 |
| Business Email | [Gmail sender guidelines](https://support.google.com/mail/answer/81126?hl=en) | 发送域认证、TLS、反垃圾、退订等投递要求 | 联系人处理依据、当地法律、项目发送授权。 |
| TikTok content | [Content Posting API](https://developers.tiktok.com/docs/en/content-posting-api-get-started) | 获批准 scope、用户授权与审计后存在发布技术能力 | 项目账号/地域/食品内容、发布/商业授权已经就绪。 |
| TikTok commercial content | [Commercial Content Disclosure](https://ads.tiktok.com/help/article/about-the-commercial-content-disclosure-setting-for-advertisers?lang=en) | 商业内容需要相应披露 | 尼泊尔账号、广告市场、landing、产品事实或投放授权。 |
| Meta/Instagram | 官方技术与 Business Help 页面需要后续账号/当前页面复核 | 只保留 Route candidate | 当前 Nepal 账号、API、广告、消息或发布授权。 |

固定分层：`technical_capability ≠ platform_policy ≠ local_legal_status ≠ project_authorization`。当前 Route A 的内部企业发现设计为 `PARTIAL`；真实 contact/outreach、Route C 发布和 Route D 广告均为 `BLOCKED`。

## 7. SF-U0–SF-U8 Stage Cards

### SF-U0｜Role & Interface Reset

- **Goal：** 用户=Online Acquisition；供应链=Local Sales + Fulfilment。
- **Entry：** P0 与旧 SF-2 冲突。
- **User Action：** 维护职责、交接点、反馈点和不可替代边界。
- **Supplier Dependency：** 确认本地 owner 和结果反馈责任。
- **Output / Funnel / Decision：** 职责文件完成 / 无 / `role_boundary_clear=true`。
- **Initial Threshold：** 角色冲突搜索当前主线 0 命中。
- **Stop：** 报价/样品/配送仍分配给用户。
- **NOT NOW：** 不开发、不获客、不发送、不发布。
- **Done / Next：** 六个责任问题均能回答；进入 SF-U1。

### SF-U1｜Online Offer Pack Ready（当前）

- **Goal：** 1 个产品可安全用于 Lead Generation。
- **Entry：** SF-U0 clear；供应链提供新增资料。
- **User Action：** 检查资料、更新 pack、标缺口、准备内部素材。
- **Supplier Dependency：** 产品/规格/素材权、接受状态、价格处理、MOQ/库存/区域、owner、claims 和 validity。
- **Output / Funnel / Decision：** 1 pack / 无 / `Can this product generate leads safely?`
- **Initial Threshold：** `1 ONLINE_ACQUISITION_READY product`。
- **Stop：** 身份、规格、素材权、supplier owner 或可否接受询盘缺失。
- **NOT NOW：** 不要求 20 个商品一起 READY；不找客户。
- **Done / Next：** pack 可供 ICP、内容和 Qualification 使用；进入 SF-U2。

### SF-U2｜ICP & Acquisition Route Lock

- **Goal：** 只锁 1 Product + 1 ICP + 1 Region + 1 Route。
- **Entry：** 至少 1 pack READY。
- **User Action：** 复核 ICP Matrix、Route Matrix、sample/window/cost/stop。
- **Supplier Dependency：** 明确可承接客户类型与 Lead owner。
- **Output / Funnel / Decision：** ICP/Route test brief / 无 / `first_test_authorizable?`
- **Initial Threshold：** 1 个完整 test brief；无 baseline 时所有数字标 initial threshold。
- **Stop：** 同时包含多个 ICP、多个主渠道或无 supplier owner。
- **NOT NOW：** 不并行酒店/餐厅/批发/B2C；不开始发送。
- **Done / Next：** First ICP/Primary/Fallback 唯一且阻断清楚；进入 SF-U3。

### SF-U3｜First Online Acquisition Test

- **Goal：** Search/Web Route 能否稳定产生 First ICP 的 Qualified Lead。
- **Entry：** Online Offer Pack READY；来源/处理/DNC/外联/用户授权逐步满足。
- **User Action：** 低频发现、官网验证、ICP qualification、只识别批准业务路径、人工批准每次 contact、记录响应。
- **Supplier Dependency：** Lead acceptance owner 和可接受范围。
- **Output Metric：** company observations、site verified、ICP-qualified、approved contact paths、human-approved contacts。
- **Funnel Metric：** reply、qualified lead、supplier accepted lead。
- **Decision Metric：** Primary Route = Keep / Improve / Stop。
- **Initial Threshold：** 20 observations / 10 business days / ≤180 human minutes / paid media 0；目标 12 site-verified、8 ICP-qualified、5 path candidates。只有另获发送授权后才启用 5 contacts、2 replies、1 qualified、1 supplier accepted。
- **Stop：** 来源/归因/处理依据/DNC/授权缺失；<8 ICP-qualified 时先改 ICP/source；不得加抓取量。
- **NOT NOW：** 不用 TikTok/Meta/Ads 做并行测试；不猜邮箱、不自动发送。
- **Done / Next（双出口）：**
  - 未获外联授权：完成 20 observations、12 site-verified、8 ICP-qualified、5 contact-path candidates 的内部基线后，状态为 `SF-U3 / internal_discovery_baseline_only / waiting_authorization`；不进入 SF-U4。
  - 已获 Route-specific 处理/DNC/发送授权：至少 1 个 Qualified Lead 且 Handoff 前置完整，才进入 SF-U4。

### SF-U4｜Lead Qualification & Supplier Handoff

- **Goal：** Qualified Lead 可清楚、低摩擦地交给供应链。
- **Entry：** 合法 Lead + supplier owner + handoff contract。
- **User Action：** 最小资格判断、生成 handoff、取得 ACCEPT/NEED_INFO/REJECT/DUPLICATE/OUT_OF_SCOPE。
- **Supplier Dependency：** 在约定时间确认接收与 next action。
- **Output Metric：** qualified records、handoffs、acknowledged decisions。
- **Funnel Metric：** supplier_accept_rate、lead_to_supplier_conversation_rate。
- **Decision Metric：** `handoff_stable?`
- **Initial Threshold：** 前 3 个 Qualified Lead 100% 有接收状态；`ack_target=1 business day` 为建议阈值。
- **Stop：** 无 owner、缺处理依据、真实私人资料要进入 Git、供应链不确认接收。
- **NOT NOW：** 用户不报价、送样、谈判或追本地订单。
- **Done / Next：** 每条 Lead 有状态/next action；进入 SF-U5。

### SF-U5｜Acquisition-to-Sale Learning

- **Goal：** 判断哪个 ICP + Route + Content 产生有价值商机。
- **Entry：** supplier decisions 和 outcome feedback 可按 lead_id 回传。
- **User Action：** 关联 traffic→lead→qualified→accepted→offered→won/lost，计算成本和 lost reason。
- **Supplier Dependency：** accepted/contacted/offer/won/lost/fulfilled/feedback_date。
- **Output Metric：** complete attribution records、weekly review。
- **Funnel Metric：** supplier_accept、lead_to_offer、lead_to_order、lost reason。
- **Decision Metric：** 哪个变量 Keep/Improve/Stop。
- **Initial Threshold：** 前 5 个 supplier-decision records 或一个完整窗口；≥80% 有结果反馈是建议完整度阈值。
- **Stop：** feedback completeness <80% 或结果无法回链；标 `attribution_incomplete` 并不扩量。
- **NOT NOW：** 不用 views、公司数量或发送量代替销售价值。
- **Done / Next：** 有一项明确学习结论；可进 SF-U6/U7。

### SF-U6｜Second Acquisition Route

- **Goal：** 验证第二 Route 是否带来增量。
- **Entry：** Primary 已有 Keep/Improve/Stop；handoff/feedback stable。
- **User Action：** 只增加 Organic B2B Content 或另一个明确 Route，保持 Product/ICP/Region/CTA 尽量稳定。
- **Supplier Dependency：** 继续接受/反馈，确认新增流量不超过承接能力。
- **Output / Funnel / Decision：** 独立 route IDs / incremental qualified and accepted leads / C2 Keep-Improve-Stop。
- **Initial Threshold：** 1 个与 Primary 同口径的完整测试窗口。
- **Stop：** 无增量、无法归因、承接压力或政策/账号未准备。
- **NOT NOW：** 不同时开 TikTok/Instagram/Facebook/Email/Ads/Crawler。
- **Done / Next：** 独立结论；进入 SF-U7/U8。

### SF-U7｜AI Assistance

- **Goal：** AI 降低一个已量化人工成本。
- **Entry：** company research/content/summary/reminder 任一有人工作业 baseline。
- **User Action：** 选择一个任务做 before/after；人工接受/修订/拒绝。
- **Supplier Dependency：** 事实和结果仍由供应链确认。
- **Output Metric：** human minutes、AI minutes、review decisions。
- **Funnel Metric：** fact_error_rate、qualified_lead_rate 不劣化。
- **Decision Metric：** AI Keep/Improve/Stop。
- **Initial Threshold：** 同一任务至少 20 个单位或 2 个完整批次比较。
- **Stop：** 节省很少、错误增加、Qualified Lead 质量下降或人工审核不可控。
- **NOT NOW：** 不自动联系、发送、报价、更新库存或判断合规。
- **Done / Next：** 净收益与安全成立；进入 SF-U8。

### SF-U8｜Automation & Scale

- **Goal：** 自动化已稳定且低风险的一步，并扩大已证明 Route。
- **Entry：** ICP/Offer/Route/Qualification/Handoff/Feedback stable + AI net benefit。
- **User Action：** 一次自动化一个动作，保留 audit、人工 override 和 fallback。
- **Supplier Dependency：** 承接 capacity、结果反馈与停止线稳定。
- **Output / Funnel / Decision：** automation runs / accepted leads and outcomes / scale or rollback。
- **Initial Threshold：** 连续 2 个稳定周期；真实窗口由 baseline 重新设定。
- **Stop：** 质量、DNC、事实、交接、反馈或 supplier capacity 失稳。
- **NOT NOW：** 不建设全自动获客/销售系统。
- **Done：** 自动化有净收益且可回退；再由用户决定规模化。

## 8. Lead Qualification 快速判断

B2B Qualified Lead 至少有：`company_name`、`company_type`、`city`、`source`、`product_interest`、`need`、主动提供时的 `volume_range`、`timing`、`contact_route`、已知时的 `decision_role`、`next_action`、`consent/contact_basis`。

不要为“信息完整”而收集不必要私人资料。完整 schema 见 Lead Handoff Contract。

## 9. Daily Operating Modes

| Stage | 用户每日模式 |
|---|---|
| SF-U1 | 检查 supplier facts → 更新 pack → 列缺口 → 内部素材准备 |
| SF-U2 | 研究 1 ICP → 锁 1 Route → 写 sample/window/cost/stop |
| SF-U3 Search | 发现公司 → 官网验证 → ICP score → 识别候选业务路径 → 内部记录；未授权不联系 |
| SF-U3 Content | 选 1 Content Card → AI 视频/图片 → QC；未授权不发布 |
| SF-U4 | 检查 Lead → Qualification → Handoff → 确认 supplier status |
| SF-U5+ | 汇总反馈、成本、lost reason → 每周只改 1 变量 |

## 10. Weekly Review / Cost Contract

每周只回答：最佳 ICP、最多 Qualified Lead 的 Route、最低成本 Route、产生真实商机的 Content、Supplier Accept 数、Offer 数、Lost Reason、下周唯一变量。

每个 Route 记录：`human_minutes`、`tool_cost`、`media_cost`、`cost_per_lead`、`cost_per_qualified_lead`、`cost_per_supplier_accepted_lead`。没有合法真实数据填 `UNKNOWN`。

## 11. Crawler / Content / Email / Ads 定位

- `Crawler = Acquisition Tool`，仅可能帮助 source/company discovery、公开公司信息 extraction 与 verification assistance；绝不自动升级 Company→Lead 或联系人→发送。
- `Content = one Acquisition Route`，可用于 trust、education、awareness、inbound lead、retargeting support 和 sales enablement；TikTok 不预设为 First Route。
- `Email = approved contact step`，不是独立成功指标；必须有来源、处理依据、DNC、认证、用户单次授权与 reply reconciliation。
- `Ads = later route`，Offer、Landing/Intake、归因和 baseline 缺一即 `DEFER`。

## 12. NOT NOW

不开发大型 CRM / LangGraph / 全自动 crawler；不接真实 Gmail sender；不猜邮箱、批量发送；不实际发布 TikTok/Meta；不投广告；不联系企业；不处理真实客户私人信息；不生成订单、报价或收款。当前只完成路线、内部执行手册、模板、指标与交接合同。
