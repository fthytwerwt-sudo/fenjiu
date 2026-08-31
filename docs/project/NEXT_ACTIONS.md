# 下一步行动｜NEXT_ACTIONS

## 2026-08-29 当前优先任务（双业务线互不替代）

**`SR-1 / Sellable Offer Evidence Contract`**：把一个候选汾酒 Offer 所需的供应链、合规、渠道、收款与履约证据整理为私有、可审计的 decision register；输出已批准/缺失/冲突/过期清单和负责人。不得导入 Git 真实数据、发布、报价、收款、下单或接触客户。

| 字段 | 定义 |
|---|---|
| `primary_route` | 供应链书面资料 → 私有 evidence register → 人工业务/合规审核 → 最小 Offer ready/blocked decision。 |
| `fallback_route` | 资料不完整时仅生成缺口清单、owner 和补件问题；不猜测、不升级。 |
| `capability_status` | `requires_supplier_and_human_evidence`。 |
| `probe_required` | 是：来源、日期、owner、有效期、冲突、业务线和敏感隔离检查。 |
| `allowed_codex_autonomy` | 整理模板、reference/hash、缺口/冲突报告、内部验证与 Git 文档收口。 |
| `forbidden_codex_guessing` | SKU、价格、库存、许可、品牌授权、账号、支付、物流、售后、平台允许或用户授权。 |
| `required_inputs` | 当前供应链书面资料、指定 Offer、资料 owner、当地/平台核验材料、用户定义的审阅人。 |
| `required_outputs` | 私有 evidence register、最小 Offer decision、gap/conflict/expiry 报告、SR-2 进入/阻断判断。 |
| `validation_commands` | 文件/哈希/敏感信息/绝对路径、事实分级、文档引用检查；无外部 action counters。 |
| `blocked_if_missing` | `supplier_fact_missing`、许可/渠道/支付/履约证据缺失、审阅人缺失或资料冲突。 |

之后的顺序：SR-1 达到定义的 `business_ready` 后，由用户决定是否授权 SR-2 的单 Offer、单触点、单承接点人工销售闭环；SR-3/5、SR-6、SR-7 与 SR-8 不允许跳级。`external_execution_allowed=false`、发送、发布、广告、报价、付款、订单、退款、发货和自动联系人采集持续关闭；WhatsApp 不作为酒类交易通道，Meta commerce channels 不作为酒类销售通道。

## SR-1 子任务（唯一当前队列）

1. **供应链 Offer 证据**：取得 SKU、规格、品牌素材/权利、价格/最低价/有效期、库存/补货，并标明来源、日期与 owner。
2. **合法性与履约证据**：核验主体、品牌授权、适用许可/年龄边界、收款、仓储配送、退换货、质量、售后和结算责任。
3. **渠道与承接设计**：只核验候选触点的账号 owner、地区、酒类内容/广告/商品展示/消息边界与一个询盘承接方式；不发布、不投放、不自动发消息。WhatsApp 不得用作酒类交易，Meta commerce channels 不得用作酒类销售。
4. **人工 Offer 决定**：由用户/供应链/必要合规责任人确认 `ready / blocked / missing / conflict / expired`，并记录 SR-2 是否可被用户另行授权。

## Seafood 双 Workstream 当前队列（与汾酒 FJ-1 分开维护）

### Supplier SF-S1

1. 供应链从 `SM-01` 至 `SM-20` 提供至少一个 SKU 的产品身份、物种/形态、规格、净重、包装、标签、批次、保质期、过敏原与素材权。
2. 供应链确认该产品的 B2B/B2C 接受状态、价格处理规则、MOQ/库存状态、服务区域、食品/进口/冷链/仓储、当地报价/样品/成交/付款/配送/售后和 local owner。
3. 所有资料仍逐项 `READY / MISSING / CONFLICT / EXPIRED`；“正在推进”不等于 READY。

### User SF-U1（今天唯一海鲜用户动作）

1. 只检查 `SM-03` 的新增供应链资料，更新 Online Offer Pack；不代供应链执行本地动作。
2. 身份、规格、素材权、询盘接受状态、supplier owner 或有效期缺失时保持 `BLOCKED`。
3. 可内部准备 First ICP（Kathmandu Valley Chinese/Hotpot Restaurants）与 Primary Route（Search/Web Prospecting），但不发现、联系、发送或发布。
4. Product Pack `ONLINE_ACQUISITION_READY` 后才进入 SF-U2；旧 SF-2 人工采购闭环已 `SUPERSEDED`。

## 保持后置或关闭

- `P08-01` 的真实资料导入仍是历史工程任务，不是当前业务队列；只有 SR-1 的业务证据和独立实现设计都满足时才能重新评估。
- 海鲜企业发现、真实 CRM/Gmail、crawler、内容发布、广告、Agent、自动化和规模化均等待 SF-U 阶段、Route-specific 来源/处理/DNC/平台/用户授权和 Supplier Handoff/Feedback 准备；本轮不启动。
- GitHub default branch/visibility/远端 CI 仍由具备管理权限的责任人单独核验；它们不替代业务闸门。
- `external_execution_allowed=false`；不得发布、发送、报价、收款、下单、退款或发货。

## Video Orchestrator 工程后续（不替代当前业务队列）

1. Aidge/OSS 本地环境、credentials 与 OSS 实际小测已完成；不再需要用户填写其他配置。
2. Aidge 继续保持 `AIDGE_PROBE_REQUIRED`；只读查询验证了 credentials/endpoint，未验证 `aidge:VideoGeneration` 精确权限。
3. 仅在用户另行同意最高约人民币 7 元后，再单独运行一次 `./videoctl probe-aidge --execute --approve-cost --max-cost-cny 7`；输出必须经 ffprobe/解码与人审。
4. Wan3/Qwen-MT/MiniMax Turbo 保持 `PROBE_REQUIRED`，不得因 DashScope Key 存在写成已物理验证。

## 每项完成证据

- 有可回读的来源、日期、责任人和书面确认；
- 同步更新 BUSINESS_STATUS、OPEN_QUESTIONS、RISKS_AND_BLOCKERS 与必要的 DECISIONS；
- 若影响协作或交接，更新 COLLABORATION_STATUS、EXECUTION_HISTORY 并生成/验证同步包；
- 不以计划、模板、Git 提交或文档生成代替供应链、平台或合规确认。
