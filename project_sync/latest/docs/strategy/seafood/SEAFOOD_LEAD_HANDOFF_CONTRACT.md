# Seafood Lead Handoff Contract｜海鲜商机交接与结果反馈合同

> **业务线：** `seafood_nepal`
> **方向：** 用户 Qualified Lead → 供应链当地销售；供应链 outcome feedback → 用户获客优化。
> **数据边界：** 本文件只定义 schema 与状态，不保存真实客户、联系人、消息、价格、订单、付款或私人信息。

## 1. 为什么必须有这个合同

用户的责任不是在尼泊尔完成报价、样品、谈判、收款或配送，而是稳定产生供应链愿意接收的 Qualified Lead。供应链如果收到了 Lead 却不回传 `accepted / offered / won / lost / fulfilled`，用户无法判断流量质量，所有渠道结论都必须标：

```text
attribution_incomplete
```

## 2. 状态定义

### Lead

来自已批准 Route、有来源和业务线，但尚未完成资格判断的潜在企业商机。企业被发现不自动等于 Lead；只有存在产品/需求相关的明确业务信号或主动询盘，才进入 `LEAD`。

### Qualified Lead

B2B 至少具有：

```text
company_name
company_type
city
source
product_interest
need
estimated_volume_range     # only if voluntarily provided
timing
contact_route
decision_role              # if known
next_action
consent_or_contact_basis
```

同时满足：业务线准确、来源允许、公司身份已核验、DNC/删除无命中、产品属于一个有效 Online Offer Pack、需求不超出供应链声明的接受范围。评分只用于人工排序，不替代这些条件。

### Supplier Accepted Lead

供应链已经按 `lead_id` 明确返回 `ACCEPT`，指定 `supplier_owner` 和 `next_action`。仅发送给供应链、已读、口头说“看看”都不算 Accepted。

## 3. End-to-End State Machine

```text
DISCOVERED
→ ENGAGED
→ LEAD
→ QUALIFIED_LEAD
→ SUPPLIER_HANDOFF
→ SUPPLIER_ACCEPTED | NEED_MORE_INFO | REJECT | DUPLICATE | OUT_OF_SCOPE
→ SUPPLIER_FOLLOW_UP
→ OFFERED
→ WON | LOST
→ FULFILLED | FULFILMENT_EXCEPTION

任意阶段 → SUPPRESSED_DNC | DELETE_REQUESTED | HOLD_MISSING_EVIDENCE
```

只允许供应链把 `SUPPLIER_HANDOFF` 推进到 supplier-owned 状态；用户不能替供应链伪造 `ACCEPTED / OFFERED / WON / FULFILLED`。

## 4. Handoff Schema｜用户 → 供应链

| Field | Required | Owner | 规则 |
|---|---:|---|---|
| `lead_id` | yes | 用户 acquisition record | 稳定 opaque ID；不含企业名/邮箱。 |
| `business_line` | yes | 系统 | 固定 `seafood_nepal`。 |
| `product_ref` | yes | 用户 + Online Offer Pack | 必须处于可接受询盘状态。 |
| `source_channel` | yes | 用户 | Search/Web、Referral、Content 等。 |
| `source_evidence_ref` | yes | 用户 | 来源/官网/内容的受控引用，不复制全文。 |
| `customer_type` | yes | 用户 | 与 SF-U2 ICP 一致。 |
| `company_ref` | yes | 用户 | 私有受控记录引用；Git 中只放 placeholder。 |
| `need_summary` | yes | 用户 | 最小业务摘要；不放原始消息。 |
| `location` | yes | 用户 | 城市/服务区域，不存不必要的精确个人地址。 |
| `volume_range` | conditional | 客户自愿提供 | 范围或 `UNKNOWN`，不得估算。 |
| `timeline` | yes | 用户 | 客户表述或 `UNKNOWN`。 |
| `contact_path_ref` | yes | 用户 | 私有业务联系路径引用；Git/普通日志无真实值。 |
| `qualification_result` | yes | 用户 reviewer | `QUALIFIED / HOLD / REJECT` + reason codes。 |
| `consent_or_contact_basis_ref` | yes | 人工/合规 | 缺失则不得 handoff/contact。 |
| `handoff_time` | yes | 系统 | UTC 时间。 |
| `supplier_owner` | yes | 供应链 | 明确当地接收人/队列的受控引用。 |
| `supplier_accept_status` | yes after ack | 供应链 | 五个允许状态之一。 |
| `next_action` | yes after ack | 供应链 | action code + due date；不写敏感自由文本。 |

### Schema example（synthetic / value-free）

```yaml
lead_id: "SEA-LEAD-EXAMPLE-001"
business_line: "seafood_nepal"
product_ref: "SM-03"
source_channel: "search_web_prospecting"
source_evidence_ref: "src_ref_example"
customer_type: "chinese_hotpot_restaurant"
company_ref: "company_ref_example"
need_summary: "synthetic_need_code"
location: "Kathmandu Valley"
volume_range: "UNKNOWN"
timeline: "UNKNOWN"
contact_path_ref: "private_contact_path_ref"
qualification_result: "QUALIFIED"
qualification_reason_codes: ["ICP_MATCH", "PRODUCT_INTEREST_PRESENT"]
consent_or_contact_basis_ref: "basis_ref_required"
handoff_time: "YYYY-MM-DDTHH:MM:SSZ"
supplier_owner: "supplier_owner_ref"
supplier_accept_status: "PENDING"
next_action: "ACK_REQUIRED"
```

本例不授权真实 contact、CRM、发送或 supplier action；字段值都是 placeholder。

## 5. Supplier Accept Contract

供应链必须返回且只能返回：

| Status | 含义 | 必填补充 | 用户下一步 |
|---|---|---|---|
| `ACCEPT` | 在当前产品/区域/能力范围内接收 | supplier owner、next action、due date | 标 `SUPPLIER_ACCEPTED`，等待结果。 |
| `NEED_MORE_INFO` | 仍可能接收，但缺最小信息 | need reason code、缺项 | 只补必要信息；不重复建 Lead。 |
| `REJECT` | 不接受该商机 | reject reason code | 记录 lost/quality signal。 |
| `DUPLICATE` | 已有相同公司/需求 | existing lead ref | 合并归因，不重复联系。 |
| `OUT_OF_SCOPE` | 产品、客户、区域或时间不在范围 | scope reason | 回 SF-U1/U2 修 Offer/ICP。 |

`RECOMMENDED_INITIAL_ACK_TARGET = 1 business day`。它是流程假设，不是现有供应链 SLA；首轮真实数据后重设。超过目标仍无状态：`supplier_ack_overdue`，用户不继续扩量。

## 6. Supplier Feedback Contract｜供应链 → 用户

| Field | Required | 说明 |
|---|---:|---|
| `lead_id` | yes | 精确回链原 Lead。 |
| `supplier_accept_status` | yes | Accept 决策。 |
| `contacted_status` | yes | `NOT_STARTED / ATTEMPTED / CONTACTED / UNREACHABLE`。 |
| `supplier_qualified_status` | yes | 当地销售判断，不覆盖用户原 qualification。 |
| `offer_status` | yes | `NOT_READY / CREATED / SENT / DECLINED`；无真实价格进入 Git。 |
| `sales_outcome` | yes | `OPEN / WON / LOST`。 |
| `lost_reason` | required if lost | 稳定 reason code。 |
| `fulfilment_status` | required if won | `PENDING / FULFILLED / EXCEPTION / CANCELLED`。 |
| `feedback_date` | yes | 结果更新日期。 |
| `next_feedback_due` | required while open | 下次反馈日期。 |

### Lost reason allowlist

`product_or_spec_mismatch`、`price`、`MOQ`、`no_stock`、`cold_chain_or_delivery`、`food_or_compliance`、`timing`、`no_reply`、`trust_or_label_gap`、`payment_or_settlement`、`competitor`、`decision_delay`、`out_of_scope`、`unknown`。

### Feedback timing hypotheses

- ACK：1 business day。
- Open Lead 更新：每 5 business days 或 next action 发生时，以先到者为准。
- Won/Lost：决定后 2 business days 内回传。
- Fulfilment：完成/异常后 2 business days 内回传。

以上均为 `RECOMMENDED_INITIAL_TEST_THRESHOLD`；供应链未书面接受前不是 SLA。

## 7. Attribution Contract

```text
source_channel / content_id / campaign_id
→ lead_id
→ qualification_result
→ supplier_accept_status
→ offer_status
→ sales_outcome
→ fulfilment_status
```

必须能计算：`supplier_accept_rate`、`lead_to_supplier_conversation_rate`、`lead_to_offer_rate`、`lead_to_order_rate`、`cost_per_supplier_accepted_lead` 和 lost reason。收入只作为受控联合结果引用，不在 Git 保存真实金额。

以下任一情况标 `attribution_incomplete`：supplier 未 ACK、open Lead 无定期反馈、Won/Lost 无 lead_id、内容/Route 无 source ID、或 Fulfilment 结果无法回链。归因不完整时不进入第二 Route、AI 自动化或规模化。

## 8. Privacy / DNC / Git Boundary

- 真实邮箱、电话、WhatsApp、消息正文、个人姓名、付款、报价、订单和地址只可留在未来获批准的私有系统。
- Git、fixture、普通日志、文档示例只保留 opaque ref、hash、status、reason code 和 aggregate count。
- DNC/删除请求优先于 Lead 分数、supplier interest 或历史沟通；命中即 `SUPPRESSED_DNC / DELETE_REQUESTED`。
- 未获联系人处理依据与用户 action-time 授权时，本合同最高只可用于内部 schema 和 synthetic validation，不得创建真实 Handoff。

## 9. Handoff Done / Stop

### Done when

- 每条 Qualified Lead 有完整最小字段；
- 供应链返回五种接收状态之一；
- Accepted Lead 有 owner/next action；
- Offered/Won/Lost/Fulfilled 可回链；
- 用户可用结果判断 Route/ICP/Content。

### Stop line

缺 source、basis、DNC、Offer Pack、supplier owner、ack 或 feedback 任一项即停止对应外部链路；不通过猜联系人、重复发送、由用户代替供应链填写结果来补洞。
