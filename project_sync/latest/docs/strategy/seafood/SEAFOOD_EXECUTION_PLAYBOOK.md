# Nepal Seafood Execution Playbook｜尼泊尔海鲜双工作流销售执行手册

> **业务线：** `seafood_nepal`
> **文档状态：** `INTERNAL_EXECUTION_DESIGN / external_acquisition_requires_route_specific_authorization`
> **供应链当前阶段：** `SF-S1 Supplier Product & Fulfilment Readiness = IN_PROGRESS_REPORTED / NOT_READY`
> **用户当前阶段：** `SF-U1 Online Offer Pack Ready = CURRENT / BLOCKED_BY_SUPPLIER_INPUTS`
> **职责北极星：** 用户负责线上流量与合格商机；供应链负责尼泊尔当地销售、成交与履约。

## 1. 30 秒行动结论

旧 `SF-2 First B2B Manual Procurement Loop` 将用户线上获客与供应链当地采购、样品、报价、成交及履约混在一起，和 2026-08-29 用户 P0 冲突，现标为：

```text
SUPERSEDED_BY_SF_SUPPLIER_AND_USER_WORKSTREAMS
```

今天用户不去推进当地采购、样品或成交；只做 `SF-U1`：检查供应链新资料，把 **1 个**候选 SKU 转成可用于线上获客的 `Online Offer Pack`。供应链可并行推进 `SF-S1`，但任何“正在做”的事项在当前书面证据齐备前仍是 `UNKNOWN / BLOCKED`。

详细日常执行见 [SEAFOOD_ONLINE_ACQUISITION_PLAYBOOK.md](SEAFOOD_ONLINE_ACQUISITION_PLAYBOOK.md)，商机交接与结果反馈见 [SEAFOOD_LEAD_HANDOFF_CONTRACT.md](SEAFOOD_LEAD_HANDOFF_CONTRACT.md)。

## 2. 职责边界：两个 Workstream，不是一个混合 SF-2

```text
Supplier Workstream
Product / food / import / price / stock / cold chain / local sales / fulfilment
                             ↓ Online Offer Pack + local owner
User Online Acquisition Workstream
Traffic / company discovery / content / search / qualification / handoff
                             ↓ Qualified Lead
Lead Handoff Contract
                             ↑ accepted / offered / won / lost / fulfilled
```

| 角色 | 主责 | 不负责 | 成功证据 |
|---|---|---|---|
| 用户 | 线上流量、企业发现、内容/搜索/网站/目录获客、合规的主动企业获客设计、Lead、Qualified Lead、Supplier Handoff、渠道/内容/ICP 优化 | 当地拜访、冷库、现场样品、当地报价/谈判、收款、订单、配送、售后、当地客户维护 | `qualified_lead → supplier_accepted` 与可回链的供应链结果反馈。 |
| 供应链 | 商品/SKU、食品/进口、当地合法销售、价格、库存、冷链、仓储、当地报价、样品、谈判、收款、订单、配送、售后与成交 | 代替用户持续运营线上获客系统 | Offer/库存/合规/履约证据；Lead 接收、跟进、Offer、Won/Lost/Fulfilled 回传。 |
| AI / Codex | 内部研究、分类、内容/视频 brief、Lead 摘要、提醒、成本/漏斗分析、规则与 Git 验证 | 认可业务事实、合法性判断、真实抓取/发送/发布、报价、谈判、付款或履约 | 人工接受率、事实错误率、节省时间与可审计输出。 |

## 3. Supplier Workstream｜SF-S1 Product & Fulfilment Readiness

### Goal

为至少一个 SKU 提供用户线上获客所需的事实包，并拥有尼泊尔当地 Lead 接收、报价、成交与履约 owner。

### Supplier flow

```text
product identity → specification / label / batch / food information
→ import / food compliance → price / MOQ / stock
→ cold chain / warehouse / payment → local quote / sample / negotiation
→ order / delivery / after-sales → outcome feedback
```

### Current status

- `CONFIRMED（P0）`：供应链正在推进当地商品和业务准备。
- `UNKNOWN / BLOCKED`：没有当前逐项书面证据证明任一 SKU、价格、库存、食品/进口、冷链、样品、报价、付款、配送或售后已 `READY`。
- `NOT USER ACTION`：用户不承担 SF-S1 的当地执行，只负责检查供应链交付是否足够支持线上获客。

### Minimum Online Offer Pack input

| 字段 | 用途 | Ready 判定 |
|---|---|---|
| `product_ref / product_name / category` | 唯一产品身份 | 与当前供应链资料一致。 |
| `specification / packaging` | 让 ICP 和内容不猜规格 | 有标签/规格书证据。 |
| `target_customer_hint` | 供应链说明能接受的客户类型 | 只是筛选输入，不自动成为市场事实。 |
| `approved_product_images / asset_usage_rights` | 内容、Landing、询盘使用 | 素材版本和权利明确。 |
| `B2B/B2C availability_status` | 判断可接何种 Lead | `ACCEPTING_INQUIRY / HOLD / NOT_AVAILABLE`。 |
| `price_handling_rule` | 决定公开/询价路径 | 可用 `price_display=NO`、`price_route=SUPPLIER_CONFIRMATION`。 |
| `MOQ / stock_status / service_area` | 资格筛选和交接 | 不要求公开数值，但必须能判断是否接受询盘。 |
| `supplier_contact_owner` | Lead 交接 | 有明确 owner 与接收状态。 |
| `claims_allowed / claims_prohibited / fact_validity` | 内容与回复事实锁 | 来源、批准人、日期、有效期完整。 |

`ONLINE_ACQUISITION_READY` 只表示足够支持受控获客，不表示整个供应链已完成或可公开销售。

## 4. User Online Acquisition Workstream｜SF-U0–SF-U8

| Stage | 唯一主要结果 | 当前状态 | 用户主动作 | Next unlock |
|---|---|---|---|---|
| SF-U0 | 角色、交接与反馈边界清楚 | `COMPLETE_PLANNING` | 只维护职责与接口，不做外部动作 | SF-U1 |
| SF-U1 | 1 个 `ONLINE_ACQUISITION_READY` Offer Pack | `CURRENT / BLOCKED_BY_SUPPLIER_INPUTS` | 检查新资料、更新 pack、列缺口、准备内部素材 | SF-U2 |
| SF-U2 | 1 Product + 1 ICP + 1 Region + 1 Route | `PLANNING_READY / INPUT_DEPENDENT` | 锁定 First ICP、Primary/Fallback Route 和测试样本 | SF-U3 |
| SF-U3 | 第一 Route 是否产生可判定基线/Qualified Lead | `INTERNAL_BASELINE_ALLOWED / EXTERNAL_TEST_BLOCKED` | 单 Route、单 CTA、单窗口测试并记录成本；未授权只做内部 baseline | 未授权停留 waiting_authorization；已授权且有 Qualified Lead 才进入 SF-U4 |
| SF-U4 | Qualified Lead 可低摩擦交给供应链 | `DEFER` | 资格判断、Handoff、确认 Supplier Accept | SF-U5 |
| SF-U5 | 知道何种 ICP/Route/Content 产生销售价值 | `DEFER` | 连接 Lead 到 accepted/offered/won/lost/fulfilled | SF-U6 / SF-U7 |
| SF-U6 | 第二 Route 的增量结论 | `DEFER` | 只增加一个新路线并单独归因 | SF-U7 / SF-U8 |
| SF-U7 | AI 对一个人工瓶颈有净收益 | `DEFER` | before/after 比较、人工批准 | SF-U8 |
| SF-U8 | 稳定获客、交接与反馈可自动化扩张 | `DEFER` | 自动化一个低风险步骤并保留回退 | 规模化决策 |

完整 Entry、指标、阈值、Stop、NOT NOW 与 Done 见线上获客主手册。旧 SF-0–SF-9 只作为 2026-08-28 历史规划保留在 Git history，不再作为当前用户路线。

## 5. 新海鲜销售漏斗与责任切点

```text
DISCOVERED → ENGAGED → LEAD → QUALIFIED_LEAD
→ SUPPLIER_HANDOFF → SUPPLIER_ACCEPTED → SUPPLIER_FOLLOW_UP
→ OFFERED → WON / LOST → FULFILLED
```

| 状态段 | 主责 | 规则 |
|---|---|---|
| `DISCOVERED → QUALIFIED_LEAD` | 用户 | 来源、ICP、需求、地区、产品兴趣、联系依据和下一步可核验。 |
| `QUALIFIED_LEAD → SUPPLIER_HANDOFF` | 用户 | 按最小字段交接，不在 Git 保存真实私人联系方式。 |
| `SUPPLIER_ACCEPTED → FULFILLED` | 供应链 | 当地联系、报价、样品、谈判、订单、付款、配送和售后。 |
| `accepted/offered/won/lost/fulfilled feedback` | 供应链回用户 | 没有结果回传则 `attribution_incomplete`，用户不扩大 Route。 |

收入、订单与履约是双方联合结果，不是用户个人执行责任；用户仍需用最终结果优化 ICP、Route、内容和 Lead Quality。

## 6. First ICP / Product / Route 决策

### Recommended first product candidate

`SM-03 41/50 单冻虾仁（货品单记录 5 kg/件）`，状态为 `RECOMMENDED_FIRST_PRODUCT_CANDIDATE / NOT_READY`。原因是产品形态/规格/箱规比部分候选更容易先形成餐饮用 Online Offer Pack；其物种、净重、标签、批次、过敏原、价格、库存、冷链与可售状态仍必须由供应链确认。

### Recommended first ICP

`Kathmandu Valley Chinese / Hotpot Restaurants`，状态为 `HYPOTHESIS / RECOMMENDED_FIRST_ICP`。

- **Why first：** 多个虾/鱼/贝/小龙虾候选与中餐/火锅菜单用途方向直接；餐饮类可由当前唯一批准的 OSM 低频 discovery 路线发现，并回企业官网验证；相对酒店/进口商更容易先验证菜单、公司身份和公开业务入口。
- **Why not others yet：** 酒店销售周期/采购层级复杂；进口商没有批准直接来源；冻品批发需先证明冷库/分销与食品责任；超市需要零售包装、标签和陈列/配送事实。
- **Change evidence：** 供应链只接受其他客户类型、SM-03 无法 READY、20 个观察中少于 8 个符合 ICP，或另一 ICP 的 supplier-accepted lead rate 明显更高。

### Recommended first acquisition route

- `Primary = Search / Web Prospecting`：低频 `SEA-OSM-POI-NP` 发现 → 企业自有官网验证 → ICP qualification → 识别候选业务联系路径。任何联系/发送须另获处理依据、DNC 与用户授权。
- `Fallback = Digital Referral / Partner`：供应链、协会或行业伙伴提供获许可的企业推荐，用户按同一 intake/handoff 合同记录；不复制会员/个人联系人。
- `Later = Organic B2B Content`：Offer、素材权、一个平台、CTA、Lead intake 和归因准备后，在 SF-U6 作为第二 Route。
- `DEFER = Paid Ads / bulk Email / automated crawler`：无 baseline、Landing、授权和反馈闭环时不进入。

## 7. 产品候选登记（来源记录，不是库存）

用户提供的 5 页《尼泊尔市场冻品 2026 年第一批次进货清单》记录 20 个产品行、数量 554、总重量 2,895 kg、外箱总立方 11.2323145。它不证明货物已发运、到港、通关、仍在库、合规、可配送或可承诺。

| Ref | 货品单产品 | 表内数量 | 表内重量 kg | 表内规格/包装摘记 | 当前状态 |
|---|---|---:|---:|---|---|
| SM-01 | 500/700 带鱼 | 10 | 95 | 17 条/件，含箱 10 kg | `CANDIDATE / BLOCKED` |
| SM-02 | 2125 真空虾仁 | 10 | 48 | 600 g/板，8 板/件 | `CANDIDATE / BLOCKED` |
| SM-03 | 41/50 单冻虾仁 | 20 | 100 | 290 只/件，5 kg/件 | `RECOMMENDED_CANDIDATE / NOT_READY` |
| SM-04 | 50-100 手冰耗儿鱼 | 10 | 44 | 4.4 kg/件 | `CANDIDATE / BLOCKED` |
| SM-05 | 小河虾 | 2 | 5 | 10 袋/件，2.5 kg/件 | `CANDIDATE / BLOCKED` |
| SM-06 | 700/800 多宝鱼 | 10 | 100 | 12 条/件，10 kg/件 | `CANDIDATE / BLOCKED` |
| SM-07 | 青口贝 | 80 | 320 | 4 kg/件 | `CANDIDATE / BLOCKED` |
| SM-08 | 50-60 盐冻虾 | 20 | 168 | 6 盒/件，9 kg/件 | `CANDIDATE / BLOCKED` |
| SM-09 | 12 头黑虎虾 | 20 | 80 | 10 盒/件，4 kg/件 | `CANDIDATE / BLOCKED` |
| SM-10 | 单冻干冰青虾 | 20 | 100 | 140 条/件，5 kg/件 | `CANDIDATE / BLOCKED` |
| SM-11 | 14 条黄花鱼 | 10 | 100 | 14 条/件，含箱 10 kg | `CANDIDATE / BLOCKED` |
| SM-12 | 花甲 | 150 | 600 | 10 袋/件，4 kg/件 | `CANDIDATE / BLOCKED` |
| SM-13 | 72 生蚝 | 50 | 350 | 72 只/件，7 kg/件 | `CANDIDATE / BLOCKED` |
| SM-14 | 8 头辽参 | 10 | 0 | 8 只/袋；重量为表内 0 | `CONFLICT_OR_MISSING_WEIGHT` |
| SM-15 | 大 A 鲍鱼 | 2 | 0 | 8 袋/件；重量为表内 0 | `CONFLICT_OR_MISSING_WEIGHT` |
| SM-16 | 小龙虾 | 100 | 750 | 10 盒/件 | `CANDIDATE / BLOCKED` |
| SM-17 | 1620 白灼虾 | 10 | 35 | 10 盒/件 | `CANDIDATE / BLOCKED` |
| SM-18 | 800/900 大白鲷 | 10 | 120 | 12 包/件 | `CANDIDATE / BLOCKED` |
| SM-19 | 蛏子肉 | 5 | 25 | 5 kg/件 | `CANDIDATE / BLOCKED` |
| SM-20 | 大板鱿鱼须 | 5 | 17.5 | 3.5 kg/件 | `CANDIDATE / BLOCKED` |

## 8. Responsibility Matrix｜责任矩阵

| 动作 | 用户 | 供应链 | AI / Codex |
|---|---|---|---|
| 商品资料 / 图片素材 | 检查是否够线上获客使用 | 提供并确认事实/权利 | 结构化、缺口检查 |
| 目标客户 / ICP | 推荐、测试、优化 | 说明可承接客户边界 | 证据整理、评分建议 |
| 企业发现 / 搜索 / 目录 | 主责，按批准 Route | 可提供 referral | 内部辅助；不真实抓取联系人 |
| 内容 / 视频 | 选择 Route、目标与发布决定 | 确认产品事实/素材 | brief、脚本、AI 手机质感、QC 建议 |
| 广告 | 后置设计与归因 | 确认可售/履约容量 | 分析；不实际投放 |
| Lead / Qualification | 主责 | 提供接受范围 | 摘要/评分建议，不代替人工 |
| Supplier Handoff | 提交合格 Lead、确认接收 | ACCEPT/REJECT/NEED_INFO | 合同/提醒/审计 |
| 报价 / 样品 / 谈判 | 不负责当地执行 | 主责 | 不生成真实承诺 |
| 订单 / 付款 / 配送 / 售后 | 不负责当地执行 | 主责 | 仅汇总受控结果码 |
| 销售反馈 | 请求并用于优化 | 必须按 lead_id 回传 | 归因和 lost reason 分析 |
| 数据分析 | 主责获客/成本优化 | 提供结果状态 | 聚合、建议、异常提示 |

## 9. 当前 Daily / Weekly Mode

### User today｜SF-U1

```text
检查供应链新资料
→ 更新 1 个 Online Offer Pack
→ 标记 missing/conflict/expired
→ 准备内部素材与 ICP/Route 假设
```

### Supplier today｜SF-S1

供应链继续商品、食品/进口、价格、库存、冷链、当地销售和履约准备；用户只接收可回读资料和 owner，不代执行。

### Weekly joint review

1. 哪个 ICP 产生的 Qualified Lead 质量最好？
2. 哪个 Route 的 cost per qualified / supplier-accepted lead 最低？
3. 供应链接收、Offer、Won/Lost/Fulfilled 分别多少？
4. 最常见 lost reason 与 `attribution_incomplete` 是什么？
5. 下一周只改变哪一个变量？

## 10. Current Blocks / NOT NOW

- `BLOCKED`：Online Offer Pack、联系人处理依据、DNC/retention、外联/发布/广告授权、Supplier Handoff owner、销售结果反馈机制。
- `NOT NOW`：大型 CRM、LangGraph、全自动 crawler、真实 Gmail sender、猜邮箱、批量发送、TikTok/Meta 发布、广告、企业联系、真实客户私人信息、订单、报价、收款。
- 本轮文件和 Git 成功只表示职责/规划/交接接口完成，不表示供应链 READY、获客已经开始、Lead 已产生或成交成立。
