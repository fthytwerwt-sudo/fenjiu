# 核心数据合同

> **状态：DESIGN DRAFT / RECOMMENDED。** 字段用于后续 schema 与 migration 设计；本轮不建表、不导入真实数据。架构边界见 [架构与模块边界](ARCHITECTURE_AND_MODULE_BOUNDARIES.md)，测试约束见 [测试与回滚策略](TEST_AND_ROLLBACK_STRATEGY.md)。

## 1. 全局约定

### 1.1 每条业务记录的基础字段

除全局配置外，所有实体至少带：

| 字段 | 规则 |
|---|---|
| `id` | UUIDv7 或等价可排序全局 ID，客户端不可指定 |
| `tenant_id`, `project_id`, `business_line_id` | NOT NULL；读写时三者都须在授权 scope 内 |
| `data_state` | `fixture` / `staging` / `approved` / `expired` / `blocked` / `conflict` / `superseded` |
| `source_kind` | `fixture` / `supplier_file` / `public_web` / `human_entry` / `system` / `adapter`；不是可信度声明 |
| `source_ref_id` | 指向 `source_file`、`source_snapshot` 或外部证据；无来源不得 `approved` |
| `version_id` | 指向 `data_version`；更新创建新版本，禁止原地丢历史 |
| `created_at`, `updated_at`, `created_by`, `updated_by` | UTC、actor 可审计 |
| `sensitivity` | `public` / `internal` / `confidential` / `restricted_personal` / `secret_reference` |

`fixture` 必须同时有 `is_synthetic=true`；任何将 `fixture` 写到 external adapter、published content、send queue、payment/order command 的命令必须被 policy 拒绝并记录审计事件。

### 1.2 状态转移

```text
fixture ────────────────> superseded
staging -> approved -> expired -> superseded
            |               ^
            v               |
          conflict ----------+
            |
            v
          blocked
```

- `staging`：已提取/录入，尚未完成字段或来源检查。
- `approved`：具备来源、有效期、scope 和人工批准的可用事实；不等于业务已授权公开执行。
- `conflict`：同一 scope/字段存在不能自动裁决的竞争值；所有依赖该字段的答复/内容必须降级。
- `blocked`：缺少必需证明、合规/授权或 policy 禁止。
- `expired`：到达有效期或来源已失效，不能继续被自动使用。
- `superseded`：有明确替代版本；保持可审计历史。

## 2. 身份、隔离、来源与审批

| 实体 | 主键与关键字段 | 状态 / 来源 / 版本 | AI 可做 | 人工闸门 |
|---|---|---|---|---|
| `tenant` | `id`, `slug`, `name`, `status`, data residency policy | `active/suspended`; system | 无 | 创建、删除、权限变更 |
| `project` | `id`, `tenant_id`, `slug`, `name`, `environment`, `external_execution_enabled=false` | project config versioned | 汇总元数据 | 开启外部执行 |
| `business_line` | `id`, `project_id`, `code`, `name`, `line_status`, `allowed_modules` | 独立业务线 | 分类建议 | 业务线创建、启用、合并 |
| `source_file` | `id`, scope, `storage_ref`, `sha256`, `mime_type`, `original_name`, `received_at`, `retention_class` | immutable; `quarantined/processable/rejected` | 文件类型识别、OCR/提取建议 | 去隔离、删除/保留策略 |
| `source_snapshot` | `id`, scope, `url`, `captured_at`, `content_hash`, `collection_policy`, `robots_result`, `license_note` | append-only; `captured/failed/blocked` | 公开页面提取 | 允许采集策略、人工复核 |
| `data_version` | `id`, `entity_type`, `entity_id`, `parent_version_id`, `diff`, `reason`, `effective_from/to` | immutable version chain | 生成差异摘要 | 合并/批准有效版本 |
| `audit_event` | `id`, scope, `correlation_id`, `actor_type/id`, `action`, `before_ref`, `after_ref`, `policy_result`, `occurred_at` | append-only; `success/denied/error` | 不能修改 | 仅通过受控保留策略归档 |
| `approval_request` | `id`, scope, `resource_type/id`, `action_type`, `risk_level`, `reason`, `requested_by`, `decision`, `decided_by/at` | `pending/approved/rejected/expired/cancelled` | 创建请求、摘要 | 批准、拒绝、授权范围 |

`source_file.storage_ref` 只能存对象/私有路径引用与 hash，不把二进制或机密内容放入代码仓库；`audit_event` 默认不保存受限原文，保存 hash、引用和脱敏摘要。

## 3. 导入与标准化合同

| 实体 | 主键与关键字段 | 状态 / 约束 | AI 可做 | 人工闸门 |
|---|---|---|---|---|
| `ingestion_job` | `id`, `source_file_id`, `parser_id/version`, `requested_by`, `idempotency_key`, `started/finished_at` | `queued/running/needs_review/failed/completed`; 同 hash+parser 幂等 | 安全提取、字段候选 | 批准重跑高成本/OCR、处理敏感文件 |
| `extraction_result` | `id`, `job_id`, `schema_hint`, `payload_ref`, `confidence`, `warnings`, `page_or_sheet_locator` | 永不直接成为事实 | 解析、OCR、表格识别、置信度 | 复核低置信/敏感项 |
| `mapping_rule` | `id`, scope, `input_signature`, `target_entity/field`, `transform_spec`, `rule_version`, `approved_by` | `draft/approved/superseded/blocked`; 可回放 | 建议 mapping、缺失/冲突报告 | 批准新规则/规则变更 |
| `normalization_candidate` | `id`, result ref, target entity, `normalized_value`, `validation_result`, `source_locator` | `staging/conflict/blocked/ready_for_approval` | 清洗、单位换算建议、重复检测 | 批准进入 domain entity |
| `review_decision` | `id`, candidate ref, `decision`, `rationale`, `reviewer`, `reviewed_at` | append-only | 不可自行批准 | 接受、修改、拒绝 |

合同要求：原始文件不可被 parser 覆盖；任何字段必须能指回页码/Sheet/行号/图片坐标或可读来源定位；mapping rule 变更须在 fixture 和历史样本上回归。

## 4. 供应链真值中心合同

| 实体 | 主键与关键字段 | 状态、版本与敏感级别 | AI 允许范围 | 人工批准点 |
|---|---|---|---|---|
| `product` | `id`, scope, `canonical_name`, `category`, `brand`, `description`, `lifecycle_status` | `draft/approved/retired`; internal | 归类、提取候选卖点 | 产品身份/品牌/品类批准 |
| `sku` | `id`, `product_id`, scope, `supplier_sku`, `barcode`, `specification`, `unit`, `packaging`, `country_of_origin` | `staging/approved/blocked`; internal | 字段标准化、重复提示 | SKU/包装/来源批准 |
| `price` | `id`, `sku_id`, scope, `amount`, `currency`, `price_type`, `min/max`, `valid_from/to`, `approval_ref` | 仅 `approved` 且未过期可被读取； confidential | 缺失/过期检测、草稿引用 | 金额、币种、有效期、报价使用 |
| `inventory` | `id`, `sku_id`, scope, `quantity`, `unit`, `available_from`, `snapshot_at`, `source_system_ref` | `staging/approved/expired/conflict`; confidential | 一致性/陈旧提醒 | 数量、可售性、替代建议 |
| `delivery_rule` | `id`, scope, `area`, `service_level`, `cutoff`, `fee_rule`, `eligibility`, `effective_from/to` | approved only; confidential | 完整性检查、草稿引用 | 地域/时效/费用/承诺 |
| `compliance_document` | `id`, scope, `document_type`, `issuer`, `valid_from/to`, `storage_ref`, `verification_state` | `unverified/verified/expired/rejected`; restricted | 提取元数据、到期提醒 | 验证、可用于何种动作 |
| `content_asset` | `id`, scope, `asset_type`, `storage_ref`, `rights_state`, `usage_scope`, `expires_at`, `hash` | `candidate/approved/expired/revoked`; restricted | 标签、相似性/质量分析 | 授权、可公开使用 |
| `approved_fact` | `id`, scope, `fact_key`, `value_json`, `source_refs`, `valid_from/to`, `approval_request_id`, `risk_class` | 只读事实视图；`approved/expired/conflict/blocked` | 提议和引用，不得直接创建 approved | 事实批准、撤回、过期处理 |
| `forbidden_expression` | `id`, scope, `pattern`, `category`, `reason`, `applies_to`, `active_from/to` | approved policy artifact; internal | 命中检测 | 新禁语/例外批准 |

**关键不变量：** 客服、内容、外联草稿只能通过 `approved_fact`（以及 `forbidden_expression`）读取可表述事实；不得直读 `price`/`inventory` 原始候选，更不得从模型记忆补充。

## 5. Leads 与 CRM 合同

| 实体 | 主键与关键字段 | 状态/敏感级别 | AI 允许范围 | 人工闸门 |
|---|---|---|---|---|
| `lead` | `id`, scope, `display_name`, `lead_type`, `source_snapshot_id`, `source_url`, `fingerprint`, `evidence_level`, `score` | `candidate/reviewed/accepted/rejected/merged`; `public/internal` | 公共字段提取、去重、评分、草稿 | 接受为 CRM、任何外联 |
| `organization` | `id`, scope, `legal_or_display_name`, `domain`, `address_city`, `verification_state` | `candidate/verified/archived`; internal | 归并建议 | 合并、验证、删除 |
| `contact` | `id`, `organization_id`, scope, `name`, `role`, `channel`, `contact_ref`, `lawful_basis`, `do_not_contact` | `restricted_personal`; `pending/verified/dnc` | 仅在授权/公开商务信息范围建议归并 | 创建/导入个人联系资料、允许联系 |
| `opportunity` | `id`, scope, `organization_id/contact_id`, `stage`, `qualification`, `next_action_at`, `owner` | `new/qualified/nurture/paused/won/lost`; internal | 推荐下一步/风险提示 | 阶段升级到报价、成交、关闭 |
| `interaction` | `id`, scope, target, `channel`, `direction`, `occurred_at`, `content_ref`, `outcome`, `evidence_ref` | immutable; internal/restricted | 摘要、行动项 | 记录真实发送/回复、修改 outcome |
| `crm_stage` | `id`, scope, `code`, `order`, `entry_criteria`, `exit_criteria`, `approval_required` | versioned policy | 校验条件 | 新阶段/规则变更 |
| `do_not_contact` | `id`, scope, target fingerprint, `reason`, `evidence_ref`, `effective_at`, `expires_at` | append-only; restricted | 匹配拦截 | 撤销/例外 |

不能仅靠“名单量”升级机会：`crm_stage` 的转换必须有 `interaction` 或人工证据。任何 `do_not_contact` 命中必须令外联草稿与发送 adapter 失败关闭。

## 6. 客服、内容/视频与外部同步合同

| 实体 | 主键与关键字段 | 状态/敏感级别 | AI 允许范围 | 人工闸门 |
|---|---|---|---|---|
| `conversation` | `id`, scope, `channel`, `external_thread_ref`, `customer_ref`, `mode`, `handoff_state` | `active/handed_off/closed`; restricted | 分类、摘要 | 启动自动答复模式、恢复自动化 |
| `message` | `id`, conversation, `direction`, `body_ref`, `received/sent_at`, `external_message_ref`, `delivery_state` | immutable; restricted | 意图/实体提取、草稿输入 | 记录真实发送，保留/删除例外 |
| `intent` | `id`, message, `label`, `confidence`, `risk_flags`, `model_version` | derived; internal | 分类/置信度 | 高风险分类例外 |
| `draft_reply` | `id`, conversation, `body`, `fact_version_refs`, `policy_result`, `requires_approval`, `expires_at` | `draft/approved/rejected/expired/sent`; restricted | 生成/改写草稿 | 发送、价格/库存/投诉/退款等答复 |
| `handoff_case` | `id`, scope, conversation, `reason_code`, `severity`, `queue`, `assigned_to`, `resolution` | `open/assigned/resolved`; restricted | 检测、摘要、路由建议 | 关闭/恢复自动答复 |
| `content_task` | `id`, scope, `topic`, `audience`, `fact_version_refs`, `script_ref`, `policy_result` | `draft/needs_review/approved/rejected/cancelled`; internal | 选题、脚本、合规检查 | 公开内容批准 |
| `video_task` | `id`, content task, `provider`, `manifest_ref`, `job_state`, `qc_result_ref`, `output_ref` | `queued/running/failed/needs_review/approved`; restricted | 调用 approved legacy adapter、QC 汇总 | 模型调用成本、重试、导出/发布 |
| `external_sync` | `id`, scope, `adapter_type`, `external_id`, `direction`, `cursor`, `payload_hash`, `status`, `idempotency_key` | `pending/succeeded/failed/blocked`; internal | 幂等重试、差异摘要 | 启用 adapter、解决冲突、生产写回 |

`draft_reply` 和 `content_task` 必须保存引用的 `approved_fact.version_id`；当任一事实 expired/superseded/conflict，草稿自动失效并不能被发送/发布。

## 7. 数据合同的最小 JSON 示例（fixture）

```json
{
  "tenant_id": "00000000-0000-7000-8000-000000000001",
  "project_id": "00000000-0000-7000-8000-000000000010",
  "business_line_id": "00000000-0000-7000-8000-000000000100",
  "data_state": "fixture",
  "is_synthetic": true,
  "source_kind": "fixture",
  "sensitivity": "internal",
  "fact_key": "product.display_name",
  "value_json": {"value": "Synthetic Sample Product"},
  "valid_from": "2026-08-06T00:00:00Z",
  "valid_to": "2026-08-13T00:00:00Z",
  "external_execution_allowed": false
}
```

该样例仅演示合同结构，绝不是 SKU、价格、库存、客户或供应链资料。

## 8. Contract 验收规则

1. 每张 contract 都有 schema、valid fixture、invalid fixture、版本号和变更说明。
2. 任一 scoped entity 缺 scope ID、source/version、状态不合法或从 `fixture` 升级为 `approved` 时必须失败。
3. `approved_fact` 缺 approval/source/effective period 时必须失败；`conflict/expired/blocked` 不得被客服/内容读取。
4. 跨业务线 read/write、任何 external sync 使用 fixture、任何 send/publish/refund/order command 缺 approval 都必须失败并生成 `audit_event`。
5. 对 legacy video manifest 只定义 input/output contract，不改变现有脚本的文件布局；回归样本必须覆盖成功、失败、断点和无官方 SKU 素材场景。
