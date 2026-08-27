# Current → Target Gap Analysis｜当前系统到目标系统的差距分析

- **日期**：2026-08-28
- **方法**：审计 `origin/main` 当前文档、代码、测试、fixtures、adapter 与 feature-flag 合同；状态只描述可回读工程能力，不把设计、fake、测试或 Git 结果写成业务完成。

## 1. Current State Matrix

| 模块 | 当前状态 | 已实现什么 | 未实现什么 | 真实联网 | 真实业务数据 | 销售动作 | 当前销售价值 | 建议 |
|---|---|---|---|---|---|---|---|---|
| Truth Center | `IMPLEMENTED_SYNTHETIC` | scoped/versioned truth、fixture 隔离、内存 repository | 真实数据存储、生产身份、真实批准 | 否 | 否 | 否 | 防止错误商品事实进入下游 | `KEEP` |
| Ingestion | `IMPLEMENTED_INTERNAL_ONLY` | synthetic source/mapping/review 合同、内存 pipeline | 私有真实资料接收、parser/OCR、生产存储 | 否 | 否 | 否 | 为真实 Offer 资料入场预留边界 | `KEEP`，待 SR-1 后按任务接入 |
| Workflow | `IMPLEMENTED_INTERNAL_ONLY` | checkpoint、retry、DLQ、manual queue | 生产队列/外部执行 | 否 | 否 | 否 | 仅在人工流程确有重复时复用 | `KEEP` |
| RBAC / Approval | `IMPLEMENTED_SYNTHETIC` | local policy、版本绑定审批、拒绝外部动作 | 真实身份/RBAC/授权源 | 否 | 否 | 否 | 保护未来高风险动作 | `KEEP` |
| Audit | `IMPLEMENTED_INTERNAL_ONLY` | append-only audit、失败补偿、脱敏指标 | 生产审计库/监控 | 否 | 否 | 否 | 可追责底座 | `KEEP` |
| Leads | `IMPLEMENTED_SYNTHETIC` | 来源政策、synthetic candidate、去重/评分合同 | 真实来源/公司资料/contactability | 否 | 否 | 否 | 仅支撑未来 B2B 小样本 | `REFOCUS` |
| CRM | `IMPLEMENTED_SYNTHETIC` | organization/contact/opportunity/DNC/next-action 合同 | 真实 CRM provider、真实客户、实际 owner workflow | 否 | 否 | 否 | 应改为“谁该做下一步” | `REFOCUS` |
| DNC | `IMPLEMENTED_SYNTHETIC` | DNC registry/拒绝外发规则 | 法律依据、保留/删除/真实同步 | 否 | 否 | 否 | 真实外联前必须保留 | `KEEP` |
| Outreach | `IMPLEMENTED_SYNTHETIC` | draft、approval、zero-send proof | sender、inbox、receipt/reply、外发授权 | 否 | 否 | 否 | 非当前主线；只用于后续 B2B | `DEFER` |
| Gmail | `NOT_IMPLEMENTED` | 无真实 adapter；仅有未来设计 | OAuth、outbox、发送/回复对账 | 否 | 否 | 否 | 高价值 B2B 才可能需要 | `DEFER` |
| Customer Service | `IMPLEMENTED_SYNTHETIC` | conversation/draft/handoff、fake inbox | 渠道收件、真实客户会话、发送 | 否 | 否 | 否 | 未来统一询盘承接可复用 | `REFOCUS` |
| Content | `IMPLEMENTED_SYNTHETIC` | brief、fact/policy lock | 真实内容、发布和销售归因 | 否 | 否 | 否 | 用于单渠道 Offer 测试 | `REFOCUS` |
| Video | `FAKE_ONLY` | fake provider、reference-only manifest、内部 QC | media generation、发布、content-to-sale 归因 | 否 | 否 | 否 | 只在加快可验证内容测试时保留 | `REFOCUS` |
| Crawl | `FAKE_ONLY` | zero-network fake CrawlPort 与 strict source policy | 合规 real adapter、真实 company discovery | 否 | 否 | 否 | B2B 发现辅助，不是发动机 | `DEFER` |
| TikTok | `NOT_IMPLEMENTED` | 无平台 adapter/账号事实/发布事实 | 账号、政策、内容、承接、归因核验 | 否 | 否 | 否 | 候选内容发现触点 | `REFOCUS` |
| Instagram | `NOT_IMPLEMENTED` | 无 adapter 或项目能力证据 | 帐号/政策/承接/归因 | 否 | 否 | 否 | 候选内容复用/信任触点 | `DEFER`，待验证 |
| Facebook | `NOT_IMPLEMENTED` | 无 adapter 或项目能力证据 | Page/Groups/Messenger/政策 | 否 | 否 | 否 | 候选本地信任/社群触点 | `DEFER`，待验证 |
| WhatsApp | `NOT_IMPLEMENTED` | 无 Business 接入或会话事实 | 账号、政策、模板、人工响应 | 否 | 否 | 否 | 候选统一询盘承接 | `NEW`，先人工路径验证 |
| Website | `NOT_IMPLEMENTED` | 无生产官网/表单/归因能力 | 可信度页、商品页、FAQ、承接 | 否 | 否 | 否 | 候选信任/转化页面 | `NEW`，仅最小版 |
| Analytics | `NOT_IMPLEMENTED` | audit metrics 非商业归因 | content/channel/inquiry/order attribution | 否 | 否 | 否 | 识别真正带来客户的渠道 | `NEW`，先轻量记录 |
| Order | `NOT_IMPLEMENTED` | 默认禁用 `order_create` | 人工确认、订单记录、供应链接口 | 否 | 否 | 否 | 销售闭环的关键缺口 | `NEW`，受 business gates 约束 |
| Payment | `NOT_IMPLEMENTED` | 默认禁用 `payment` | 合法收款主体、支付路径、对账 | 否 | 否 | 否 | 销售闭环的关键缺口 | `BLOCKED` |
| Fulfillment | `NOT_IMPLEMENTED` | 无仓储/配送/售后系统 | 真实责任、SOP、状态与异常处理 | 否 | 否 | 否 | 销售闭环的关键缺口 | `BLOCKED` |
| Feedback loop | `NOT_IMPLEMENTED` | 无客户/订单回流和归因 | 复购、投诉、内容/Offer 反馈 | 否 | 否 | 否 | 决定是否优化或扩张 | `NEW`，先人工记录 |

代码证据：例如 `modules/truth_center/models.py`、`modules/crm/outreach.py`、`modules/customer_service/drafts.py` 和 `modules/content_video/contracts.py` 强制 `is_synthetic=True` / `external_execution_allowed=False`；`adapters/crawl/fake.py`、`adapters/support/fake.py` 与 `adapters/video/fake.py` 为 zero-network/zero-send fake；`adapters/ai/` 与 `adapters/crm/` 没有实际 provider 实现。

## 2. 当前投入、最接近销售和偏离点

### A. 已投入最多的地方

1. 安全合同、scope/lineage、fixture 隔离、审批、审计和负向测试。
2. synthetic ingestion、workflow、leads/CRM/DNC、客服草稿和视频 QC 的边界建模。
3. Phase 0–8 工程路线、任务卡和 run-ready 设计。

这些资产有价值，但主要降低未来系统失控风险；它们本身不产生合格询盘、订单或履约。

### B. 距离真实销售结果的排序

1. `business_gates` 的书面事实与供应链责任（目前缺失，但对成交必要）。
2. 人工统一询盘承接、资格判断、报价/交接记录（未实现）。
3. 单一内容/信任触点到询盘的受控路径（未核验）。
4. 现有 CRM/DNC/客服手工接管合同（可复用但 synthetic）。
5. B2B 企业发现与精准邮件（后置；没有联系人处理依据不得进行）。
6. 视频、crawler、Agent、全自动化（距离成交最远）。

### C. 原规划偏离销售结果的原因

- 旧 Phase 顺序把大量“安全的内部系统完成度”放在真实 Offer、渠道承接和履约验证之前。
- 以 crawl、fixture、contract 和 QC 数量代替客户、询盘、订单与履约指标。
- 将 CRM 设计成数据实体集合，而不是待跟进客户与下一步动作系统。
- 将视频验收停在技术 QC，未要求 `content_id → inquiry → order outcome` 归因。
- 把不存在的真实 adapter/API/账号能力留在未来规划里，容易被误读为已具备销售能力。

### D. 目标系统的关键差距

| 销售层 | 当前差距 | 先用的低成本方案 | 何时再工程化 |
|---|---|---|---|
| 可销售 Offer | SKU、价格、库存、合法性、履约责任皆未有当前证据 | 供应链书面资料包与人工核验表 | 当资料版本、审批、频繁更新成为瓶颈 |
| 客户承接 | 没有已核验的统一入口和响应 owner | 一个受控 DM/WhatsApp/Web 入口与人工 SOP | 多渠道/时效导致人工遗漏时 |
| 销售推进 | 没有客户阶段、下一步、报价/交接闭环 | 最小字段表与每日人工复盘 | 真实询盘量使表格不可靠时 |
| 订单与履约 | 没有收款、订单、配送、售后责任证据 | 供应链人工确认和可审计交接记录 | 已验证稳定订单路径后 |
| 内容/渠道归因 | 没有 content/channel 到订单关系 | content ID、入口码、人工来源记录 | 有多个内容/渠道且人工核对不可持续时 |
| B2B 精准开发 | 来源、联系人处理、DNC/retention、外发授权不全 | 先不做，或仅 company-only 合规研究 | Offer/合规/数据依据齐备、需要额外机会时 |

## 3. 目标转换原则

1. 先解除业务阻断，再让客户看到商品，再提高询盘和销售推进，最后降低人工成本与完善系统。
2. 所有工程模块必须映射到一个漏斗阶段、一个指标和一个停线；否则 `DEFER`。
3. `technical_ready`、`data_ready`、`business_ready`、`sales_loop_validated` 不能互相替代。
4. 原有安全底座不因方向改变而被放宽；公开酒类行动、真实数据和付款仍 fail-closed。

具体目标架构见 [SALES_SYSTEM_TARGET_ARCHITECTURE.md](SALES_SYSTEM_TARGET_ARCHITECTURE.md)，复用判断见 [CURRENT_SYSTEM_REUSE_MATRIX.md](CURRENT_SYSTEM_REUSE_MATRIX.md)。
