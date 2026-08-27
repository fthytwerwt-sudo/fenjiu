# 下一步行动｜NEXT_ACTIONS

## 2026-08-28 当前唯一优先任务

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

## 当前顺序

1. **供应链补齐商品单和价格（P0）**：取得 SKU、规格、商品素材、价格、最低价、价格有效期、库存、有效期和补货周期，并标明资料日期与负责人。
2. **确认首批可售 SKU（P0）**：仅在商品、价格、库存、主体/资质和履约输入齐备后，确定首批可上架 SKU；没有证据时保持 UNKNOWN。
3. **补齐账号、资质、收款与履约（P0）**：确认账号主体/管理员/认证支持、当地主体与品牌授权、收款、仓储配送、退换货、质量、售后和结算责任。
4. **核验 TikTok 当前平台边界（P0）**：取得酒类内容、广告、账号和转化的当前书面规则，并与当地合规边界交叉核验。
5. **决定最小上线试点（P1）**：仅在 P0 证据齐备且用户明确授权后，定义首批 SKU、年龄/地域限制、内容和订单路径；默认保持人工审核，不自动外发。
6. **上线前再验收（P1）**：公开执行前重新核验合规、权限、库存、价格、收款和履约证据，记录日期、责任人和停止条件。

## 工程下一步（与业务 P0 独立）

1. **P08-01 等待真实资料（工程/业务闸门）**：Phase 5–7 已完成合成工程合同并进入 `main`；P08-01 只能在供应链提供当前、获授权的资料包后开始。最小输入仍为 SKU、规格、品牌素材、价格/有效期、库存/有效期、来源/版本/负责人，以及主体、资质、授权、账号、收款和履约的书面证据。当前状态为 `BLOCKED / real_supplier_data_missing（阻断 / 缺少真实供应链资料）`。
2. **保持外部动作关闭**：在 P08 资料审核、业务闸门和用户明确授权完成前，`external_execution_allowed = false（外部执行允许 = 否）`；不得发布、发送、报价、收款、下单、退款或发货。
3. **远端治理待授权**：GitHub API 的 visibility（可见性）尚未获认证回读，default branch（默认分支）仍为 `chore/project-collaboration-system` 而非 `main`。需具备仓库管理权限的责任人单独核验/决定；不得用本地测试或匿名 Git 读取推断 Private（私有）状态。远端 CI 仍需具备 `workflow` scope 的授权凭据单独写入并回读。
4. **可进入最小企业发现测试，但不得跨越持久化或联系人边界**：`FENJIU_SOURCE_CATALOG.md` 与 `SEAFOOD_SOURCE_CATALOG.md` 已提供单业务线、低频、公司级企业发现来源和 YAML 配置。后续任务只可使用各自 `approved_source_ids`，以 `transient_discovery_only` 方式人工查看并回企业官网交叉验证；不得写入 candidate store 或真实 CRM，不采集联系人、不发信、不报价，也不将目录结果写成供应链或合规事实。

## 每项完成证据

- 有可回读的来源、日期、责任人和书面确认；
- 同步更新 BUSINESS_STATUS、OPEN_QUESTIONS、RISKS_AND_BLOCKERS 与必要的 DECISIONS；
- 若影响协作或交接，更新 COLLABORATION_STATUS、EXECUTION_HISTORY 并生成/验证同步包；
- 不以计划、模板、Git 提交或文档生成代替供应链、平台或合规确认。
