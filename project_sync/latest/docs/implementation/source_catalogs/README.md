# Source Catalog Config｜来源目录机器配置说明

本目录保存未来 Codex 读取的**来源配置**，而不是客户数据库。

## 文件与用途

| 文件 | 业务线 | 用途 |
|---|---|---|
| `fenjiu_sources.yaml` | `fenjiu_nepal` | 汾酒未来企业发现的来源、条款、字段、裁决和 fallback（备用来源）配置。 |
| `seafood_sources.yaml` | `seafood_nepal` | 海鲜未来企业发现的来源、条款、字段、裁决和 fallback 配置。 |

任何一次运行只能读取**一个**业务线的 YAML。不得把两份配置合并成同一候选列表，或把一个业务线的 `source_id` 用于另一业务线。

## Schema（数据结构）

每个来源必须有下列字段：

```yaml
source_id: "稳定且全局唯一的来源 ID"
business_line: "fenjiu_nepal | seafood_nepal"
source_name: "来源名称"
source_owner: "来源运营方"
source_country: "来源覆盖国家"
source_category: "目录/协会/开放数据/监管流程等"
source_tier: "A | B | C | D | X"
source_homepage: "来源主页"
discovery_entry_url: "实际研究过的发现入口"
terms_url: "条款；未知则 null"
privacy_url: "隐私政策；未知则 null"
robots_or_access_policy_url: "robots、API 或访问政策；未知则 null"
terms_reviewed_at: "最后复核日期与缺口"
data_freshness: "已知更新时间或 unknown"
target_customer_types: []
supported_geographies: []
available_company_fields: []
available_contact_fields: []
company_data_storage_status: "allowed | conditional | prohibited | unknown"
contact_data_processing_status: "allowed | conditional | prohibited | unknown"
bulk_access_status: "allowed | conditional | prohibited | unknown"
login_required: "true | false | conditional | unknown"
paid_access_required: "true | false | conditional | unknown"
captcha_or_anti_bot_present: "true | false | conditional | unknown"
official_api_available: "true | false | conditional | unknown"
manual_search_available: "true | false"
recommended_query_patterns: []
recommended_search_keywords: []
nepali_keywords_verified: "true | false"
evidence_refs: []
confidence: "high | medium | low"
use_decision: "APPROVED_FOR_DISCOVERY | CONDITIONAL | MANUAL_ONLY | REJECTED"
reason_codes: []
stop_conditions: []
fallback_source_ids: []
last_reviewed_at: "YYYY-MM-DD"
```

若 `use_decision=APPROVED_FOR_DISCOVERY`，还必须提供 machine-enforceable（机器可执行）的 `access_constraints`：

```yaml
access_constraints:
  requires_attribution: true
  max_requests_per_second: 1
  requires_identifying_user_agent: true
  public_service_only_for_manual_queries: true
  systematic_enumeration_prohibited: true
  details_page_automation_prohibited: true
  cache_policy: "no candidate-store persistence in the current task"
  retry_policy: "stop on rate-limit or policy uncertainty; no automatic retry loop"
```

## 三个必须分开的裁决

| 字段 | 回答的问题 | 不能推断 |
|---|---|---|
| `use_decision` | 来源是否能用于发现企业候选。 | 企业信息一定能存、联系人一定能处理或可以外联。 |
| `company_data_storage_status` | 最小公司级字段能否进入未来的私有 candidate store（候选存储）。 | 联系方式、人员信息、信用或采购事实可以保存。 |
| `contact_data_processing_status` | 是否已存在处理 business email/phone/WhatsApp 的政策依据。 | 来源网页公开就等于 allowed。 |

`APPROVED_FOR_DISCOVERY` 只放行发现，不放行持久化。当前两个已批准来源的 `company_data_storage_status` 均为 `conditional`，所以运行模式固定为 `transient_discovery_only`：可以由人工临时查看公司级发现结果并回企业官网交叉验证，但**不得**写入 candidate store、CRM、日志或 Git。只有 `company_data_storage_status=allowed`、来源条款/保留政策和未来 P08-RAB 准入合同同时满足时，才可改变持久化开关。

本期两份配置没有任何 `contact_data_processing_status: allowed`。`REJECTED` 来源绝不允许出现在任何运行包的 `approved_source_ids` 中。

## Codex 读取规则

1. 先验证 `business_line`、`product_scope`、`source_catalog_version` 与目标 YAML 一致。
2. 只允许使用 `approved_source_ids` 中 `use_decision=APPROVED_FOR_DISCOVERY` 的来源进行最小企业发现。
3. 对每个已批准来源，验证 `access_constraints`；任何缺失、超过 `max_requests_per_second`、无识别性 User-Agent、系统化枚举或违反缓存/重试策略都返回 `blocked_source_access_policy`。
4. 若来源的 `company_data_storage_status` 不是 `allowed`，只能进入 `transient_discovery_only`，不能自动复制或持久化公司字段。
5. `CONDITIONAL` 与 `MANUAL_ONLY` 只能用于人工来源研究或回企业官网验证，不能自动复制资料。
6. `REJECTED`、Google Maps/Places 抓取、付费联系人产品、私人社交资料、登录/验证码绕过一律拒绝。
7. 任何发现观察必须回企业自有官网或另一个允许来源交叉验证；不得由搜索结果片段、点评站或地图结果单独成立。
8. 当前不允许提取/猜测邮箱、电话、WhatsApp 或采购联系人；不写 CRM，不产生外联草稿。

## 维护与失效

- 每次真实来源测试前，重新打开 `discovery_entry_url`、`terms_url` 和 `robots_or_access_policy_url`；记录复核日期和变化。
- 条款变更、访问限制、登录/验证码、来源 owner 不明、来源失效或业务线不一致时，先降级为 `CONDITIONAL`、`MANUAL_ONLY` 或 `REJECTED`。
- 新来源必须先以 `CONDITIONAL` 进入，附真实 `evidence_refs`，经过人工审查后才可能成为 `APPROVED_FOR_DISCOVERY`。
- 不把客户名称、联系人、价格、库存、进口记录、订单、Cookie、Token、密码、API key 或本地绝对路径写入此目录。

## 当前能力状态

```yaml
capability_status:
  source_catalog_ready: true
  real_customer_discovery_not_started: true
  transient_discovery_only: true
  candidate_store_write_enabled: false
  contact_processing_blocked: true
  crm_write_blocked: true
  gmail_send_blocked: true
```
