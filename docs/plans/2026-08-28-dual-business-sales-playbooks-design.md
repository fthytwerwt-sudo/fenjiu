# 双业务线 Sales-First 执行手册设计

## Goal｜目标

把既有 Sales-First 总规划转化为两套独立、可直接执行且可审计的行动手册：`fenjiu_nepal` 与 `seafood_nepal`。每套手册只在相应阶段说明当前可做动作、不可做动作、需要的供应链输入、单一渠道试验、人工销售承接、数据记录与下一阶段解锁条件。

## 已确认约束

- 汾酒当前为 `SR-1 Sellable Offer Ready`；`fenjiu_20_year` 与 `fenjiu_30_year` 是唯一允许的产品标识。公开资料可以构成内部内容事实候选，不能替代尼泊尔 SKU、价格、库存、主体/授权、平台资格、收款与履约证据。
- 海鲜的 2026 年第一批次货品单可作为产品候选与包装/数量记录来源；它不能证明当前可售库存、产品标签合规、食品/进口资格、冷链、价格、收款或配送能力。
- 任何公开发布、广告、真实报价、收款、订单、履约、外联或处理真实联系人仍须由业务闸门、政策和用户具体授权解除。
- 视频可由 AI 生成，但视觉标准是 `iPhone Natural Look`。真实产品包装、标签、人物、门店、客户、评价和本地场景不得由 AI 虚构；未获素材权利时只可生成无品牌、无标签的内部预演镜头。

## 设计选择

采用“**一条线一套主手册 + 一条线一套内容手册 + 两份共用控制表**”而非把所有细节堆入现有总规划。

1. `FENJIU_EXECUTION_PLAYBOOK.md` 与 `SEAFOOD_EXECUTION_PLAYBOOK.md`：独立描述阶段、Offer gate、销售 SOP、渠道顺序、日周节奏、输入与停止线。
2. `FENJIU_CONTENT_PLAYBOOK.md` 与 `SEAFOOD_CONTENT_PLAYBOOK.md`：独立描述目标客户、内容支柱、hooks、AI iPhone 视觉约束、脚本、caption、CTA、QC 与首批内容卡。
3. `DUAL_BUSINESS_LINE_STAGE_GATE_MATRIX.md`：让用户在一个页面判断“现在做什么 / 不做什么 / 何时解锁”。
4. `DUAL_BUSINESS_LINE_KPI_SCORECARD.md`：定义每阶段 Output / Funnel / Decision 指标，且将任何缺真实基线的数字标为 `RECOMMENDED_INITIAL_TEST_THRESHOLD`。

## 内容与事实安全设计

每张内容卡都含 `fact_lock_required`、`proof_needed`、`compliance_check`、`publish_status` 与 `sales_metric`。对没有供应链实证的事实采用以下表达：

- 可写：饮用/烹饪场景、产品类别的教育性问题、需要核验的包装信息、客户资格问题、过程性 CTA。
- 不可写：尼泊尔价格、现货、交期、进口或销售许可、冷链温度、口感承诺、健康功效、客户评价、市场领先、实际销量。
- `publish_status` 默认 `publish_blocked_pending_business_gates`；只有逐项事实、素材权利、平台政策与外部授权有效时才能改为可发布。

## 业务路线设计

- **汾酒**：先核验一个 20 年或 30 年的具体 SKU/Offer；之后以一个获准的内容发现渠道和一个非交易询盘入口测试人工销售闭环。B2B 是后置的低频精准试点。
- **海鲜**：建议 `B2B-first`，因为当前货品单以箱规/重量与多 SKU 为中心，且冷链、验收、批量采购和履约是首要未知项；B2C 为证据充分后的第二路线，而非同时启动。此为 `RECOMMENDATION`，不是已验证的商业结论。

## 验证设计

文档必须通过：Markdown 链接/交叉引用检查、`git diff --check`、明确禁止事实/隐私/本地绝对路径扫描、双线关键词污染检查、阶段/`NOT NOW`/停止线/内容卡数量检查、项目机制验证与相关回归。
