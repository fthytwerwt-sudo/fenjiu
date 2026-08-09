# P05-01｜公开来源 policy 与 fake CrawlPort 报告

> **状态：task_branch_local_validated；最终 commit / push / remote readback 以执行回报为准。**
>
> **执行日期：** 2026-08-09
>
> **精确工程基线：** `origin/main` `eda64feb9945e1f9f2eaa688b1152f87b8182bf5`
>
> **任务分支：** `codex/p05-01-source-policy-crawl-port`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic 的 source policy、snapshot hash、evidence locator 与 fake `CrawlPort` 合同。不访问真实网址，不读取 `research_channels.json`，不读取真实联系人、供应链、价格、库存、资质或身份资料，不创建 CRM lead/contact，不外发、不发布、不报价。

## 1. 结论

- 新增 `modules/leads/source_policy.py`，定义 `SourcePolicy`、`PublicSnapshot`、`EvidenceLocator`、`PublicFieldCandidate` 与稳定 `CrawlBoundaryError`。
- 新增 `adapters/crawl/fake.py`，实现 `FakeCrawlPort`。端口只从内存合成 fixture 读取 HTML 字符串并生成 hash；`external_fetch_count=0`，无 crawler SDK、browser、HTTP client 或网络调用。
- 新增 `fixtures/leads/synthetic_public_sources.json`，只包含 `.invalid` 合成来源、合成 HTML 与 value-free evidence 输入；`.gitignore` 与 architecture 测试只允许该 fixture 入 Git。
- 所有进入路径必须通过 policy/robots/terms/owner gate：缺 policy、owner、robots review、terms review 或被 robots/terms 拒绝均 fail closed，并写 P04 append-only audit。
- login、CAPTCHA、authentication required、private source 一律拒绝并写安全审计；公开页面 snapshot/evidence 不等于企业真实性、可联系授权或外联许可。
- HIGH 修复后，P05-01 policy 与 fake crawl extraction 双层拒绝联系语义字段；`contact`、`email`、`phone`、`whatsapp`、`wechat`、`telegram`、`linkedin`、`outreach` 等字段不得进入 `allowed_fields`、evidence 或 candidate，即使来源是 synthetic、value-hash、zero-network。

## 2. Source policy 字段

`SourcePolicy` 必填或显式检查：

```text
policy_id
scope
purpose
owner_ref
allowed_url_prefixes
robots_review_ref
robots_allowed
terms_review_ref
terms_allowed
allowed_fields
max_frequency_per_day
retention_days
manual_review_required
stop_conditions
data_state=fixture
is_synthetic=true
external_execution_allowed=false
business_external_ready=false
```

阻断字段：

```text
login_required
captcha_required
private_source
authentication_required
```

当前仅允许 `.invalid` synthetic URL，用于证明 contract；真实 public source policy、robots/terms 复核、频率配置和任何真实 crawl 需后续单独授权任务。

## 3. Snapshot / evidence 合同

`PublicSnapshot` 只保存：

```text
scope
policy_id
snapshot_ref
content_hash
source_url_hash
retrieved_at
http_policy_result=synthetic_zero_network
data_state=fixture
is_synthetic=true
external_execution_allowed=false
business_external_ready=false
```

`PublicFieldCandidate` 只保存 field name、value hash 和 evidence locator；不保存 HTML、原始 URL、字段原文、联系人或外联资料。`safe_summary()` 只输出安全引用、hash 和 scope。

## 4. Negative behavior proofs

| 场景 | 稳定结果 |
|---|---|
| no policy / missing policy id | `source_policy_required` |
| missing owner | `source_owner_required` |
| missing robots review | `robots_review_required` |
| robots denied | `robots_denied` |
| missing terms review | `terms_review_required` |
| terms denied | `terms_denied` |
| login required | `login_required_source_forbidden` |
| CAPTCHA required | `captcha_source_forbidden` |
| private source | `private_source_forbidden` |
| authentication required | `authentication_source_forbidden` |
| contact/email/phone/social/outreach field requested | `public_field_forbidden` |
| cross business line snapshot reuse | `cross_scope_forbidden` |
| external export attempt | `external_export_forbidden` |

所有拒绝路径保持 `external_fetch_count=0` 并追加 audit event；audit metadata 仅含 source URL hash、snapshot ref、field count、reason code 和 fetch count，不含 URL、HTML、字段原文、联系人、secret、token、cookie 或本地路径。

## 5. Test-first evidence

- **RED**：新增 `tests/contracts/test_source_policy_and_crawl_port.py` 后，首次运行 `python3 -m unittest tests.contracts.test_source_policy_and_crawl_port` 失败于 `ImportError: cannot import name 'FakeCrawlPort' from 'adapters.crawl'`。
- **GREEN**：新增最小 `SourcePolicy` 与 `FakeCrawlPort` 后，同一 P05-01 专项 5 项通过。
- **Review HIGH RED**：新增 contact-like field policy / forged policy / extract bypass tests 后，同一 P05-01 专项先失败，`SourcePolicy.allowed_fields` 可接受 `contact_email`，`FakeCrawlPort.fetch_snapshot()` 与 `extract_public_fields()` 未拒绝并可能生成 candidate。
- **Review HIGH GREEN**：新增 `public_field_forbidden` 双层拒绝后，policy construction、policy validation、extract-time field inspection 均 fail closed；审计只记录安全 hash/result code，不记录原字段名、字段值、CRM/contact/outreach payload。P05-01 专项 8 项通过。

## 6. Validation evidence

- `python3 -m unittest tests.contracts.test_source_policy_and_crawl_port`：8 项通过。
- `python3 -m unittest discover -s tests/contracts`：70 项通过。
- `python3 -m unittest discover -s tests/architecture`：8 项通过。
- `python3 -m unittest discover -s tests/workflows`：11 项通过。
- `python3 -m unittest tests.contracts.test_action_policy_rbac_approvals tests.contracts.test_audit_metrics_retry_dead_letter`：16 项通过。
- `python3 -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha eda64feb9945e1f9f2eaa688b1152f87b8182bf5`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha eda64feb9945e1f9f2eaa688b1152f87b8182bf5 --all-files`：通过。
- `git diff --check`：通过。
- `make regression`：通过；两轮 migration replay、16 类 SQL negative constraints、8 architecture、14 regression、8 local-runtime、16 control-plane、70 contracts、35 ingestion tests 全部通过。

远端 push 和 remote readback 以最终执行回报为准。

## 7. 工程治理检查

- `repository_hygiene_check（仓库卫生检查）`：新增代码、测试、fixture 和报告仅包含 synthetic/value-free 标识符、hash、`.invalid` 合成 URL 与相对路径；不包含 secret、token、cookie、私人联系方式、真实业务资料或本地绝对路径。
- `configuration_validation（配置验证）`：未新增配置、环境变量、生产连接、真实账号、crawler SDK、browser 或外部 provider。
- `data_safety_check（数据安全检查）`：未读取 `research_channels.json`、真实供应链、客户、价格、库存、资质、身份或联系人资料；联系语义字段在 P05-01 层 fail closed，汾酒/海鲜业务线隔离通过 `ScopeRef` 和 snapshot ref 证明。
- `dependency_compatibility_check（依赖兼容检查）`：`not_applicable`；未新增或修改依赖。

## 8. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P05-01 synthetic source policy、fake zero-network crawl、snapshot hash、evidence locator、audit denial 和 export denial 合同已由专项测试验证。
- **CONFIRMED（工程边界）**：真实 crawl、真实 website policy、真实 robots/terms 判断、CRM lead/contact、DNC、外联草稿、发送、发布、报价、付款、订单和履约均未实现。
- **BLOCKED（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界、公开来源授权、真实联系人合法性、真实外部执行仍未建立或未获书面证据。
- **不成立**：本任务不代表找客、客户可联系、CRM 可投入真实业务、外联授权、平台许可、供应链确认、上线、销售或履约能力。

## 9. P05-02 handoff

P05-02 可复用：

- `SourcePolicy`：作为 reviewed synthetic public source 的 policy/evidence 输入。
- `PublicSnapshot.safe_summary()`：作为 source hash、snapshot ref、retrieved_at 和 business line scope 输入。
- `PublicFieldCandidate.safe_summary()`：作为 lead candidate 的 value hash + evidence locator 输入。
- `FakeCrawlPort.external_fetch_count`：继续作为 zero-network probe。

P05-02 不应复用或假设：

- 不应把 snapshot/evidence 自动升级为 approved lead、organization、contact 或 opportunity。
- 不应创建 contact，除非后续 synthetic review/consent/DNC 合同明确允许。
- 不应引入 Twenty/CRM service、真实 provider ID、真实联系人或外发动作。
