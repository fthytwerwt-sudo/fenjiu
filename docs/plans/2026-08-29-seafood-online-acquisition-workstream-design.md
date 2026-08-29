# Seafood Online Acquisition Workstream Design｜海鲜线上获客主线设计

## Goal｜目标

把海鲜业务从“用户参与当地采购、样品、报价、谈判与履约”修正为两条职责清楚、可并行但不可互相替代的工作流：供应链负责尼泊尔当地商品、销售与履约；用户负责线上流量、企业发现、内容/搜索/主动获客、Lead Qualification、Supplier Handoff 和基于供应链结果反馈的渠道优化。

## P0 与当前事实

- `CONFIRMED（P0）`：用户不在尼泊尔，海鲜职责是 `Online Acquisition & Traffic`；不承担当地采购推进、样品、报价、谈判、收款、配送或售后。
- `CONFIRMED（P0）`：供应链正在推进当地商品和业务准备；“正在推进”不等于任一 SKU、价格、库存、食品、冷链、付款、报价、样品、成交或履约已经 `READY`。
- `CONFIRMED（P1）`：当前海鲜执行手册把旧 `SF-2` 设计为混合了用户线上动作与供应链当地销售动作的 B2B 人工采购闭环，和本轮 P0 冲突。
- `CONFIRMED（P1）`：20 个商品候选、既有 B2B/B2C Hook、内容卡和 AI `iPhone Natural Look` 资产可保留；它们不构成可售库存、发布授权或渠道优先级证明。

## 方案比较

### Approach A｜只修改旧 SF-2 文案

优点是改动小；缺点是阶段、KPI、内容、CRM 与供应链反馈仍围绕混合职责，后续会再次把当地成交压力推给用户。`REJECTED`。

### Approach B｜双 Workstream + 独立获客手册 + Handoff Contract

供应链采用 `SF-S1 Supplier Product & Fulfilment Readiness`；用户采用 `SF-U0` 至 `SF-U8`。现有 execution playbook 成为双工作流总入口，新建日常线上获客手册和商机交接/反馈合同。旧 `SF-2` 明确 `SUPERSEDED`。这是本轮采用方案。

### Approach C｜新增获客手册但保留旧主线

优点是历史不动；缺点是两个当前主线互相矛盾，使用者无法判断谁负责报价、样品和成交。`REJECTED`。

## Architecture｜结构

```text
Supplier Workstream
SF-S1 Product / Food / Cold-chain / Price / Stock / Local sales / Fulfilment
                         ↓ supplier offer pack + local owner
User Online Acquisition Workstream
SF-U0 Role reset → SF-U1 Online Offer Pack → SF-U2 ICP/Route Lock
→ SF-U3 First Acquisition Test → SF-U4 Qualification/Handoff
→ SF-U5 Acquisition-to-Sale Learning → SF-U6 Second Route
→ SF-U7 AI Assistance → SF-U8 Automation/Scale
                         ↓ qualified lead
Lead Handoff Contract
                         ↑ accepted / offered / won / lost / fulfilled feedback
```

用户主责首先截止于 `QUALIFIED_LEAD → SUPPLIER_HANDOFF`；但用户必须获得 `SUPPLIER_ACCEPTED / OFFERED / WON / LOST / FULFILLED` 结果，否则标 `attribution_incomplete`，不能判断获客质量。

## First ICP Decision

`RECOMMENDED_FIRST_ICP = Kathmandu Valley Chinese / Hotpot Restaurants`。

这是 `HYPOTHESIS`，基于：货品单中的多类虾、鱼、贝和小龙虾与中餐/火锅菜单用途方向较直接；当前 Source Catalog 对餐饮类企业提供唯一已批准的低频 OSM discovery 路线及 REBAN/FNCCI 人工 fallback；餐饮企业的公司身份、菜单和官方网页通常比进口商/批发商的采购资格更容易先做线上验证。酒店销售周期、决策层级和采购入口更复杂；进口商没有已批准直接来源；超市需要零售包装/标签/陈列与配送证据。

改变该决定的证据：供应链明确只接受某一客户类型、首个 `ONLINE_ACQUISITION_READY` 产品不适合中餐/火锅、餐饮企业线上可发现/可联系率低于阈值、或另一个 ICP 的 supplier-accepted lead rate 明显更高。

## First Product Boundary

`SM-03 41/50 单冻虾仁（表内 5 kg/件）`作为 `RECOMMENDED_FIRST_PRODUCT_CANDIDATE`，不是 READY SKU。它只有在供应链提供产品身份、标签/批次/过敏原、素材权、B2B 可接受状态、价格处理规则、MOQ/库存/区域与 owner 后，才能变成 `ONLINE_ACQUISITION_READY`。若证据不全，SF-U1 保持 `BLOCKED`。

## Acquisition Route Decision

- `Primary = Search / Web Prospecting`：仅用获批准的低频 `SEA-OSM-POI-NP` 发现 + 企业自有官网验证；联系人处理/外联仍需要独立依据与授权。
- `Fallback = Digital Referral / Partner`：供应链、REBAN/FNCCI/行业伙伴提供获许可的企业推荐，用户用同一 intake/handoff 记录；不复制协会联系人或会员名单。
- `Later = Organic B2B Content`：只有 Online Offer Pack、内容事实/素材权、一个入口和归因已就绪时，作为 SF-U6 第二路线测试。
- `DEFER = Paid Ads / bulk email / crawler automation`：无 Offer、landing/intake、baseline、政策/授权与 supplier feedback 时不进入。

## First Test Design

以下均为 `RECOMMENDED_INITIAL_TEST_THRESHOLD`，不是历史 baseline 或商业预测：

```text
minimum_sample = 20 company observations
observation_window = 10 business days after route-specific authorization
human_time_cap = 180 minutes
paid_media_cost = 0
target = 12 company-owned-site verified
target = 8 ICP-qualified accounts
target = 5 approved business contact paths
after separate outreach authorization: 5 human-approved contacts
target = 2 replies
target = 1 qualified lead
target = 1 supplier-accepted lead
```

若未获联系人处理/外联授权，测试最高停在 `ICP-qualified accounts + approved contact path candidates`，不得发送；外部效果指标保持 `UNKNOWN`。

## Error / Stop Handling

- 来源条款、ODbL 归因、公司官网、处理依据、DNC、用户授权或供应链 owner 缺失：停止在内部 review。
- 20 个观察中少于 8 个 ICP-qualified：`IMPROVE ICP/source`，不扩大抓取。
- 8 个合格账户中少于 5 个有可批准联系路径：转 fallback referral，不猜邮箱或抓联系人。
- 供应链没有确认接收或没有结果反馈：`attribution_incomplete`，停止扩量。
- 内容、Email、Ads、Crawler 不能连接到 qualified/supplier-accepted lead：保持 `DEFER`。

## Verification Design

验证必须覆盖：旧职责冲突搜索、SF-U0–U8 字段完整性、First ICP/Route 唯一性、Lead/Handoff/Feedback 状态、内容作为候选 Route、Crawler 工具定位、汾酒文件无实质变化、链接/敏感信息/绝对路径、机制验证、同步包、完整回归与远端回读。
