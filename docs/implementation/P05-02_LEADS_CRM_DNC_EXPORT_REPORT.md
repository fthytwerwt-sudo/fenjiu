# P05-02｜Leads、CRM、DNC 与可替换导出报告

> **状态：task_branch_completed_for_controller_review；main 集成、业务状态和 Phase 5 完成由总控另行审查决定。**
>
> **执行日期：** 2026-08-09
>
> **精确工程基线：** `origin/main` `914a76146f47734d2989b4d4ce71c5fdaeedd988`
>
> **任务分支：** `codex/p05-02-leads-crm-domain`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic 的 lead review、CRM domain、DNC/withdrawal、retention intent 和 scoped JSON/CSV export 合同。不安装 Twenty，不接 CRM provider，不外发，不读取或写入真实 contact、客户、供应链、价格、库存、资质或身份资料。

## 1. 结论

- 新增 `core/contracts/leads_crm.py`，把 `SyntheticLeadCandidate`、`LeadReview`、`LeadDedupeResult` 和 `LeadReviewDecision` 放在模块边界之下，避免 `modules/crm` 反向依赖 `modules/leads`。
- 新增 `modules/crm/domain.py`，实现 `CrmRepository`、`DncRegistry`、`CrmExportService`、organization/contact/opportunity/interaction/stage、retention intent 和可审计 scoped export。
- 新增 `migrations/0003_leads_crm_dnc_export.sql`，建立 lead/review/organization/contact/DNC/opportunity/interaction/retention 8 张 local contract 表及触发器。
- 新增 `tests/contracts/test_leads_crm_domain.py`，覆盖 reviewed lead 才能进入 CRM、source/consent/DNC gate、source-aware dedupe、跨业务线拒绝、DNC 冻结/反绕过、export scope 与 deletion/retention intent。
- 更新 migration regression，要求 `0003` replay 成功、CRM 表计数正确，并验证 contact consent、跨业务线、DNC immutable 和 external execution 禁止等 SQL 负例。

## 2. 行为合同

| 行为 | P05-02 稳定结果 |
|---|---|
| 未 review / rejected lead 进入 CRM | `lead_review_required` |
| unresolved identity approve | `merge_candidate_manual_review_required` |
| 同 source + 同 organization fingerprint | `duplicate`，理由 `same_source_fingerprint` |
| 不同 source + 同 organization fingerprint | `merge_candidate`，不得静默合并 |
| contact 缺 source 或 consent | `contact_source_consent_required` |
| DNC/withdrawal 命中 contact 或 draft | `dnc_blocked` |
| prompt/admin override 尝试绕过 DNC | 仍按 DNC 拒绝 |
| scoped export 请求其他 business line | `cross_scope_forbidden` |
| retention delete/anonymize intent | contact 从 export contacts 中省略，intent 仍保留为审计线索 |
| provider ID | 不作为 JSON/CSV key；Twenty/UI adapter 仍 `deferred` |

## 3. 数据与迁移边界

- CRM domain 只保存 hash、内部 ref、scope、evidence ref、consent/DNC 状态和合成标记，不保存真实姓名、电话、邮箱、社交账号、价格、库存或 provider ID。
- PostgreSQL migration 只建合同 schema 和约束，不插入 tenant、客户、供应链、联系人或业务数据。
- `dnc_records` 与 `retention_intents` 均通过 trigger 阻止 update/delete；DNC 覆盖 contact 与 draft。
- `interactions` 固定 `sent_count=0`、`external_sent=false`，`send_attempt` 被 SQL CHECK 拒绝。

## 4. Test-first evidence

- **RED（Python）**：新增 `tests/contracts/test_leads_crm_domain.py` 后，首次运行 `python3 -m unittest tests.contracts.test_leads_crm_domain` 失败于 `ImportError: cannot import name 'CrmBoundaryError' from 'modules.crm'`。
- **RED（migration）**：更新 migration regression 后，首次运行 `sh tests/migrations/run_scope_migration_regression.sh` 失败在缺少 P05-02 CRM 表与 `0003` migration。
- **GREEN**：实现 core contract、CRM domain、`0003` migration 与 SQL 负例后，P05-02 专项 7 项通过，migration replay/negative constraints 通过。
- **Boundary repair**：首次完整 `make regression` 在 architecture guard 失败，原因是 `modules/crm/domain.py` 直接 import `modules.leads.domain`；已将共享 lead/CRM contract 下沉到 `core/contracts/leads_crm.py` 后，architecture 和完整回归通过。

## 5. Validation evidence

- `python3 -m unittest tests.contracts.test_leads_crm_domain`：7 项通过。
- `sh tests/migrations/run_scope_migration_regression.sh`：通过；两轮 migration replay、P05-02 新增 SQL 负例和既有 P02 负例均通过。
- `python3 -m unittest tests.contracts.test_leads_crm_domain tests.contracts.test_source_policy_and_crawl_port tests.contracts.test_action_policy_rbac_approvals tests.contracts.test_audit_metrics_retry_dead_letter`：31 项通过。
- `python3 -m unittest discover -s tests/architecture`：8 项通过。
- `python3 -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests`：通过。
- `make regression`：通过；两轮 migration replay、8 architecture、14 regression、8 local-runtime、16 control-plane、77 contracts、35 ingestion tests 全部通过。

## 6. 工程治理检查

- `repository_hygiene_check（仓库卫生检查）`：新增代码、migration、测试和报告仅含 synthetic/value-free ref、hash、scope 与相对路径；不含 secret、token、cookie、私人联系方式、真实客户、真实供应链、真实价格/库存或本地绝对路径。
- `configuration_validation（配置验证）`：未新增环境变量、生产连接、CRM provider、Twenty、SDK、队列、外发端点或真实账号。
- `data_safety_check（数据安全检查）`：未读取 `research_channels.json`、真实 contacts、客户、供应链、价格、库存、资质或身份资料；跨业务线通过 `ScopeRef` 和 SQL FK/trigger 拒绝。
- `dependency_compatibility_check（依赖兼容检查）`：`not_applicable`；未新增或修改依赖。
- `failure_handling（失败处理）/ negative behavior test（负向行为测试）`：覆盖缺 source/consent、DNC、prompt override、unresolved merge、duplicate、cross-scope、provider-key export、retention intent、SQL immutable 和 external execution 禁止。

## 7. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P05-02 synthetic lead review、CRM domain、DNC/withdrawal、retention intent、scoped export 和 `0003` migration 已在任务分支通过验证。
- **CONFIRMED（工程边界）**：CRM 真值仍在本系统合同；Twenty、UI、provider adapter、真实 CRM 同步和外部发送均保持 `DEFER`。
- **BLOCKED（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界、真实联系人合法性、真实外部执行授权仍未建立或未获当前书面证据。
- **不成立**：本任务不代表 Phase 5 完成、CRM 可用于真实业务、找客完成、联系人可联系、外联授权、上线、销售、收款、订单或履约能力。

## 8. P05-03 handoff

P05-03 可复用：

- `CrmRepository.review_lead()` 与 `create_crm_record()`：作为 reviewed CRM entity 输入；只接受 synthetic reviewed lead。
- `DncRegistry.is_blocked()` 与 `record_withdrawal()`：用于 draft 前 DNC gate；DNC 不可被 prompt/admin override 绕过。
- `CrmExportService.export_scope()`：用于 internal JSON/CSV export；provider ID 不作为 key，future adapter/UI 保持 `deferred`。
- `InteractionKind.DRAFT` 与 `create_interaction()`：可作为 draft-only 内部记录入口；`SEND_ATTEMPT` 和 external send 仍禁止。
- `retention_intents`：用于 deletion/anonymization intent；export 需继续尊重 retention restriction。

P05-03 不应假设：

- 不应创建真实 recipient、真实 contact、真实外部发送端口、email/WhatsApp/social adapter 或 provider credential。
- 不应把 CRM review、DNC、export 或 draft approval 写成发送、报价、库存、交期、平台许可或业务完成。
- 无 approved price/inventory truth 时，草稿只能写“需确认”的内部建议，不得生成金额、库存或交期承诺。
