# Nepal Seafood Execution Playbook｜尼泊尔海鲜销售执行手册

> **业务线：** `seafood_nepal`
> **文档状态：** `INTERNAL_EXECUTION_DESIGN / publish_blocked_pending_business_gates`
> **当前阶段：** `SF-1 Seafood Offer & Cold-Chain Ready`
> **Primary route：** `RECOMMENDATION: B2B-first`；**Secondary route：** `B2C-after-validated-fulfilment`。

## 1. 30 秒行动结论

今天只做 `SF-1`：以 2026 年第一批次货品单为**产品候选清单**，补齐一个可履约 SKU 的规格、标签、批次、价格、库存、食品/进口责任、冷链、收款、售后和负责人。不能把货品单写成“尼泊尔现货库存”、不能公开销售、报价、收款或配送。

建议先跑 B2B：先以一个酒店/餐厅/冻品渠道的合规采购与冷链交接路径，验证规格、收货、损耗、配送窗口和复购潜力。B2C 必须等到相同 SKU 已有价格、库存、食品资料、订单、支付、配送半径、售后和消费端合规路径。这是根据当前“箱规/重量为主、履约数据缺失”的 `RECOMMENDATION`，不是已验证的市场结论。

## 2. 货品单登记：可写入的产品候选，不是销售库存

### 2.1 来源与解释边界

用户提供的《尼泊尔市场冻品 2026 年第一批次进货清单》共有 5 页。可视觉复核的表内汇总是 **20 个货品行、数量 554、总重量 2,895 kg、外箱总立方 11.2323145**。这些数字描述该表，不足以证明货物已发运、到港、通关、可售、合规、仍在库、可配送或可承诺。

PDF 是电子表格导出的图文清单，部分行的外箱尺寸/立方为 0 或空，产品 14 与 15 的总重量为 0。所有这些值须保留为 `manifest_recorded_value`，不能修正、推算或当作重量/温控事实。

### 2.2 产品候选登记表

| `product_ref` | 清单产品名称（保留原表语义） | 数量 | 表内总重量 kg | 表内包装/规格摘记 | 当前可用结论 |
|---|---:|---:|---:|---|---|
| `SM-01` | 500/700 带鱼 / Hairtail | 10 | 95 | 17 条/件，含箱 10 kg | 鱼类候选；`BLOCKED` 规格、标签、库存与冷链。 |
| `SM-02` | 2125 真空虾仁 / frozen shrimps | 10 | 48 | 600 g/板，8 板/件 | 虾类候选；未确认物种、净重、标签。 |
| `SM-03` | 41/50 单冻虾仁 / Frozen skinless shrimp | 20 | 100 | 290 只/件，5 kg/件 | 虾类候选；规格仅为表内记录。 |
| `SM-04` | 50-100 手冰耗儿鱼 / Navodon septentrionalis | 10 | 44 | 4.4 kg/件 | 鱼类候选；物种译名需供应链确认。 |
| `SM-05` | 小河虾 / Small freshwater shrimp | 2 | 5 | 10 袋/件，2.5 kg/件 | 虾类候选；不代表适用 B2C 包装。 |
| `SM-06` | 700/800 多宝鱼 / Turbot | 10 | 100 | 12 条/件，10 kg/件 | 鱼类候选。 |
| `SM-07` | 青口贝 / Mussel | 80 | 320 | 4 kg/件 | 贝类候选；过敏原/标签 `UNKNOWN`。 |
| `SM-08` | 50-60 王牌盐冻虾 / Frozen salted shrimp | 20 | 168 | 6 盒/件，9 kg/件 | 虾类候选；配料/盐度 `UNKNOWN`。 |
| `SM-09` | 12 头黑虎虾 / Black tiger shrimp | 20 | 80 | 10 盒/件，4 kg/件 | 虾类候选；实际物种/等级待确认。 |
| `SM-10` | 单冻干冰青虾 / Freshwater shrimp | 20 | 100 | 140 条/件，5 kg/件 | 虾类候选；“干冰”不替代冷链记录。 |
| `SM-11` | 14 条黄花鱼 / Yellow croaker | 10 | 100 | 14 条/件，含箱 10 kg | 鱼类候选。 |
| `SM-12` | 花甲 / Original clam | 150 | 600 | 10 袋/件，4 kg/件 | 贝类候选；物种/标签待确认。 |
| `SM-13` | 72 生蚝 / Oysters on the half shell | 50 | 350 | 72 只/件，7 kg/件 | 贝类候选；食品安全与储存要求 `BLOCKED`。 |
| `SM-14` | 8 头辽参 / sea cucumber | 10 | 0 | 8 只/袋 | 表内重量为 0；不得估算。 |
| `SM-15` | 大 A 鲍鱼 / Abalone | 2 | 0 | 8 袋/件 | 表内重量为 0；不得估算。 |
| `SM-16` | 小龙虾 / Crayfish | 100 | 750 | 10 盒/件 | 甲壳类候选；未确认规格/标签。 |
| `SM-17` | 1620 白灼虾 / cooked shrimp | 10 | 35 | 10 盒/件 | 虾类候选；加工条件/配料 `UNKNOWN`。 |
| `SM-18` | 800/900 大白鲷 / Dabai Diao fish | 10 | 120 | 12 包/件 | 鱼类候选；中文/英文品种对应待确认。 |
| `SM-19` | 蛏子肉 / Frozen razor clam meat | 5 | 25 | 5 kg/件 | 贝类候选；过敏原/标签待确认。 |
| `SM-20` | 大板鱿鱼须 / Quick-frozen seasoned squid | 5 | 17.5 | 3.5 kg/件 | 头足类候选；“调味”配料/过敏原待确认。 |

### 2.3 海鲜 Offer 必备资料

| 资料组 | 每个拟售 SKU 要有的证据 | 当前状态 | 无证据时的动作 |
|---|---|---|---|
| 产品主数据 | 产品名、物种/品种、形态、规格/等级、净重、包装、原产地、批次、标签、保质期、过敏原 | `UNKNOWN` | 禁止做规格、产地、口感和配料承诺。 |
| 冷链 | 储存/运输温度、冷库、配送车/箱、温控记录、收货标准、中断处置、解冻要求 | `UNKNOWN / BLOCKED` | 禁止报价、接单和配送。不可自行填 `-18°C`。 |
| 食品与进口 | 责任主体、进口/食品/产品登记、检验检疫、标签与追溯文件 | `UNKNOWN / BLOCKED` | 不上架、不向客户声称合规。 |
| 商业 | B2B/B2C 价、MOQ、现有库存、补货、运费、损耗、退款/退换、结算与有效期 | `UNKNOWN` | 不报价格、不承诺库存或交期。 |
| 履约 | 覆盖区域、配送窗口、收款、售后、质量异常、召回与 owner | `UNKNOWN` | `publish_blocked_pending_business_gates`。 |

## 3. B2B-first / B2C-second 决策矩阵

以下是优先顺序的设计判断；没有真实数据的列均为 `HYPOTHESIS`，不得写成市场事实。

| 判断维度 | B2B：酒店/餐饮/冻品渠道 | B2C：消费者直销 | 当前判断 |
|---|---|---|---|
| `time_to_first_sale` | 可由少量采购对话和样品/验收推进；`HYPOTHESIS` | 需要内容、零售页、支付和逐单配送；`HYPOTHESIS` | B2B 优先验证。 |
| `order_value` | 箱规/多 SKU 可能更适合批量采购；`HYPOTHESIS` | 单次家庭订单规模未知 | B2B 优先。 |
| `gross_margin_potential` | 未获成本、损耗或价格资料 | 未获成本、获客或履约资料 | 两者 `UNKNOWN`，不做利润选择。 |
| `customer_acquisition_difficulty` | 企业识别、审批、冷链/采购核验难 | 消费者内容与信任建立难 | 都需测试；不同时启动。 |
| `cold_chain_feasibility` | 可在少量收货点验证 | 要覆盖多个家庭时更复杂 | B2B 优先。 |
| `payment_feasibility` | 企业结算与付款主体未知 | 消费者支付路径未知 | 两者 `BLOCKED`。 |
| `repeat_potential` | 菜单/分销补货可能存在；`HYPOTHESIS` | 家庭复购未知；`HYPOTHESIS` | 先用 B2B 记录验证。 |
| `compliance_burden` | 食品、进口、标签、冷链均适用 | 同时增加消费者信息、零售、配送与售后 | B2C 后置。 |
| `content_dependency` | 重点是规格/菜单/冷链信息与采购信任 | 重点是内容发现、便利性、家庭场景 | B2C 对内容依赖更高。 |
| `sales_effort` | 高触点但账户少 | 单量小但服务触点多 | 先量化 B2B 人工时间。 |
| `available_evidence` | 货品单有箱规/重量线索 | 没有零售包装、价格、配送/支付证据 | B2B-first。 |

## 4. 渠道顺序与扩张规则

| 顺序 | 渠道/角色 | 进入条件 | 测量 | Stop line |
|---|---|---|---|---|
| `S-C1` | B2B：用户/供应链明确转介，或经批准的公司采购入口 | 一个具体 SKU、B2B 价/MOQ、冷链/食品/履约、数据处理与单次接触授权 | `qualified_procurement_conversation`、受控样品/验收意愿、交接质量 | 缺任一闸门、无采购匹配或无合格对话即不扩名单。 |
| `S-C2` | B2B 信任内容：获准的单一行业内容触点或合作方展示页 | S-C1 有合格对话，需要解释规格/菜单适配，且内容/平台事实有效 | `content_ref → procurement_inquiry` | 只带来浏览、不形成采购对话即 Stop。 |
| `S-C3` | B2C：一个获准内容发现渠道 + 一个非交易询盘/转化路径 | 已验证产品、价格、支付、配送半径、售后与消费者合规路径 | `qualified_household_inquiry`、有效订单/履约 | 无法稳定履约、温控/投诉异常或无法归因时暂停。 |
| `S-C4` | 第二渠道 | 前一渠道已有 Keep 或明确的覆盖缺口 | 增量合格询盘/采购对话 | 不同时启动两个候选平台。 |

## 5. 阶段总览

| 阶段 | 唯一主要结果 | 当前状态 | 解锁 |
|---|---|---|---|
| SF-0 | 双路线隔离与 B2B-first 决策已记录 | `COMPLETE_PLANNING` | SF-1 |
| SF-1 | 一个有食品/冷链证据的可售 SKU/Offer | `CURRENT` | SF-2 |
| SF-2 | 一个 B2B 人工采购与交接闭环 | `BLOCKED` | SF-3 / SF-5 |
| SF-3 | 一个 B2B 获客/信任渠道的 Keep / Improve / Stop | `DEFER` | SF-4 |
| SF-4 | 规格/场景内容到采购询盘的学习循环 | `DEFER` | SF-6 / SF-7 |
| SF-5 | B2B 跟进、样品/报价和失单原因不遗漏 | `DEFER` | SF-6 / SF-8 |
| SF-6 | 满足条件后，一个 B2C 最小履约闭环 | `DEFER` | SF-7 |
| SF-7 | 第二渠道或第二客群的可归因增量 | `DEFER` | SF-9 |
| SF-8 | AI 解决经测量的重复工作 | `DEFER` | SF-9 |
| SF-9 | 可规模化且质量稳定的销售/履约模型 | `DEFER` | 扩张决策 |

## 6. SF 阶段行动卡

### SF-0｜Route Reset

- **Goal：** 分清海鲜 B2B 与 B2C，不让内容、客户、价格、食品事实或履约假设混入汾酒。
- **Actions：** 使用独立 `business_line`、`product_ref`、客户类型、渠道与指标；按第 3 节采用 B2B-first。
- **NOT NOW：** 不同时跑 B2B/B2C，不建立消费者名单，不把旧市场研究写成可售库存。
- **Unlock：** SF-1。

### SF-1｜Seafood Offer & Cold-Chain Ready（当前）

- **Goal / Main result：** 为一个候选 SKU 建立从标签到收货异常的可审计 Offer；不是仅把货品单转成菜单。
- **Actions：**
  1. 从 `SM-01` 至 `SM-20` 选择一个 SKU 作 `first_offer_candidate`，不按货品单重量自行排序。
  2. 供应链补齐第 2.3 节证据；检查来源、日期、owner、有效期与文件版本。
  3. 写出禁止表达、B2B 资格问题、收货验收字段和异常/停售流程。
- **Daily / Weekly：** 每日追缺件；每周检查批次、标签、温控和价格/库存是否发生冲突/过期。
- **Target / Channel / Content：** 不选客户、不发内容；只生成内部、无品牌/产地/价格/可配送声称的 AI 视频草稿。
- **Data / Initial target：** 一个 SKU 的 `READY` 完整证据包；`STOP_LINE=任一食品/冷链/价格/履约关键字段未知`。
- **Owner / AI：** 供应链提供事实；用户决定商业路线；AI 仅作资料结构化、镜头规划与无标签预演。
- **NOT NOW / Fallback：** 不报价、送样、接单、配送、发布、爬取客户；持续缺件则保持内部资料收集。

### SF-2｜First B2B Manual Procurement Loop

- **Goal：** 用一个 SKU、一个合规企业类型、一个人工 owner 验证“采购需求 → 规格/事实确认 → 报价前复核 → 收货/履约交接”能否完整记录。
- **Entry：** SF-1 对该 SKU 的食品、冷链、商业、履约与外部行动授权全部 READY。
- **Target customer：** 酒店采购/Hotel F&B、海鲜餐厅、中餐厅、火锅、冻品批发、食品进口或 Foodservice；全为候选，必须逐家核验。
- **Actions：** 只以一个来源/转介/入口联系；人工询问菜单、规格、收货窗口、冷冻储存、MOQ、验收和下一步；报价/样品/订单必须重新核验真实事实。
- **Data：** `company_ref`、`product_ref`、`procurement_need`、`freezer_signal`、`receiving_window`、`stage`、`owner`、`next_action_at`、`outcome_ref`。
- **Initial target：** `MINIMUM_TEST_SAMPLE=5` 个已批准的采购对话或一个观察窗口；以信息完整度和合格对话为第一判断。
- **Stop / NOT NOW：** 任一冷链/食品/付款/履约事实失效即停止；不批量外联、不猜联系人、不用消耗端播放量代替采购意愿。
- **Unlock：** 有可回顾的数据后进 SF-3 / SF-5。

### SF-3｜B2B Channel Validation

- **Goal：** 验证一个 B2B 获客/信任渠道是否产生合格采购对话。
- **Actions：** 一次仅试一个来源或内容/转介路径；保持同一 SKU、客户类型和人工 owner；记录从渠道到采购对话的归因。
- **Data / target：** `MINIMUM_TEST_SAMPLE=10` 次可审计触点或预设观察窗口；主指标为 `qualified_procurement_conversation_rate`，不是公司/页面数。
- **Stop / NOT NOW：** 无合格对话、不符合来源/处理依据或无法归因就停止；不加第二渠道、不启动 B2C。
- **Unlock：** Keep/Improve/Stop 结论后进入 SF-4。

### SF-4｜B2B Product-to-Inquiry Learning

- **Goal：** 找出规格、包装、菜单/场景教育与 CTA 中真正推动采购询盘的单一变量。
- **Actions：** 在被批准的 SKU 上测试规格问题、收货场景、菜品适配或验收清单；所有产品语句回链 `fact_ref`。
- **Data：** `content_ref`、target segment、hook、proof status、procurement inquiry、qualified conversation、lost reason。
- **Stop / NOT NOW：** 没有下游数据、事实过期或只产生播放即停止；不批量生成广告素材。
- **Unlock：** 获得可复用 B2B 内容假设后，才考虑 SF-6/7/8。

### SF-5｜B2B Follow-up / CRM Stabilization

- **Goal：** 让每一位已获准联系的企业有明确 owner、样品/报价前置条件和下一步。
- **Entry：** 真实人工跟进已证明有漏项/老化问题，且数据处理依据存在。
- **Actions / Data：** `new → qualified → fact_recheck → sample_or_offer_pending → decision → won/lost/DNC`；记录跟进完成率、样品/报价状态与失单原因。
- **Stop / NOT NOW：** 无真实负担时不接复杂 CRM 或 AI；DNC/删除立即止处理。
- **Unlock：** 先稳定人工流程，再评估 SF-8。

### SF-6｜B2C Controlled Loop（Secondary Route）

- **Goal：** 仅在已有可履约 SKU 后，验证一个消费者场景能否从内容/询盘进入安全交接。
- **Entry：** 已验证单品零售包装、标签、价格、库存、支付、配送半径、温控、售后、消费者资料处理与外部授权。
- **Target customer：** Kathmandu Valley 城市家庭、高收入家庭、家庭聚餐、火锅/中餐爱好者和国际餐饮消费者均为 `HYPOTHESIS`，须按实际订单复核。
- **Actions：** 一个频道、一个 CTA、一个入口、一个产品/套餐；人工处理询盘和交接。
- **Data / Stop：** `qualified_household_inquiry`、有效订单、准时/合格交接、投诉/退款/温控异常；任一质量异常暂停。
- **NOT NOW：** 不与 B2B 同时大规模推进、不用假产品视频吸引下单。

### SF-7｜Second Channel / Segment Expansion

- **Goal：** 只有已验证的首渠道有覆盖缺口或被 Stop 时，测试一个增量渠道/客群。
- **Actions：** 保持 Offer、价格、履约和 owner 不变，只改变渠道或客群；单独记录增量。
- **Stop：** 无增量、冷链负载不稳或归因不全，回到原渠道/人工。

### SF-8｜AI Assistance

- **Goal：** 减少已量化的重复劳动，例如无标签视觉草稿、字幕初稿、内容数据汇总或跟进提醒。
- **Decision metric：** 人工制作分钟数、人工修改率、事实/QC 通过率、漏跟进、有效采购对话率。无净收益则不用。
- **NOT NOW：** 不让 AI 判断食品合规、温度、批次、价格、库存、客户资格；不自动回复/报价/下单。

### SF-9｜Scale

- **Goal：** 在货物事实、冷链、客户结果与人工基线稳定后，受控增加 SKU、客户类型或配送区域。
- **Entry / Stop：** 每个新增 SKU/区域重新过 SF-1；温控、食品、投诉、拒付、损耗、回款或合规事件任一失稳立即缩回。

## 7. 采购沟通、跟进与失单 SOP

`New inquiry → qualification → product/cold-chain fact check → need / sample / offer path → follow-up due → supplier handoff → won / lost / DNC`

| 状态 | Owner | 动作 | Deadline | Exit condition |
|---|---|---|---|---|
| `new_inquiry` | 人工销售 | 标记 B2B/B2C、产品候选、渠道和回联许可 | 同一工作日内的目标，由用户后续设定 | 有场景/企业识别。 |
| `qualification` | 人工销售 | 询问菜单/用途、所需规格、数量级、区域、冷冻储存、收货窗口和决策路径 | 下一工作日 | 需求明确或 `not_qualified`。 |
| `fact_recheck` | 销售 + 供应链 | 核验标签、批次、价格、库存、温控、配送/付款规则 | 报价/样品/订单前 | READY 或 `hold_missing_business_gate`。 |
| `follow_up_due` | 指定 owner | 仅按已同意的下一步复联，记录结果 | 约定日期 | 决策、DNC、lost 或 handoff。 |
| `supplier_handoff` | 供应链 owner | 确认库存、温控、配送、付款、验收和异常路径 | 不确定则停止 | 书面确认或回到 hold。 |

**Seafood B2B 资格问题：** 您是酒店/餐厅/批发/零售哪类企业？需要哪一个经批准的产品/规格？菜单或销售场景是什么？冷冻储存与收货窗口如何安排？预计数量级、MOQ 和验收标准？谁负责采购下一步？

**Seafood B2C 资格问题（SF-6 后才可用）：** 想做哪类餐食？所在允许配送区域？需要了解包装/过敏原/储存还是在批准后询价？何时需要？如出现食品安全/过敏原问题，立即转人工与供应链。

**Lost reason：** `product_or_spec_mismatch`、`price_not_available`、`MOQ`、`no_stock_or_unconfirmed`、`cold_chain_or_delivery`、`food_or_compliance`、`timing`、`no_reply`、`trust_or_label_gap`、`payment_or_settlement`、`competitor`、`decision_delay`、`unknown`。

## 8. Daily / Weekly Rhythm 与归因合同

| 节奏 | 只做什么 | 不做什么 |
|---|---|---|
| 每日（SF-1） | 检查供应链缺件、批次/标签/价格/库存/温控的更新和冲突 | 不发布、不报价、不送样/配送。 |
| 每日（SF-2 以后） | 检查到期跟进、事实状态、收货/异常、内容/询盘来源 | 不自动答复、自动报价或自动改库存。 |
| 每周 | SKU/事实复核、采购/内容/冷链/失单复盘、确定单一实验变量 | 不同时测试 B2B/B2C、多 SKU、多渠道。 |

最小归因链：`business_line → product_ref → content_or_channel_ref → inquiry_ref → company_or_customer_ref → conversation_ref → offer_ref → handoff_ref → outcome_ref`。缺链统一标 `attribution_incomplete`；货品单重量、视频播放或企业数量都不能替代销售结果。
