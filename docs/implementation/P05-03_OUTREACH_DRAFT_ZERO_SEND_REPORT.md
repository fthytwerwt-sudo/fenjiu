# P05-03｜外联草稿、人工批准与 zero-send proof 报告

> **状态：task_branch_local_validated；commit / push / remote readback 以执行回报为准。**
>
> **执行日期：** 2026-08-09
>
> **精确工程基线：** `origin/main` `fb3fb62a63bb9ded231a0f933eafc9f41841a2f1`
>
> **任务分支：** `codex/p05-03-draft-zero-send`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic 的 CRM outreach draft（外联草稿）、fact lock（事实锁）、manual handoff（人工转交）、内部 approval（审批）与 zero-send proof（零发送证明）合同。不创建真实 recipient（收件人）、SendPort（发送端口）、provider endpoint（服务端点）、邮箱/WhatsApp/social adapter、真实联系人、价格、库存或外部执行能力。

## 1. 结论

- 新增 `modules/crm/outreach.py`，提供 `OutreachDraftService`、`OutreachDraftCommand`、`OutreachFactRef`、`OutreachFactLock`、`OutreachManualHandoff`、`OutreachZeroSendProof` 与 draft state（草稿状态）合同。
- 新增 `core/application/outreach_draft.py`，把 P05-03 draft approval（草稿审批）适配到 P04 `ActionApprovalService`，避免 `modules.crm` 反向导入 `core.security`。
- `prepare_draft()` 只接受 reviewed synthetic CRM organization（已审查合成 CRM organization）和 fresh approved synthetic fact refs（新鲜已批准合成事实引用）；草稿绑定 `fact_locks`、`policy_version`、`template_version` 和 safe evidence refs。
- DNC、缺少 consent evidence、cross-scope fact、expired/conflict fact、高风险输入统一 fail closed，返回 manual handoff，不生成 draft interaction。
- 草稿默认 editable by human（人工可编辑），且商业条款与库存只输出 confirmation-required placeholder（需要确认占位）；没有 approved fact 时不猜金额、库存或交期。
- 新增 `approve_outreach_draft` internal policy action（内部策略动作），只允许 support agent 对 fixture synthetic draft 走 P04 approval flow；批准结果为 `approved_internal`，不等于发送。
- `invalidate_on_fact_change()` 在 policy version 改变或 fact version 被 invalidated 时把草稿置为 `invalidated`；不会发送或尝试外部执行。
- zero-send proof 固定：`external_send_attempts=0`、`external_execution_allowed=false`、`send_port_present=false`、`provider_endpoint_present=false`、`external_recipient_present=false`。
- 修复 `tests/migrations/test_scope_migrations.sh` mismatch message（不匹配提示）的逐行输出，避免 P00 scanner 将带反斜杠换行的提示文本误判为 local absolute path；migration 逻辑未改变。

## 2. Test-first evidence

- **RED**：新增 `tests/contracts/test_outreach_draft_zero_send.py` 后，首次运行 `python3 -m unittest tests.contracts.test_outreach_draft_zero_send` 失败于 `ImportError: cannot import name 'OutreachDraftCommand' from 'modules.crm'`。
- **GREEN**：实现最小 outreach draft contract、`approve_outreach_draft` policy action 与 module exports 后，P05-03 专项 4 项通过。

## 3. 行为合同

| 场景 | 稳定结果 |
|---|---|
| reviewed synthetic CRM entity + fresh approved synthetic facts + consent evidence | 生成 internal editable draft，绑定 fact/policy/template lock |
| 无 approved commercial/inventory fact | 只生成 `commercial_terms_confirmation_required` / `inventory_confirmation_required` |
| DNC 命中 | `manual_handoff.reason_code=dnc_blocked` |
| consent 缺失 | `manual_handoff.reason_code=consent_required` |
| fact expired / conflict / revoked / superseded | manual handoff；不生成草稿 |
| cross-scope fact | `manual_handoff.reason_code=cross_scope_forbidden` |
| high risk | `manual_handoff.reason_code=manual_review_required` |
| draft approval | `approved_internal`；`external_send_attempts` 仍为 0 |
| policy/fact change | draft `invalidated` |
| SendPort/provider/recipient | 合同中不存在可调用公共路径 |

## 4. 已验证

- `python3 -m unittest tests.contracts.test_outreach_draft_zero_send`：4 项通过。
- `python3 -m unittest tests.contracts.test_leads_crm_domain tests.contracts.test_source_policy_and_crawl_port`：15 项通过。
- `python3 -m unittest tests.contracts.test_action_policy_rbac_approvals tests.contracts.test_audit_metrics_retry_dead_letter`：16 项通过。
- `python3 -m unittest tests.ingestion.test_approval_publish_and_refresh`：9 项通过。
- `python3 -m unittest tests.contracts.test_customer_service_fact_retrieval_risk_policy_and_drafts`：5 项通过。
- `python3 -m unittest discover -s tests/architecture`：8 项通过。
- `python3 -m unittest discover -s tests/contracts`：100 项通过。
- `python3 -m unittest discover -s tests/ingestion`：35 项通过。
- `python3 -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 161964db23b2c9500f8590435b1671bdbfae4b26`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 161964db23b2c9500f8590435b1671bdbfae4b26 --all-files`：通过。
- `git diff --check`：通过。
- `make regression`：通过；两轮 migration replay、SQL negative constraints、8 architecture、14 regression、8 local-runtime、16 control-plane、100 contracts、35 ingestion tests 全部通过。

## 5. 工程治理检查

- `repository_hygiene_check（仓库卫生检查）`：P00 default 与 `--all-files` 均通过；新增代码、测试和报告仅含 synthetic/value-free refs、scope、hash、policy/action identifiers。
- `configuration_validation（配置验证）`：未新增环境变量、生产连接、CRM provider、发送端点或真实账号。
- `data_safety_check（数据安全检查）`：未读取 `.env`、真实联系人、供应链资料、价格、库存、资质或海鲜业务事实。
- `dependency_compatibility_check（依赖兼容检查）`：`not_applicable`；未新增或修改依赖。

## 6. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P05-03 local synthetic draft-only contract 已由专项测试验证。
- **CONFIRMED（工程边界）**：草稿、审批、人工转交和 zero-send proof 均为内部合同；无外部发送、真实联系人或 provider。
- **BLOCKED（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界、真实联系人合法性、真实外联授权、真实 RBAC/auth/RLS 和任何外部执行仍未建立或未获当前书面证据。
- **不成立**：本任务不代表 Phase 5 完成、CRM 可用于真实业务、外联授权、上线、销售、报价、收款、订单、配送或履约能力。
