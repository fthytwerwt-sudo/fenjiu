# 核心数据合同、真值中心与业务线隔离

> **状态：PLANNED。** 这是 Phase 2 的唯一领域合同来源。字段名是建议 schema，不表示当前已有数据库、SKU、价格、客户或订单数据。

## 1. 每个业务实体的不可省略字段

除 `tenant` 外，每个持久业务实体必须包含：

```text
id (UUID), tenant_id, project_id, business_line_id,
data_state, source_ref_id, data_version_id,
created_at, updated_at, created_by, correlation_id
```

`business_line_id` 永不从 UI 筛选或 prompt 推断，必须由 authenticated scope 注入。唯一约束和外键均带 tenant/project/business line；repository/query/worker payload 都拒绝缺 scope 或跨线 scope。

合法 `data_state`：`fixture`、`mock`、`staging`、`approved`、`expired`、`blocked`、`conflict`、`superseded`。`fixture/mock` 必须有 `is_synthetic=true` 与 `external_execution_allowed=false`；它们不能提升为 real/approved，只能被明确替换。`approved` 不等于 external action permitted。

## 2. 核心实体合同

| 实体 | 主键 / 关键唯一约束 | 来源、版本与敏感级别 | AI 自动可改 | 必须人工批准 / 过期冲突 / 留存 |
|---|---|---|---|---|
| `tenant` | `id`; `slug` global unique | 管理创建；`restricted` | 无 | 业务线、管理员、数据区域；软删禁止，关闭后 archive。 |
| `project` | `id`; `(tenant_id, slug)` | 决策来源；`internal` | display metadata 草稿 | business line 开启/关闭；archive，不级联删除事实。 |
| `business_line` | `id`; `(tenant_id, project_id, slug)` | 用户/项目决定；`restricted` | 无 | `fenjiu_nepal`/`seafood_nepal` 创建与外部 flags；禁用后只读 archive。 |
| `source_file` | `id`; `(tenant_id, sha256, storage_locator_version)` | uploader、hash、MIME、收到时间；`confidential`/`restricted` | MIME/OCR 分类建议，不可改 hash/原件 | quarantine、可处理性、保留期；原件私有存储、到期后受控销毁记录保留。 |
| `ingestion_job` | `id`; `(source_file_id, parser_version, mapping_profile_version)` idempotent | parser/mapping、attempt、input hash；`internal` | extraction/mapping candidate、低风险 normalization | 重跑、失败恢复、批准前状态；保留 job/错误码，原文最小化。 |
| `extraction_result` | `id`; `(ingestion_job_id, extractor_version, content_hash)` | page/sheet/row/cell/bbox；`confidential` | 文本/OCR/table candidates 与 confidence | 人工修订定位和低置信结果；不可覆盖，生成新 version。 |
| `mapping_rule` | `id`; `(business_line_id, source_signature, target_contract, version)` | 示例 hash、owner；`internal` | AI proposal、同一 fixture replay | 规则激活、字段合并、敏感字段 mapping；supersede 保留历史。 |
| `product` / `sku` | `id`; `(scope, canonical_product_code)`；SKU `(scope, sku_code, effective_from)` | 供应链资料/素材；`restricted` | 名称翻译、单位规范、候选去重 | 身份、规格、酒精度、条码、素材权利、可售状态；冲突→`conflict`，不静默取最新。 |
| `price` | `id`; `(scope, sku_id, price_type, currency, effective_from, source_version)` | 价格文件、有效区间；`restricted` | 币种/小数/日期标准化建议 | 金额、最低价、税/运费、佣金、有效期；到期→`expired`，冲突→`conflict`，不删除。 |
| `inventory` | `id`; `(scope, sku_id, location_ref, observed_at, source_version)` | 库存/补货报告；`restricted` | 单位规范、异常检测 | 数量、批次、可售性、补货承诺；按 freshness policy 过期/冲突。 |
| `delivery_rule` | `id`; `(scope, region_ref, service_type, effective_from)` | 履约 SOP；`restricted` | 结构化候选 | 区域、时效、运费、退换货、责任；到期/冲突使报价和客户答复失效。 |
| `compliance_document` | `id`; `(scope, document_kind, issuer, issue_date, file_hash)` | 签发方、有效期、原文件；`restricted` | 文本提取、到期提醒 | 授权/许可真实性、适用范围；过期/撤销自动 `blocked` 下游。 |
| `content_asset` | `id`; `(scope, asset_hash, rights_version)` | 权利、来源、使用限制；`restricted` | 标签、转写、候选分类 | 素材权利、真人/商品身份、对外用途；未批准只可内部。 |
| `approved_fact` | `id`; `(scope, fact_type, subject_ref, data_version_id)` | 指向 extraction/source/version/approval；按事实敏感级别 | 无；AI 只能提出 candidate | 创建、变更、revoke；expired/conflict/superseded 禁止被 query 层返回。 |
| `forbidden_expression` | `id`; `(scope, locale, normalized_text, policy_version)` | 合规/品牌 policy；`restricted` | 命中检测、候选改写 | 新禁语、豁免、适用范围；policy 失效后重新审核草稿。 |
| `lead` | `id`; `(scope, source_fingerprint)` | public snapshot + evidence；`personal/restricted` | 提取、分类、评分、去重候选 | accept/merge、联系合法性、DNC；source 过期不删证据，停跟进。 |
| `organization` / `contact` | `id`; org `(scope, normalized_name, domain_or_address_hash)`；contact `(scope, organization_id, normalized_contact_hash)` | public/consented source；`restricted` | 名称规范、关联候选 | 建档、合并、联系方式、DNC；保留最小证据，按政策匿名/删除 PII。 |
| `opportunity` / `interaction` / `crm_stage` | `id`; opportunity `(scope, organization_id, pipeline_key)`；interaction external id idempotent | CRM action source；`restricted` | stage 建议、摘要/next step draft | stage 变更、发送记录、金额/合同；DNC/删除请求优先。 |
| `conversation` / `message` | `id`; conversation `(scope, channel_ref, external_conversation_id)`；message `(conversation_id, external_message_id)` | channel adapter、consent/retention；`restricted` | intent、translation、risk tags、摘要 | 接入、人工接管、保留期限、任何发送；hash/redact 内容，不存不必要 PII。 |
| `intent` / `draft_reply` / `handoff_case` | `id`; draft `(message_id, policy_version, fact_version_set_hash)` | model/policy/fact versions；`restricted` | draft、classification、translation | high-risk intent、回复批准、handoff close；facts/policy 变更即 `superseded`。 |
| `content_task` / `video_task` | `id`; video `(content_task_id, provider, idempotency_key)` | fact lock、manifest、provider refs；`internal/restricted` | script/storyboard/prompt/QC candidate | brief、素材权利、提交成本、视频/导出批准；过期事实停止任务。 |
| `approval_request` | `id`; `(scope, action_type, subject_ref, version, state=pending)` | actor, policy, evidence；`restricted` | 创建建议，不能 approve 自己 | approve/reject/revise/expire；append decisions、不可覆写。 |
| `audit_event` / `data_version` / `external_sync` | `id`; audit `(correlation_id, sequence)` unique; version `(entity_type, entity_id, version_no)` | actor、hash、scope、policy；`restricted` | 无 | append-only；更正用新 version/supersede，保留期后加密归档而非普通删除。 |

## 3. 版本、冲突与删除规则

1. 更新 `approved_fact`、价格、库存、规则或合规资料时只创建新的 `data_version`，保留 `parent_version_id`、field diff、source evidence 与 decision。
2. 相同事实 scope 中存在相互矛盾的有效值，创建 `conflict`；系统不得按时间戳/模型置信度私自选择。人工决定产生一个新 `approved` version，其他 version 标记 `superseded` 而不删除。
3. freshness policy 必须按 fact type 可配置。到期的 `price/inventory/delivery_rule/compliance_document` 会让相关草稿、缓存和 content task 失效；无有效 approved truth 时返回 handoff/unknown。
4. 原始文件由私有存储及记录的 retention policy 控制；Git 仅存 fixture、schema 和无敏感报告。客户/联系人数据的删除、匿名或法律保留请求由专门 command 处理，必须写 audit event，不可 `DELETE` 绕过。

## 4. 合同级验收

- valid/invalid fixtures 覆盖每个实体的 scope、source、version、state 和敏感级别。
- 跨 tenant/project/business line 查询、缺 source/version、`fixture → external action`、`candidate → approved`、过期/冲突事实读取全部必须失败。
- AI output 只能创建 candidate/draft；价格、库存、合规、发送、发布、退款、订单和审批的 positive path 必须有具权限的人类 actor 与 evidence。
- 导入、webhook、video submission、外部 sync 的 idempotency key 在重跑时不产生重复事实、互动、消息或外部副作用。

## 5. Phase 1 port contract 冻结

P00-02 只冻结 port contract 名称和失败语义，不创建 schema、migration 或具体依赖版本。所有 port payload 必须携带 `tenant_id`、`project_id`、`business_line_id`、`correlation_id`、`idempotency_key`、`actor_ref`、`feature_flag_snapshot` 和 `policy_decision_ref`；缺任一字段必须 fail closed。

| Port | 输入必须证明 | 输出只能产生 | 默认失败语义 |
|---|---|---|---|
| `WorkflowPort` | scope、checkpoint key、approval subject、retry policy | workflow state、audit event、next command proposal | checkpoint 不可恢复或 action policy 不明时暂停，不执行外部动作。 |
| `CrawlPort` | approved source policy、robots/terms review ref、rate limit、business line scope | public snapshot candidate、source hash、extraction candidate | policy/terms/频率不明时 `blocked`；不得创建 CRM contact 或发送。 |
| `CrmPort` | approved lead/contact decision、DNC status、export scope | external id mapping、interaction draft/export record | DNC、scope mismatch 或 adapter disabled 时 manual-only。 |
| `SupportPort` | conversation consent/retention、approved fact version set、risk classification | draft reply、handoff request、approved-send request | 无 approved fact、高风险、平台/账号未授权时 handoff，不发送。 |
| `VideoPort` | content task、fact/asset/policy lock、cost approval、synthetic/real data origin | manifest candidate、provider task ref、QC result | legacy/provider 未验证、素材权利不明、fact 过期或 cost 未批时停止。 |

这些 contract 的存在不表示对应模块已实施，也不表示外部 workflow/crawl/CRM/support/video provider 已可用。真实 provider 接入前必须另有 ADR/风险评审、版本/许可证核验、fake contract 和关闭 adapter 后的 export/readback 测试。
