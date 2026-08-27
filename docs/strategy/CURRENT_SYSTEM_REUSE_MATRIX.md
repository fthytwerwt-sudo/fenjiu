# Current System Reuse Matrix｜现有模块处理判断表

- **日期**：2026-08-28
- **原则**：`RETIRE` 表示停止作为当前主路线，不删除历史代码、文档、测试或审计证据。

| 分类 | 资产 | 结论与销售价值 | 进入条件 |
|---|---|---|---|
| `KEEP` | Truth Center、scope/lineage、fixture isolation | 防止过期/未批准商品事实进入内容、报价或客户沟通 | 始终保留 fail-closed 边界。 |
| `KEEP` | DNC、审批、audit、retry/DLQ、人工队列 | 真实询盘/外联/订单进入后仍需要最小化保护与可追责 | 不代表已可处理真实数据。 |
| `KEEP` | workflow checkpoint、内存 contract、negative tests | 在明确的重复流程出现后可降低失误 | 不为架构完整而扩大。 |
| `REFOCUS` | CRM / Leads | 从“数据实体”改为 owner、stage、next action、outcome | 先有合格询盘或明确 B2B 小样本。 |
| `REFOCUS` | Customer Service | 从 synthetic 对话合同改为统一询盘的人工优先承接 | 指定渠道和隐私/账号边界已核验。 |
| `REFOCUS` | Content / Video | 从生成/QC 成功改为 content/channel → inquiry → outcome | 有可售 Offer、CTA、归因记录。 |
| `REFOCUS` | Analytics | 从内部技术指标改为内容/渠道/销售归因 | 有最小字段和真实或受控试点数据。 |
| `REFOCUS` | Source Catalog / CrawlPort | 从 page/company 数改为 valid/qualified/contactable/reply/opportunity 质量 | B2B 阶段、来源/条款/联系人依据齐备。 |
| `DEFER` | Gmail sender/inbox/outbox、自动 outreach | 高价值 B2B 的后置能力，不是当前获客中心 | 真实 Offer、联系人处理依据、DNC/retention、审批、授权、对账设计。 |
| `DEFER` | LangGraph/Agent 多步编排 | 仅当 deterministic workflow 无法处理已证明的动态分支/恢复 | 有重复的复杂人工流程和退出验证。 |
| `DEFER` | 真实 video/AI/CRM provider | 现有 adapter 均 fake 或缺失，不能假定 SDK/API 可用 | 先证明销售瓶颈和供应商/政策/成本。 |
| `DEFER` | 多平台自动分发、广告、批量内容 | 未证明渠道 ROI 且酒类政策/项目授权未核验 | SR-3/4 有证据后单独决策。 |
| `RETIRE / SUPERSEDE` | “先完成 AI Native Sales OS，再寻找销售用途” | 被 Sales-First 北极星替代 | 历史规划保留为工程资产。 |
| `RETIRE / SUPERSEDE` | TikTok-only 作为长期项目中心 | 被“一个销售系统、多个受控触点、一个漏斗”替代 | TikTok 仍是候选渠道，不自动恢复多平台运营。 |
| `RETIRE / SUPERSEDE` | crawl count/page count/company count 作为成功标准 | 被合格账户、询盘、对话、订单 outcome 替代 | 只作为运营过程诊断，不作业务 KPI。 |
| `NEW` | Sellable Offer evidence contract | 将 SKU、价格、库存、合规、支付、履约从缺口转为可审计输入 | 供应链/当地责任人提供书面证据。 |
| `NEW` | Unified inquiry intake + manual sales SOP | 让客户可进入且有人负责下一步 | 指定渠道和承接方式获授权。 |
| `NEW` | Offer/order handoff 与 sales attribution | 把询盘连接到供应链交接和反馈 | 业务闸门满足后，先用人工记录。 |
