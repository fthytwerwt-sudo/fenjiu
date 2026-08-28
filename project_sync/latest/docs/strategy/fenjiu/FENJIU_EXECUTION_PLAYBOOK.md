# Fenjiu Nepal Execution Playbook｜汾酒尼泊尔销售执行手册

> **业务线：** `fenjiu_nepal`
> **文档状态：** `INTERNAL_EXECUTION_DESIGN / publish_blocked_pending_business_gates`
> **当前阶段：** `FJ-1 Sellable Offer Ready`
> **本文件不等于：** 尼泊尔已获许可、商品已上架、平台已获准、已报价、已成交或可履约。

## 1. 30 秒行动结论

今天只做 `FJ-1`：让供应链为 **一个**待选 Offer 提供当前、可核验、带责任人的书面资料。当前不能拍带具体销售承诺的内容、不能公开发布、不能报价、不能收款、不能下单。

汾酒产品范围仅为 `fenjiu_20_year` 与 `fenjiu_30_year`。它们是产品**标识**，不是已确认的尼泊尔 SKU。先以一个实际到手、供应链批准的瓶装版本完成资料锁定，才选一个渠道、一条 CTA、一名人工销售 owner 跑第一轮闭环。

## 2. 事实、研究与不可猜测项

### 2.1 公开产品研究登记（仅内部事实候选）

| 产品标识 | 可公开复核的候选事实 | 可靠来源 | 当前可否作为尼泊尔可售事实 | 必须由供应链确认 |
|---|---|---|---|---|
| `fenjiu_20_year` | 汾酒官方旗舰店当前页面显示青花 20 的 53%vol、500mL 版本；官方渠道同时可见 42%vol、500mL 和 53%vol、375mL 等变体。 | [汾酒官方旗舰店青花 20 系列](https://fenjiu.jd.com/view_search-717843-25464971-99-1-20-1.html)；[汾酒官方微店 53%vol 500mL](https://detail.youzan.com/show/goods?alias=27a1ti65hgjj3&from_source=gbox_seo) | 否，`RESEARCH_SUPPORTED_ONLY` | 实际瓶型、酒精度、容量、箱规、条码、标签、批次、授权、可售区域、库存、定价与有效期。 |
| `fenjiu_30_year` | 一个当前可访问的海外商业产品页展示 `QINGHUA FEN JIU 30` 为 53% alc.、6×500mL，并使用“aged for 30 years in ceramic vats”的产品表述；官方微店也可见 42%vol、48%vol、500mL 的青花 30 变体。前者是公开商业资料，不是尼泊尔或项目事实。 | [Fenjiu BE：Qinghua Fen Jiu 30](https://fenjiu.be/product/)；[汾酒官方微店产品页](https://detail.youzan.com/show/goods/newest?kdt_id=2592959) | 否，`RESEARCH_SUPPORTED_ONLY` | 同上，且必须确认本项目所称“30 年”是否确为青花 30 的某一 SKU。 |

**结论：** 两个名称存在度数、容量与包装变体。内容、报价、库存和渠道选择必须引用已批准 `offer_ref`，不得仅凭“20 年/30 年”推断规格、定位、价格或供货。

### 2.1.1 公开研究 Source Register（2026-08-28）

| Source ID | 来源类别 | 支持的保守结论 | 不支持的结论 |
|---|---|---|---|
| `FJ-PUB-01` | [Fenjiu BE：Qinghua Fen Jiu 30](https://fenjiu.be/product/) | 当前可访问的海外商业产品页展示 53% alc.、6×500mL、蓝白瓷瓶及“aged for 30 years in ceramic vats”的产品表述；仅作公开产品研究。 | 此页面为尼泊尔官方/授权渠道、项目实际 SKU、库存、价格或可售性。 |
| `FJ-PUB-02` | [汾酒官方旗舰店：青花20系列](https://fenjiu.jd.com/view_search-717843-25464971-99-1-20-1.html) | 当前公开页可见青花20 53%vol、500mL 与多种包装/版本展示。 | 任何版本都是本项目商品或统一规格。 |
| `FJ-PUB-03` | [汾酒官方旗舰店：青花30系列](https://fenjiu.jd.com/view_search-717843-25464972-99-1-20-1.html) | 当前公开页可见青花30系列；可支持“30 不是仅一张单一电商图”的研究判断。 | 某个页面列出的动态价格、库存或中国销售状态可移植到尼泊尔。 |
| `FJ-PUB-04` | [中粮酒业：53度青花20升级版](https://productandservice.cofco.com/search/single-products/2633) | 页面将青花20升级版列为 500mL、中国大陆供应；可作为包装/区域版本差异的旁证。 | 尼泊尔规格、供货、授权或价格。 |
| `FJ-PUB-05` | [汾酒集团品牌文化](https://www.fenjiu.com.cn/brandCulture/index.html) | 可支持青花系列层面的品牌/工艺背景；只在与具体 SKU 无关的教育内容中谨慎使用。 | 20/30 任一 SKU 的固定配方、陈年、价格或可售状态。 |

这些链接的角色是 `RESEARCH_SUPPORTED`，不是供应链证据。任何网页动态价格、库存、促销、评价、配送范围或“官方店”页面的销售状态都不进入 Offer 真值。

### 2.2 Sellable Offer 状态表

| 闸门 | 当前状态 | `FJ-1` 需要的最小书面证据 | 失败处理 |
|---|---|---|---|
| SKU / 商品身份 | `UNKNOWN` | 实物照片、中文/英文标签、SKU、条码、度数、容量、包装、批次 | `BLOCKED`，不得拍到未核验标签。 |
| 价格 | `UNKNOWN` | 供货价、B2C/B2B 价、最低价、样品价、税费/运费、币种、有效期、批准人 | `BLOCKED`，所有内容禁用价格 CTA。 |
| 库存 | `UNKNOWN` | 可承诺数量、仓库地点、盘点日、补货周期、缺货规则 | `BLOCKED`，不写“现货”“可立即配送”。 |
| 合规 / 授权 | `BLOCKED` | 当地主体、进口/销售资格、品牌授权、产品合法可售、年龄/地域/标签要求 | `BLOCKED`，不公开发布或交易。 |
| 履约 | `UNKNOWN` | 收款路径、仓配、运费/时效、破损/退换/售后、财务结算与 owner | `BLOCKED`，不收款、不承诺交期。 |
| 渠道 | `UNKNOWN` | 账号 owner/region/权限、酒类内容/广告/消息边界、询盘入口、用户本次授权 | `BLOCKED`，不发布、不投放。 |

**FJ-1 统一输出：** 每项仅能标 `READY / BLOCKED / MISSING / CONFLICT / EXPIRED`。`READY` 必须含来源、日期、负责人、有效期与版本；不存在“口头 READY”。

## 3. 渠道顺序与扩张规则

| 顺序 | 渠道角色 | 现在状态 | 何时允许进入 | 最小测量 | 停止线 |
|---|---|---|---|---|---|
| `C1` | 候选主发现触点：一个获准的 TikTok 自然内容账号 | `UNKNOWN / NOT_AUTHORIZED` | Offer、账号、酒类政策、非交易询盘路径和本次发布授权都已核验 | `content_id → inquiry → qualified_inquiry` | 观察窗口后没有合格询盘，停止扩量，回到受众/Hook/CTA/Offer 核验。 |
| `C2` | 信任与复用触点：Instagram 或 Facebook **二选一** | `DEFER` | `C1` 已完成一个完整观察周期且需要触达一个已定义但 C1 覆盖不到的成人受众，或 C1 被明确 Stop | 增量合格询盘，而非曝光 | 无增量或政策不明，撤回到 C1。Meta commerce 不用于酒类交易。 |
| `C3` | B2B 精准渠道：获批准的公司入口/受控商务邮件 | `DEFER` | FJ-6 的来源、数据处理依据、DNC、联系审批、B2B Offer 和单次发送授权齐备 | `verified_company → qualified_conversation → offer_request` | 小样本没有合格对话，停止扩大名单/发送。 |

WhatsApp 不得作为酒类交易、下单或付款通道。是否可作为非交易的人工询盘承接，需在使用前另行核验平台政策、当地法律与用户授权；未核验即 `BLOCKED`。

## 4. 阶段总览

| 阶段 | 唯一主要结果 | 当前状态 | 完成才可解锁 |
|---|---|---|---|
| FJ-0 | 销售优先边界与测量规则一致 | `COMPLETE_PLANNING` | FJ-1 |
| FJ-1 | 一个可审计的可售 Offer | `CURRENT` | FJ-2 |
| FJ-2 | 一名 owner 用一个入口完成一次人工销售闭环 | `BLOCKED` | FJ-3 / FJ-5 |
| FJ-3 | 一个渠道经过完整 Keep / Improve / Stop 测试 | `DEFER` | FJ-4 / FJ-7 |
| FJ-4 | 可解释的内容到合格询盘学习循环 | `DEFER` | FJ-7 / FJ-8 |
| FJ-5 | 人工跟进不再遗漏的最小 CRM 节奏 | `DEFER` | FJ-6 / FJ-8 |
| FJ-6 | 受控 B2B 小样本的合格销售对话 | `DEFER` | FJ-7 / FJ-8 |
| FJ-7 | 第二渠道带来可归因的增量 | `DEFER` | FJ-9 |
| FJ-8 | AI 对一个已测量瓶颈有净收益 | `DEFER` | FJ-9 |
| FJ-9 | 渠道与履约都稳定的可扩张闭环 | `DEFER` | 规模化决策 |

## 5. FJ 阶段行动卡

### FJ-0｜Sales Reset

- **Goal / Why now：** 以销售结果而非系统完成度统一两条业务线；避免 TikTok-only、AI-first 与多平台并行复燃。
- **Entry / Main result：** 已有用户方向与 Sales-First 文件；结果是可回读的阶段、渠道与停止线。
- **Actions：** 每次计划先写 buyer、Offer、渠道角色、转化入口、owner、衡量窗口与 Stop line。
- **Daily / Weekly：** 无渠道日常动作；每周仅检查事实/计划是否与业务状态一致。
- **Owner / Supplier / AI：** 用户负责方向；Codex 整理与核验；供应链不产生新事实；AI 不介入。
- **Data / Initial target：** 文档一致性；无对外数据。`Done when=planning_ready=true`。
- **NOT NOW：** 不建 CRM、不发内容、不跑广告、不找客、不做自动化。
- **Fallback / unlock：** 事实源不可读时停止写入；一致后进入 FJ-1。

### FJ-1｜Sellable Offer Ready（当前）

- **Goal / Why now：** 为一个实际 SKU 建立可销售而非“看起来像商品”的证据包。
- **Entry / Main result：** `planning_ready=true`；结果是一个 `offer_ref` 的 READY/BLOCKED 判定，而不是一张漂亮产品图。
- **Actions：**
  1. 供应链从 20 年或 30 年中指定一个实物 SKU；提供第 2 节全部证据。
  2. 用户/人工按字段检查来源、日期、owner、有效期与冲突。
  3. 生成 `offer_fact_sheet`、禁止表达、询盘资格问题及外部执行核验单。
- **Daily / Weekly：** 每日追踪缺件 owner；每周召开 20 分钟缺口复核，只更新证据状态，不估算数值。
- **Target customer / Channel / Content：** 尚不选定客户或平台；仅做内部、无价格/库存/许可承诺的内容草稿。
- **Sales action / Data：** `supplier_request_sent?`、关键字段 READY 数、过期/冲突数、缺件 age。
- **Initial target：** `RECOMMENDED_INITIAL_TEST_THRESHOLD=1` 个完整 Offer 证据包；`STOP_LINE=任一关键闸门未知`。
- **Owner / Supplier / AI：** 供应链提供事实；用户判断可继续；AI 仅可生成表格草稿/缺口摘要。
- **NOT NOW：** 不发布内容、不接询盘、不报价、不做广告/CRM/crawler。
- **Done / Next unlock / Fallback：** 全项 `READY` 并有用户授权时解锁 FJ-2；持续缺件则保留 `BLOCKED`，不以研究替代。

### FJ-2｜First Manual Sales Loop

- **Goal / Why now：** 用一个 Offer、一条 CTA、一个非交易询盘入口与一名 owner 验证客户能否进入人工对话。
- **Entry：** FJ-1 的 Offer、渠道、政策与外部执行授权均 `READY`。
- **Actions：** 选择 C1；为每条内容赋 `content_id`；人工登记询盘、资格、下一步与丢失原因；报价前重新核验 Offer；订单只由供应链书面确认后交接。
- **Daily / Weekly：** 每日检查待回复、到期跟进与事实失效；每周复盘一次转化漏斗和丢失原因。
- **Target / Content / Sales action：** 一个成人目标场景；一类教育或场景内容；非交易 CTA 只邀请合规询盘/信息请求。
- **Data：** `inquiry_at`、`channel_source`、`content_id`、`stage`、`owner`、`next_action_at`、`outcome_ref`。
- **Initial target：** `MINIMUM_TEST_SAMPLE=10` 个已记录询盘或预先到期的观察窗口，取先发生者；不是销量目标。
- **Stop / NOT NOW：** 事实失效、政策/授权不明、无 owner 或无法记录即停；不测试多个平台、不自动回复、不接支付。
- **Done / unlock：** 获得可复盘人工记录后，分别解锁 FJ-3 与 FJ-5；无数据则回 FJ-1 或修入口。

### FJ-3｜First Channel Validation

- **Goal：** 为 C1 得出 Keep / Improve / Stop，而不是积累播放量。
- **Entry / Actions：** FJ-2 运行中；每个周期只改变一个变量（受众、Hook 或 CTA）；保留同一 Offer、入口和 owner。
- **Daily / Weekly：** 发布/记录前核查事实锁；每日响应；周末把 `views → inquiry → qualified_inquiry → conversation` 连起来。
- **Data / Initial target：** `MINIMUM_TEST_SAMPLE=6` 条已发布且可归因内容或一个完整观察窗口；`qualified_inquiry_rate` 与 `conversation_rate` 是主指标。
- **Stop / NOT NOW：** 合格询盘为零、归因失效或政策变化即 Stop；不加渠道、不买量、不将点赞当成功。
- **Done / unlock / Fallback：** 有明确结论才进 FJ-4；若 Improve，重做单一变量而不扩平台。

### FJ-4｜Content-to-Inquiry Learning

- **Goal：** 形成“哪类客户、场景、Hook 和 CTA 带来合格询盘”的证据。
- **Actions：** 对比内容柱/Hook/时长，保持事实锁；每月淘汰只带来虚荣指标的类别。
- **Data / target：** `content_id`、pillar、hook、CTA、qualified inquiry、conversation、offer request；首轮只要求能判断方向，数值无基线时均为 `UNKNOWN`。
- **Stop / NOT NOW：** 没有下游数据就暂停优化内容；不建视频工厂、不批量分发。
- **Unlock：** 可重复的内容假设；可申请 FJ-7 或 FJ-8 的小范围评估。

### FJ-5｜Follow-up / CRM Stabilization

- **Goal：** 真实询盘出现后，确保每个合格客户有 owner 和 next action。
- **Entry：** 已出现多次需跟进的真实询盘，或手工表格已导致可证明的漏跟进。
- **Actions：** 固化阶段、deadline、DNC/删除升级、失单原因；只存合法且最小化的资料。
- **Data / target：** `follow_up_due`、`follow_up_completed`、`missed_follow_up`、stage aging；先测人工基线。
- **Stop / NOT NOW：** 没有真实负担、没有处理依据或没有 owner 时不接第三方 CRM/AI。
- **Unlock：** 跟进节奏稳定后才评估 FJ-6 或 FJ-8。

### FJ-6｜B2B Precision Pilot

- **Goal：** 用小样本验证高匹配企业能否形成合规、可管理的销售对话。
- **Entry：** B2B Offer、来源条款/处理依据、公司核验、DNC/retention、人工 reviewer、联系与发送授权均 `READY`。
- **Target customer：** 高端中餐/泛亚洲餐饮、酒店 F&B、优质酒类渠道、合规礼赠渠道；全部只是候选类型，非真实客户结论。
- **Actions / Data：** 只做 company-first 人工审核；每次联系单独批准；记录 `verified_company`、`contactability_basis`、`qualified_conversation`、`need_confirmed`、`lost_reason`。
- **Initial target：** `MINIMUM_TEST_SAMPLE=10` 家已审核企业；评估合格对话，不评估爬取数量。
- **Stop / NOT NOW：** 没有处理依据、DNC、授权、来源许可或 Offer 事实即停止；不猜邮箱、不批量外联。
- **Unlock：** 有可复盘 B2B 对话后可评估 C3 或 FJ-8。

### FJ-7｜Second Channel Expansion

- **Goal：** 验证第二渠道是否带来 C1 无法获得的可归因增量。
- **Entry：** C1 已获得 Keep，或被明确 Stop 且存在低成本替代假设；Offer/入口/owner 保持稳定。
- **Actions：** 一次只启动 C2；新渠道只改变渠道变量；记录增量而不是汇总流量。
- **Stop / NOT NOW：** 没有增量、无法归因或政策/账号证据失效则关闭；不同时开 Instagram、Facebook、Website。
- **Unlock：** 第二渠道有独立结论，才可能进入 FJ-9。

### FJ-8｜AI Assistance

- **Goal：** 只解决一个已测量的人工重复瓶颈。
- **Entry：** 已有人工 baseline，例如脚本制作时间、跟进完成率或人工研究时长。
- **Actions：** 选择一个 AI 辅助（脚本草稿、回复摘要、跟进提醒或研究摘要），采用人工批准，比较前后指标。
- **Decision metric：** 制作时间、人工修改率、漏跟进、回复质量或有效公司率；无净收益即 `STOP`。
- **NOT NOW：** 不自动回复、不自动报价、不自动发送、不自动更新库存。

### FJ-9｜Automation / Scale

- **Goal：** 在重复、可测且有控制面的工作上降低成本，并扩张已证实的销售路径。
- **Entry：** 有稳定 Offer、渠道、履约、客户结果与人工基线；异常处理和停止开关已验证。
- **Actions / Data：** 只自动化一个可审计低风险步骤；监控人工节省、错误率、合格询盘、订单交接与投诉/DNC。
- **Stop / NOT NOW：** 业务闸门、质量、合规或人工接管任一项不稳即降级为人工；不为“系统完整”扩张。

## 6. 人工销售与跟进 SOP

`New inquiry → eligibility check → need understood → fact recheck → approved offer path → follow-up due → supplier handoff → won / lost / DNC`

| 状态 | Owner | 动作 | Deadline | Exit condition |
|---|---|---|---|---|
| `new_inquiry` | 人工销售 | 记录来源、内容 ID、时间；不承诺价格/库存 | 同一工作日内的目标，由用户后续设定 | 已识别成人/企业、场景和回联许可。 |
| `qualified` | 人工销售 | 询问用途、数量级、区域、时间、个人/企业、是否需要信息或报价 | 下一工作日 | 有明确需求或标 `not_qualified`。 |
| `fact_recheck` | 销售 + 供应链 | 检查 Offer 是否仍 READY | 给报价前 | 事实有效，或 `hold_missing_business_gate`。 |
| `follow_up_due` | 记录 owner | 执行已同意的下一步，记录结果 | 预先约定日期 | 转 `offered / lost / DNC / handoff`。 |
| `supplier_handoff` | 供应链 owner | 确认库存、付款、履约和异常路径 | 未确认不承诺 | 书面交接或回到 hold。 |

**Fenjiu B2C 资格问题：** 你希望了解哪一款经批准的产品资料？使用场景是什么？你所在的允许配送区域？是否已达到当地法定饮酒年龄？希望先了解产品还是在批准后询价？

**Fenjiu B2B 资格问题：** 企业类型/城市？成人餐饮、酒店 F&B、酒类渠道或礼赠的哪种场景？需要了解产品、采购流程还是合规文件？谁负责下一步？何时适合复联？

## 7. Daily / Weekly Rhythm

| 节奏 | 只做什么 | 不做什么 |
|---|---|---|
| 每日（FJ-1） | 追踪供应链缺件、检查版本/有效期、记录冲突 | 不发布、不联系客户。 |
| 每日（FJ-2 以后） | 检查待回复、执行到期 next action、记录询盘/内容/异常 | 不用 AI 自动发送或报价。 |
| 每周 | Offer/库存/合规复核；内容/渠道/询盘/失单复盘；确定一个下周变量 | 不同时开多个新平台或修改多个变量。 |

## 8. 失单原因与归因合同

**Lost reason（只能选择已知项）：** `price_not_available`、`product_mismatch`、`no_stock_or_unconfirmed`、`delivery_or_area`、`timing`、`no_reply`、`trust_or_fact_gap`、`compliance_or_policy`、`decision_delay`、`competitor`、`unknown`。

所有内容/销售记录至少链接：`business_line → content_id → channel → inquiry_ref → conversation_ref → offer_ref → order_ref / outcome_ref`。任何断链都标 `attribution_incomplete`；不以播放量填补缺失的下游证据。
